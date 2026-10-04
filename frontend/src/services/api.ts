import type {
  AddHouseholdMemberRequest,
  CreateHouseholdRequest,
  HealthResponse,
  Household,
  HouseholdMember,
  InventoryInput,
  InventoryItem,
  MemberFoodProfile,
} from '../types/api'
import {
  messageForHttpStatus,
  NETWORK_ERROR_MESSAGE,
} from './apiErrors'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').replace(
  /\/$/,
  '',
)

export class ApiError extends Error {
  readonly status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...init?.headers,
      },
    })
  } catch {
    throw new ApiError(NETWORK_ERROR_MESSAGE)
  }

  if (!response.ok) {
    throw new ApiError(messageForHttpStatus(response.status), response.status)
  }

  return response
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await request(path, init)
  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError('The server returned an unexpected response.')
  }
}

async function requestNoContent(path: string, init?: RequestInit): Promise<void> {
  await request(path, init)
}

function isHousehold(value: unknown): value is Household {
  if (typeof value !== 'object' || value === null) return false
  const household = value as Record<string, unknown>
  return (
    typeof household.householdId === 'string' &&
    typeof household.name === 'string' &&
    Array.isArray(household.members)
  )
}

function isHouseholdMember(value: unknown): value is HouseholdMember {
  if (typeof value !== 'object' || value === null) return false
  const member = value as Record<string, unknown>
  return typeof member.personId === 'string' && typeof member.name === 'string'
}

function isInventoryItem(value: unknown): value is InventoryItem {
  if (typeof value !== 'object' || value === null) return false
  const item = value as Record<string, unknown>
  return (
    typeof item.inventoryId === 'string' &&
    typeof item.householdId === 'string' &&
    typeof item.ingredient === 'string' &&
    typeof item.category === 'string' &&
    typeof item.quantity === 'number' &&
    item.quantity >= 0 &&
    typeof item.unit === 'string' &&
    (typeof item.purchaseDate === 'string' || item.purchaseDate === null) &&
    (typeof item.expiryDate === 'string' || item.expiryDate === null) &&
    (typeof item.storage === 'string' || item.storage === null) &&
    (typeof item.notes === 'string' || item.notes === null) &&
    ['FRESH', 'USE_SOON', 'EXPIRING', 'EXPIRED'].includes(String(item.status)) &&
    Array.isArray(item.consumptionHistory) &&
    item.consumptionHistory.every(
      (record) =>
        typeof record === 'object' &&
        record !== null &&
        'quantity' in record &&
        typeof record.quantity === 'number' &&
        'consumedAt' in record &&
        typeof record.consumedAt === 'string',
    )
  )
}

async function expectHousehold(path: string, init?: RequestInit): Promise<Household> {
  const value: unknown = await requestJson(path, init)
  if (!isHousehold(value)) {
    throw new ApiError('The server returned an unexpected household response.')
  }
  return value
}

async function expectInventoryItem(
  path: string,
  init?: RequestInit,
): Promise<InventoryItem> {
  const value: unknown = await requestJson(path, init)
  if (!isInventoryItem(value)) {
    throw new ApiError('The server returned an unexpected inventory item.')
  }
  return value
}

export async function getHealth(): Promise<HealthResponse> {
  const value: unknown = await requestJson('/health')
  if (
    typeof value !== 'object' ||
    value === null ||
    !('status' in value) ||
    typeof value.status !== 'string'
  ) {
    throw new ApiError('The server returned an unexpected health response.')
  }
  return { status: value.status }
}

export function createHousehold(
  request: CreateHouseholdRequest,
): Promise<Household> {
  return expectHousehold('/households', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export function getHousehold(householdId: string): Promise<Household> {
  return expectHousehold(`/households/${encodeURIComponent(householdId)}`)
}

export async function addHouseholdMember(
  householdId: string,
  request: AddHouseholdMemberRequest,
): Promise<HouseholdMember> {
  const value: unknown = await requestJson(
    `/households/${encodeURIComponent(householdId)}/members`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    },
  )
  if (!isHouseholdMember(value)) {
    throw new ApiError('The server returned an unexpected member response.')
  }
  return value
}

export async function updateMemberFoodProfile(
  householdId: string,
  personId: string,
  profile: MemberFoodProfile,
): Promise<HouseholdMember> {
  const value: unknown = await requestJson(
    `/households/${encodeURIComponent(householdId)}/members/${encodeURIComponent(personId)}/food-profile`,
    {
      method: 'PUT',
      body: JSON.stringify(profile),
    },
  )
  if (!isHouseholdMember(value)) {
    throw new ApiError('The server returned an unexpected member response.')
  }
  return value
}

export async function getInventory(
  householdId: string,
): Promise<InventoryItem[]> {
  const value: unknown = await requestJson(
    `/households/${encodeURIComponent(householdId)}/inventory`,
  )
  if (!Array.isArray(value) || !value.every(isInventoryItem)) {
    throw new ApiError('The server returned an unexpected inventory response.')
  }
  return value
}

export async function createInventoryItem(
  householdId: string,
  item: InventoryInput,
): Promise<InventoryItem> {
  return expectInventoryItem(
    `/households/${encodeURIComponent(householdId)}/inventory`,
    {
      method: 'POST',
      body: JSON.stringify(item),
    },
  )
}

export async function updateInventoryItem(
  householdId: string,
  inventoryId: string,
  item: InventoryInput,
): Promise<InventoryItem> {
  return expectInventoryItem(
    `/households/${encodeURIComponent(householdId)}/inventory/${encodeURIComponent(inventoryId)}`,
    {
      method: 'PUT',
      body: JSON.stringify(item),
    },
  )
}

export async function deleteInventoryItem(
  householdId: string,
  inventoryId: string,
): Promise<void> {
  await requestNoContent(
    `/households/${encodeURIComponent(householdId)}/inventory/${encodeURIComponent(inventoryId)}`,
    { method: 'DELETE' },
  )
}

export async function consumeInventoryItem(
  householdId: string,
  inventoryId: string,
  quantity: number,
): Promise<InventoryItem> {
  return expectInventoryItem(
    `/households/${encodeURIComponent(householdId)}/inventory/${encodeURIComponent(inventoryId)}/consumption`,
    {
      method: 'POST',
      body: JSON.stringify({ quantity }),
    },
  )
}
