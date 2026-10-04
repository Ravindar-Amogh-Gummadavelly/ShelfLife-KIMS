import type {
  AddHouseholdMemberRequest,
  CreateHouseholdRequest,
  HealthResponse,
  Household,
  HouseholdMember,
  MemberFoodProfile,
} from '../types/api'

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

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
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
    throw new ApiError(
      'ShelfLife could not reach the server. Check that the backend is running and try again.',
    )
  }

  if (!response.ok) {
    const messages: Record<number, string> = {
      404: 'That household or member could not be found. Please refresh and try again.',
      422: 'Please review the form. Some information is missing or invalid.',
      503: 'Household storage is temporarily unavailable. Please try again shortly.',
    }
    throw new ApiError(
      messages[response.status] ??
        'Something went wrong while saving your changes. Please try again.',
      response.status,
    )
  }

  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError('The server returned an unexpected response.')
  }
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

async function expectHousehold(path: string, init?: RequestInit): Promise<Household> {
  const value: unknown = await requestJson(path, init)
  if (!isHousehold(value)) {
    throw new ApiError('The server returned an unexpected household response.')
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
