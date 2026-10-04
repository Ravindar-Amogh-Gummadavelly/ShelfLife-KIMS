export interface HealthResponse {
  status: string
}

export type SpiceLevel = 'low' | 'medium' | 'high'

export interface HouseholdMember {
  personId: string
  name: string
  ageCategory: string | null
  allergies: string[]
  prohibitedFoods: string[]
  dietaryRestrictions: string[]
  dislikes: string[]
  preferredFoods: string[]
  spiceLevel: SpiceLevel | null
  texturePreferences: string[]
  cuisinePreferences: string[]
  constraints: string[]
  preferences: string[]
  texture: string | null
}

export interface Household {
  householdId: string
  name: string
  members: HouseholdMember[]
}

export interface CreateHouseholdRequest {
  name: string
}

export interface MemberFoodProfile {
  allergies: string[]
  prohibitedFoods: string[]
  dietaryRestrictions: string[]
  dislikes: string[]
  preferredFoods: string[]
  spiceLevel: SpiceLevel | null
  texturePreferences: string[]
  cuisinePreferences: string[]
}

export interface AddHouseholdMemberRequest extends MemberFoodProfile {
  name: string
}
