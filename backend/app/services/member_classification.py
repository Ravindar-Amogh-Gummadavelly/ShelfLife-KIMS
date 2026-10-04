from app.models.household import (
    HouseholdMember,
    HouseholdMemberClassification,
    HouseholdMemberHardConstraints,
    HouseholdMemberSoftPreferences,
)


def classify_member_profile(member: HouseholdMember) -> HouseholdMemberClassification:
    return HouseholdMemberClassification(
        hard_constraints=HouseholdMemberHardConstraints(
            allergies=member.allergies,
            prohibited_foods=member.prohibited_foods,
            dietary_restrictions=member.dietary_restrictions,
            legacy_constraints=member.constraints,
        ),
        soft_preferences=HouseholdMemberSoftPreferences(
            dislikes=member.dislikes,
            preferred_foods=member.preferred_foods,
            spice_level=member.spice_level,
            texture_preferences=member.texture_preferences,
            cuisine_preferences=member.cuisine_preferences,
            legacy_preferences=member.preferences,
            legacy_texture=member.texture,
        ),
    )
