from app.models.household import HouseholdMember
from app.services.member_classification import classify_member_profile


def test_member_profile_classifies_hard_constraints_and_soft_preferences() -> None:
    member = HouseholdMember(
        name="Alex",
        allergies=["peanuts"],
        prohibitedFoods=["pork"],
        dietaryRestrictions=["vegetarian"],
        dislikes=["mushrooms"],
        preferredFoods=["lentils"],
        spiceLevel="low",
        texturePreferences=["firm"],
        cuisinePreferences=["Indian"],
        constraints=["legacy dietary rule"],
        preferences=["legacy preference"],
        texture="soft",
    )

    classification = classify_member_profile(member)

    assert classification.hard_constraints.model_dump() == {
        "allergies": ["peanuts"],
        "prohibited_foods": ["pork"],
        "dietary_restrictions": ["vegetarian"],
        "legacy_constraints": ["legacy dietary rule"],
    }
    assert classification.soft_preferences.model_dump(mode="json") == {
        "dislikes": ["mushrooms"],
        "preferred_foods": ["lentils"],
        "spice_level": "low",
        "texture_preferences": ["firm"],
        "cuisine_preferences": ["Indian"],
        "legacy_preferences": ["legacy preference"],
        "legacy_texture": "soft",
    }
