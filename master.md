# ShelfLife — Master Project Guide

> **Project codename:** ShelfLife
> **Tagline:** The Kitchen That Remembers
> **Project type:** Digital-only, local-first/open-source AI kitchen companion
> **Primary goal:** Build a meaningful AI household food-management system that understands people, inventory, food-waste risk, and household routines — not just a generic recipe chatbot.
>
> **This file is the single source of truth for the project.**
>
> Any AI coding agent, contributor, or developer working on ShelfLife should read this file before making architectural or product decisions.

---

# 1. PROJECT VISION

## 1.1 What is ShelfLife?

ShelfLife is an AI-powered household kitchen companion that remembers:

* who lives in the household
* what each person can and cannot eat
* food preferences
* dislikes
* texture preferences
* spice tolerance
* cultural/cuisine preferences
* what ingredients are available
* what ingredients are likely to expire
* what the household tends to waste
* which meals worked well in the past
* how meals should be adapted for different people

ShelfLife uses this information to answer a much more useful question than:

> "What recipe can an AI generate?"

Instead, ShelfLife answers:

> **"What should this household cook right now, given who is eating, what we have, what needs to be used, and what each person needs?"**

---

# 2. CORE PROBLEM

Most recipe applications operate around recipes.

ShelfLife operates around the **household**.

A normal recipe application might know:

```text
Recipe:
Spinach Dal

Ingredients:
- spinach
- lentils
- tomato
- onion
- spices
```

ShelfLife knows:

```text
Household:
- 4 people
- 1 vegetarian
- 1 low-spice preference
- 1 person dislikes soft textures
- 1 person has a food allergy
- spinach expires soon
- tomatoes are available
- household usually cooks within 30 minutes
- previous spinach dishes were rated positively
```

Therefore ShelfLife can determine:

> "Spinach dal is appropriate, but modify the texture and spice level, use the spinach before it expires, and avoid the allergen."

---

# 3. THE CORE PRODUCT PRINCIPLE

## Build an AI that knows a kitchen, not an AI that knows recipes.

Every major feature should reinforce this principle.

Do not turn ShelfLife into:

* a generic chatbot
* a generic recipe generator
* a generic grocery list
* a generic nutrition assistant
* a generic voice assistant
* a generic AI wrapper

AI is useful only when it is connected to household context.

---

# 4. TARGET USER

The primary user is a household that has some combination of:

* multiple people with different food preferences
* allergies or dietary restrictions
* children
* elderly family members
* roommates
* partners
* cultural/cuisine preferences
* limited cooking time
* food waste problems
* frequently changing inventory

Example household:

```text
Family of 4

Person 1:
- vegetarian
- medium spice
- likes Indian food

Person 2:
- eats everything
- dislikes mushrooms

Person 3:
- child
- low spice
- dislikes soft textures

Person 4:
- elderly parent
- low spice
- prefers softer food
```

The system must find practical meals that work for the household.

---

# 5. PRIMARY USER JOURNEY

The ideal ShelfLife journey is:

```text
Create Household
       ↓
Add People
       ↓
Define Constraints & Preferences
       ↓
Add Inventory
       ↓
ShelfLife Understands Household
       ↓
Ask "What should we cook?"
       ↓
Retrieve Household Memory
       ↓
Check Inventory
       ↓
Check Hard Constraints
       ↓
Check Food-Waste Risk
       ↓
Generate Candidate Meals
       ↓
Adapt Meal For Household
       ↓
Validate Result
       ↓
Explain Why Meal Was Selected
       ↓
User Cooks
       ↓
User Gives Feedback
       ↓
ShelfLife Learns
       ↓
Future Recommendations Improve
```

---

# 6. CORE PRODUCT FEATURES

The final product should contain these major capabilities.

## 6.1 Household Profile

Store:

* household name
* household members
* age category where relevant
* dietary restrictions
* allergies
* preferences
* dislikes
* texture preferences
* spice tolerance
* cuisine preferences
* cooking preferences
* available equipment

---

## 6.2 Inventory

Each inventory item should support:

* ingredient name
* category
* quantity
* unit
* purchase date
* expiry date
* storage location
* freshness state
* notes
* optional image
* consumption history

Inventory states:

```text
FRESH
USE_SOON
EXPIRING
EXPIRED
```

---

## 6.3 Household Constraint System

Constraints are divided into two categories.

### Hard constraints

These must never be violated.

Examples:

* allergy
* medically required exclusion
* religious dietary restriction
* explicitly prohibited ingredient
* household dietary rule

### Soft constraints

These should influence ranking but may be overridden.

Examples:

* dislikes
* spice preference
* cuisine preference
* texture preference
* cooking time
* preferred equipment

Example:

```text
Hard constraint:
Peanuts → NEVER use

Soft constraint:
Spicy food → Prefer low spice
```

The AI must never be trusted as the sole enforcement layer for hard constraints.

A deterministic validation layer must check the final recommendation.

---

# 7. "ONE MEAL, MULTIPLE PLATES"

One of ShelfLife's key product ideas is that a household should not need three completely different meals.

Instead:

```text
                    COMMON BASE
                        │
             ┌──────────┼──────────┐
             ↓          ↓          ↓
          Person A   Person B   Person C
          Low spice  Normal     Firmer texture
```

Example:

```text
Base:
Vegetable rice

Person A:
Low spice

Person B:
Normal spice

Person C:
Extra-crispy vegetables
```

The system should reuse as much of the common meal as possible.

This makes recommendations more realistic for actual households.

---

# 8. "WHY THIS MEAL?"

Every major recommendation should be explainable.

Example:

> ### Spinach Dal + Rice
>
> **Why ShelfLife chose this**
>
> * Spinach expires in 2 days
> * Uses ingredients already available
> * Works for all household dietary constraints
> * Can be prepared in approximately 25 minutes
> * Requires one main cooking vessel
> * Matches your household's preferred cuisine
> * Similar meals were previously rated positively

The explanation should be generated from actual system data.

Do not invent reasons.

---

# 9. AI RESPONSIBILITY

AI should handle:

* natural language understanding
* meal generation
* adaptation
* explanation
* substitution suggestions
* conversational interaction
* summarization
* contextual reasoning

Deterministic application logic should handle:

* hard allergy filtering
* inventory calculations
* expiry calculations
* quantity calculations
* permissions
* validation
* database integrity
* structured data
* safety checks
* workflow state

The architecture should follow:

```text
AI proposes
      ↓
Application validates
      ↓
User receives result
```

Not:

```text
AI decides everything
      ↓
Trust AI blindly
```

---

# 10. SPONSOR STRATEGY

Sponsor technologies must solve real ShelfLife problems.

Do not add technology solely to claim a sponsor category.

Primary integrations:

1. Gemma
2. MongoDB Atlas
3. Mastra
4. TabPFN
5. Tinker
6. SerpApi
7. ElevenLabs
8. Temporal
9. Sentry
10. Render
11. GitHub Copilot

Optional technologies should not be added unless they improve the product.

---

# 11. HIGH-LEVEL ARCHITECTURE

```text
                         ┌─────────────────────┐
                         │      SHELFLIFE      │
                         │    React / PWA      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    API / Agent      │
                         │      Mastra         │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────┐       ┌──────────────┐      ┌──────────────┐
       │    Gemma    │       │   MongoDB     │      │    Tools     │
       │ AI reasoning│       │    Atlas      │      │              │
       └─────────────┘       │ Household     │      │ Inventory    │
                             │ Memory        │      │ Constraints  │
                             │ Inventory     │      │ Recipes      │
                             │ History       │      │ Research     │
                             └──────────────┘      └──────┬───────┘
                                                         │
                     ┌───────────────────────────────────┼─────────────┐
                     │                                   │             │
                     ▼                                   ▼             ▼
               ┌──────────┐                       ┌──────────┐  ┌───────────┐
               │ TabPFN   │                       │  Tinker  │  │  SerpApi  │
               │ Waste    │                       │ Fine-tune│  │ Web       │
               │Prediction│                       │Adaptation│  │ Research  │
               └──────────┘                       └──────────┘  └───────────┘

                             │
                             ▼
                      ┌──────────────┐
                      │   Temporal   │
                      │  Workflows   │
                      └──────┬───────┘
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
             ┌────────┐ ┌──────────┐ ┌─────────┐
             │ Vision │ │ElevenLabs│ │ Sentry  │
             │ Fridge │ │  Voice   │ │Tracing  │
             └────────┘ └──────────┘ └─────────┘

                      ┌──────────────┐
                      │    Render    │
                      │  Deployment  │
                      └──────────────┘
```

---

# 12. TECHNOLOGY PRINCIPLES

The exact implementation may evolve, but the system should remain modular.

Recommended stack:

## Frontend

* React
* Vite
* TypeScript
* Tailwind CSS
* PWA capabilities where useful

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy only if relational persistence is needed for supporting services

## Primary data platform

* MongoDB Atlas

## Agent layer

* Mastra

## AI

* Gemma / open-weight model

## Predictive ML

* TabPFN

## Fine-tuning

* Tinker

## Voice

* ElevenLabs

## Search

* SerpApi

## Durable workflows

* Temporal

## Observability

* Sentry

## Hosting

* Render

## Development

* GitHub
* GitHub Actions
* GitHub Copilot

---

# 13. DATA MODEL

MongoDB should store the primary application data.

Suggested collections:

```text
households
people
dietary_constraints
preferences
inventory_items
recipes
meal_recommendations
meal_history
feedback
memories
waste_events
conversations
workflow_events
```

---

# 14. HOUSEHOLD DOCUMENT

Conceptual structure:

```json
{
  "householdId": "...",
  "name": "My Household",
  "members": [
    {
      "personId": "...",
      "name": "...",
      "constraints": [],
      "preferences": [],
      "texture": "...",
      "spiceLevel": "..."
    }
  ],
  "cookingPreferences": {
    "maxTypicalTimeMinutes": 30,
    "preferredCuisines": [],
    "availableEquipment": []
  }
}
```

Do not expose sensitive information unnecessarily.

---

# 15. INVENTORY DOCUMENT

Conceptual structure:

```json
{
  "inventoryId": "...",
  "householdId": "...",
  "ingredient": "spinach",
  "quantity": 250,
  "unit": "g",
  "purchaseDate": "...",
  "expiryDate": "...",
  "storage": "refrigerator",
  "status": "USE_SOON"
}
```

---

# 16. MEMORY MODEL

ShelfLife should eventually remember useful household-level facts.

Examples:

```text
"The family prefers meals under 30 minutes."

"Ananya dislikes mushrooms."

"Dad prefers low-spice food."

"The household liked spinach dal last week."

"Paneer meals have historically been well received."

"Meals requiring more than two cooking vessels are rarely prepared."
```

Memory should be categorized.

Possible categories:

```text
PREFERENCE
DISLIKE
SUCCESS
FAILURE
ROUTINE
CONSTRAINT
COOKING_PATTERN
MEAL_FEEDBACK
```

---

# 17. AGENT TOOL DESIGN

Mastra should expose explicit tools.

Potential tools:

```text
get_household_context
get_inventory
get_expiring_inventory
get_person_constraints
check_meal_constraints
search_recipes
generate_meal_candidates
adapt_meal
record_meal_feedback
record_inventory_usage
predict_waste
research_ingredient
create_meal_plan
```

The agent should not directly manipulate arbitrary database records.

Tools should enforce boundaries.

---

# 18. AGENT DECISION PIPELINE

When the user asks:

> "What should we cook tonight?"

The system should conceptually execute:

```text
1. Understand request
        ↓
2. Load household context
        ↓
3. Load current inventory
        ↓
4. Identify expiring ingredients
        ↓
5. Retrieve household preferences
        ↓
6. Apply hard constraints
        ↓
7. Calculate useful inventory candidates
        ↓
8. Consider waste prediction
        ↓
9. Generate candidate meals
        ↓
10. Score candidates
        ↓
11. Adapt for household members
        ↓
12. Validate final result
        ↓
13. Explain recommendation
        ↓
14. Return structured response
```

---

# 19. MEAL SCORING

The recommendation system should eventually score candidate meals based on multiple factors.

Conceptual score:

```text
Meal Score =
    constraint compatibility
  + expiry urgency
  + waste reduction
  + inventory availability
  + household preference
  + historical success
  + cooking time
  + equipment availability
  + meal variety
```

Hard constraints must act as filters before scoring.

A meal containing an allergen should not simply receive a lower score.

It should be rejected.

---

# 20. PHASE ROADMAP

ShelfLife is divided into **8 major phases**.

Do not create unnecessary micro-phases.

Each phase must result in a usable improvement.

---

# PHASE 1 — FOUNDATION + DEPLOYMENT

## Objective

Create the application foundation and establish the development/deployment workflow.

## Build

* GitHub repository
* React/Vite frontend
* FastAPI backend
* MongoDB Atlas connection
* environment configuration
* health endpoint
* basic UI shell
* basic API client
* CI/CD
* initial Render deployment
* testing foundation
* README

## Sponsor usage

### GitHub Copilot

Use for:

* implementation assistance
* tests
* refactoring
* GitHub Actions
* PR review
* documentation

### Render

Use as the real application deployment platform.

## Completion criteria

The following must work:

```text
Browser
   ↓
React
   ↓
FastAPI
   ↓
MongoDB Atlas
```

The deployed application should be accessible.

---

# PHASE 2 — HOUSEHOLD MEMORY + INVENTORY

## Objective

Build the actual data foundation of ShelfLife.

## Build

Household:

* create household
* add members
* edit members
* constraints
* preferences
* texture
* spice
* cuisine

Inventory:

* add ingredient
* edit ingredient
* delete ingredient
* quantity
* unit
* purchase date
* expiry date
* storage
* status

## UI

Minimum screens:

```text
Dashboard
Household
People
Inventory
```

## Completion criteria

A real household can be entered and stored.

A real inventory can be entered and stored.

No AI is required yet.

---

# PHASE 3 — AI KITCHEN BRAIN

## Objective

Introduce ShelfLife's core intelligence.

## Sponsor

* Gemma
* Mastra
* MongoDB Atlas

## Build

Mastra agent with tools for:

* household context
* inventory
* constraints
* recipes
* meal generation
* meal explanation

## User interaction

Example:

> "What should we cook tonight?"

The system should return:

```text
Meal
Ingredients
Preparation
Estimated time
Household adaptations
Why this meal
```

## Constraint engine

Hard constraints must be deterministic.

Example:

```text
User allergy:
Peanut

Generated meal:
Peanut curry

Constraint validator:
REJECT
```

The system should regenerate or choose another meal.

## Completion criteria

The AI recommendation is based on actual household and inventory data.

---

# PHASE 4 — SMART WASTE PREVENTION

## Objective

Use household history to predict food waste and turn predictions into useful recommendations.

## Sponsor

* TabPFN

## Data collection

Record:

```text
ingredient
purchase date
expiry date
quantity
consumed quantity
wasted quantity
household size
usage frequency
```

## TabPFN task

Predict:

> Probability that an ingredient will become waste.

Example:

```text
Spinach     87%
Bananas     71%
Tomatoes    54%
Rice        12%
```

## Product behavior

The prediction must influence the recommendation engine.

Example:

> "Spinach has a high waste risk. Here are two meals that use it."

## Completion criteria

ShelfLife can show waste-risk predictions and use them in meal ranking.

---

# PHASE 5 — ADAPTIVE PERSONALIZATION + TINKER

## Objective

Make ShelfLife adapt meals intelligently to changing household needs.

## Examples

User:

> "Make it less spicy."

User:

> "I only have 15 minutes."

User:

> "We're out of onions."

User:

> "Make it suitable for someone who dislikes soft textures."

User:

> "We have one extra guest."

The system should adapt the meal instead of starting from zero.

---

## Tinker integration

Create a baseline:

```text
Gemma baseline
```

Create a fine-tuned model:

```text
ShelfLife household-adaptation model
```

Evaluate both.

Metrics:

```text
constraint compliance
adaptation quality
personalization quality
latency
cost
```

The final project should show measurable improvement where possible.

## Completion criteria

A clear baseline-vs-fine-tuned evaluation exists.

---

# PHASE 6 — MULTIMODAL KITCHEN

## Objective

Make ShelfLife practical in real kitchen situations.

---

## 6.1 Fridge Vision

User uploads a fridge/pantry image.

System produces:

```text
Possible ingredients:
✓ spinach
✓ tomatoes
✓ carrots
? coriander
? green chili
```

The user confirms uncertain items.

Only confirmed items should automatically enter inventory.

Do not assume computer vision is always correct.

---

## 6.2 SerpApi

Add explicit web research capability.

Potential uses:

```text
ingredient substitution
cuisine research
current cooking information
recipe research
```

The agent should clearly indicate when external web research was used.

---

## 6.3 ElevenLabs

Create:

# Kitchen Mode

Hands-free conversational experience.

Examples:

> "What's next?"

> "Add spinach to my inventory."

> "Start cooking."

> "Repeat that step."

> "I don't have tomatoes."

The voice system should interact with the same ShelfLife agent and tools.

## Completion criteria

Users can interact through:

* text
* image
* voice

---

# PHASE 7 — PROACTIVE SHELFLIFE AGENT

## Objective

Make ShelfLife proactive instead of purely reactive.

## Sponsor

* Temporal

## Workflow

```text
Scheduled workflow
       ↓
Check inventory
       ↓
Check upcoming expiry
       ↓
Run waste prediction
       ↓
Retrieve household preferences
       ↓
Generate meal options
       ↓
Validate meals
       ↓
Notify user
       ↓
Wait for response
       ↓
Resume workflow
```

Example:

> Good morning.
>
> Your spinach has a high chance of going unused this week.
>
> I found two meals that use it and work for everyone.
>
> Would you like to cook one tonight?

Temporal should provide durable workflow execution, retry behavior, and resumability.

## Completion criteria

ShelfLife can proactively generate useful recommendations without the user initiating every interaction.

---

# PHASE 8 — PRODUCTION, OBSERVABILITY + OPEN SOURCE

## Objective

Turn the prototype into a polished open-source project suitable for public demonstration.

---

## Sentry

Instrument the agent.

Track:

```text
request
↓
Mastra
↓
memory retrieval
↓
Gemma
↓
tool calls
↓
validation
↓
response
```

Monitor:

* latency
* failures
* retries
* model calls
* tool calls
* workflow errors
* constraint violations
* resource usage

---

## Render

Production deployment.

The deployed version should demonstrate the actual system rather than a fake mock.

---

## GitHub

Create:

```text
README.md
CONTRIBUTING.md
CODE_OF_CONDUCT.md
LICENSE
SECURITY.md
.env.example
```

GitHub configuration:

```text
.github/
├── workflows/
├── ISSUE_TEMPLATE/
└── pull_request_template.md
```

---

# 21. FINAL REPOSITORY STRUCTURE

The structure can evolve, but should remain understandable.

Recommended:

```text
shelflife/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   └── utils/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── tools/
│   │   ├── constraints/
│   │   ├── workflows/
│   │   └── config/
│   ├── tests/
│   └── requirements.txt
│
├── ai/
│   ├── prompts/
│   ├── evaluations/
│   ├── datasets/
│   ├── tabpfn/
│   └── tinker/
│
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── evaluation/
│   └── demos/
│
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
│
├── master.md
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── LICENSE
├── .env.example
└── docker-compose.yml
```

Do not create folders that are not needed yet.

---

# 22. API DESIGN

Suggested endpoints:

```text
GET    /api/health

POST   /api/households
GET    /api/households/{id}
PUT    /api/households/{id}

POST   /api/households/{id}/people
GET    /api/households/{id}/people
PUT    /api/people/{id}
DELETE /api/people/{id}

POST   /api/households/{id}/inventory
GET    /api/households/{id}/inventory
PUT    /api/inventory/{id}
DELETE /api/inventory/{id}

POST   /api/households/{id}/ask
POST   /api/households/{id}/feedback

GET    /api/households/{id}/waste-risk
POST   /api/households/{id}/meal-plan

POST   /api/vision/analyze
POST   /api/voice/transcribe
POST   /api/research
```

The exact endpoints may change.

Do not prematurely build every endpoint.

---

# 23. STRUCTURED AI OUTPUT

Do not rely on free-form AI responses for important application behavior.

Prefer structured output.

Conceptual response:

```json
{
  "meal": {
    "name": "Spinach Dal",
    "estimatedMinutes": 25,
    "servings": 4
  },
  "ingredientsUsed": [],
  "adaptations": [],
  "whyChosen": [],
  "constraintValidation": {
    "passed": true,
    "violations": []
  }
}
```

The backend should validate the structure before sending it to the frontend.

---

# 24. AI SAFETY RULES

The AI must not:

* override known allergies
* invent inventory
* claim an ingredient exists when it does not
* claim a meal satisfies a restriction without validation
* silently change hard constraints
* invent household memories
* present uncertain vision results as certain
* pretend web research happened when it did not
* hide uncertainty

Use confidence and confirmation where appropriate.

---

# 25. VISION RULE

Computer vision produces **candidates**, not unquestionable facts.

Example:

```text
Vision:
spinach: 96%
tomato: 92%
coriander: 54%
```

The UI should allow:

```text
✓ Confirm spinach
✓ Confirm tomato
? Review coriander
```

Only confirmed items should modify inventory automatically.

---

# 26. MEMORY RULE

Do not save every conversation sentence as permanent memory.

Only persist useful, stable information.

Good memory:

> "User prefers low-spice meals."

Bad memory:

> "User asked what to cook at 7:43 PM on Tuesday."

Unless the latter is required for history, it should not become permanent memory.

---

# 27. PRIVACY PRINCIPLE

ShelfLife is designed around household information, which can be sensitive.

The architecture should follow:

```text
Minimum necessary data
        ↓
Clear user control
        ↓
Secure storage
        ↓
No unnecessary exposure
```

Where practical, support a local-first development/demo mode.

Do not collect unnecessary personal information.

---

# 28. EVALUATION

ShelfLife should be evaluated as a system, not merely by whether the UI works.

## Product metrics

Measure:

* recommendation usefulness
* constraint compliance
* waste reduction
* meal acceptance
* adaptation quality
* response latency
* tool reliability

---

# 29. AI EVALUATION

Create a fixed evaluation dataset.

Example test:

```text
Household:
Vegetarian
Low spice
Person dislikes mushrooms

Inventory:
spinach
rice
lentils
mushrooms

Request:
"What should we cook?"
```

Expected behavior:

* mushroom meals should be avoided if disliked strongly
* vegetarian constraint must be respected
* low spice should influence recommendation
* available ingredients should be prioritized

---

# 30. CONSTRAINT COMPLIANCE METRIC

Define:

```text
Constraint Compliance =
valid recommendations / total evaluated recommendations
```

Hard constraint violations should be treated as severe failures.

Target:

```text
Hard constraint compliance → as close to 100% as possible
```

---

# 31. TABPFN EVALUATION

Compare predicted waste risk against actual outcomes.

Possible metrics:

* accuracy
* precision
* recall
* F1
* calibration
* ranking quality

The most important product question:

> Does the prediction help ShelfLife choose better "use soon" recommendations?

---

# 32. TINKER EVALUATION

Compare:

```text
Baseline Gemma
VS
Fine-tuned ShelfLife model
```

Measure:

```text
Constraint compliance
Personalization
Adaptation quality
Latency
Cost
```

Document both improvements and regressions.

Never claim an improvement without measurement.

---

# 33. AGENT OBSERVABILITY

Every important agent run should be traceable.

Example:

```text
Request ID
   │
   ├── household retrieval
   │
   ├── inventory retrieval
   │
   ├── memory retrieval
   │
   ├── waste prediction
   │
   ├── Gemma generation
   │
   ├── constraint validation
   │
   └── final response
```

Sentry should make debugging possible.

---

# 34. TEMPORAL WORKFLOW PRINCIPLE

Temporal should be used where durability matters.

Good use:

```text
daily expiry monitoring
```

Bad use:

```text
simple synchronous button click
```

Do not use Temporal merely for sponsor recognition.

---

# 35. SERPAPI PRINCIPLE

SerpApi should be an explicit tool.

Use it when the user asks for information that benefits from external/current research.

Do not route every normal meal recommendation through web search.

ShelfLife should remain useful without external web access.

---

# 36. ELEVENLABS PRINCIPLE

Voice should improve the kitchen experience.

The main reason for voice is:

> Hands are often busy while cooking.

Therefore Kitchen Mode should prioritize:

* short responses
* step-by-step instructions
* repeat
* pause
* next step
* ingredient updates
* hands-free queries

---

# 37. MASTRA PRINCIPLE

Mastra is the orchestration layer.

The agent should have controlled access to tools.

Conceptually:

```text
User
 ↓
Mastra
 ├── memory
 ├── inventory
 ├── constraints
 ├── recipes
 ├── waste prediction
 ├── research
 └── feedback
 ↓
Validated answer
```

---

# 38. MONGODB PRINCIPLE

MongoDB Atlas is the main application data and memory layer.

Use it for:

* household information
* inventory
* history
* preferences
* memory
* feedback
* meal records

Avoid adding another database unless there is a concrete technical reason.

---

# 39. RENDER PRINCIPLE

Render should host a genuine working version of ShelfLife.

The demo deployment should not be a separate fake application.

The public demo should use the same architecture as the project wherever practical.

---

# 40. OPTIONAL TECHNOLOGIES

The following should NOT be forced into the product.

## Arduino

Removed.

ShelfLife is a **digital-only project**.

Do not add:

* sensors
* physical kitchen hardware
* Arduino devices
* physical agents

---

## DigitalOcean

Optional.

Only use if a real requirement appears, such as:

* GPU inference
* model hosting
* specialized compute

Do not deploy the same workload twice simply to claim two hosting sponsors.

---

## Tiger Data

Optional.

MongoDB is already the primary data layer.

Use Tiger Data only if semantic/vector search creates a genuine technical advantage that justifies the additional infrastructure.

---

## Backboard

Optional.

Potential use:

* contributor memory
* developer assistant workflow
* open-source project context

Do not force it into the household user experience.

---

## Entire

Use primarily for:

* development history
* engineering decisions
* project write-up
* understanding why implementation choices were made

Do not make it a required end-user dependency.

---

# 41. DEVELOPMENT RULES

Any AI coding agent working on ShelfLife must follow these rules.

## Rule 1 — Read master.md first

Before implementing a feature, understand:

* current phase
* architecture
* existing code
* sponsor role
* data model

---

## Rule 2 — Do not skip phases

Do not implement advanced AI features before the data foundation exists.

Correct:

```text
Foundation
 ↓
Household
 ↓
Inventory
 ↓
AI
```

Incorrect:

```text
Build voice AI
 ↓
Build database later
```

---

## Rule 3 — Do not over-engineer

Prefer:

```text
simple working implementation
```

over:

```text
complex theoretical architecture
```

---

## Rule 4 — Preserve modularity

AI providers should be replaceable where practical.

Do not hard-code the entire system around one model.

---

## Rule 5 — Keep sponsor integrations replaceable

ShelfLife should remain a valid product even if a sponsor service is temporarily unavailable.

Example:

```text
ElevenLabs unavailable
       ↓
Text mode still works
```

---

## Rule 6 — Test every meaningful feature

New features should include appropriate tests.

---

## Rule 7 — Never fake integration

Do not create:

```text
"Powered by TabPFN"
```

without actually using TabPFN.

Do not claim:

```text
"Tinker fine-tuned model"
```

without actually fine-tuning/evaluating a model.

Do not claim:

```text
"Temporal workflow"
```

without actual Temporal workflow execution.

Sponsor integrations must be demonstrable.

---

# 42. DEFINITION OF DONE

A feature is not complete when the code compiles.

A feature is complete when:

```text
Implementation
+
Tests
+
Error handling
+
UI integration
+
Documentation
+
Real data
+
Validation
```

are sufficient for the feature's scope.

---

# 43. GIT WORKFLOW

Use small meaningful commits.

Examples:

```text
feat: add household profile
feat: add inventory management
feat: add constraint engine
feat: add Gemma meal agent
feat: add waste prediction
feat: add meal adaptation
feat: add fridge vision
feat: add kitchen voice mode
feat: add proactive meal workflow
feat: add Sentry tracing
```

Avoid giant commits such as:

```text
finished entire project
```

---

# 44. CONTRIBUTOR STRATEGY

ShelfLife should be easy for open-source contributors to understand.

Potential issues:

```text
good first issue:
Add inventory filtering

good first issue:
Add recipe card component

good first issue:
Add meal feedback UI

good first issue:
Add new cuisine dataset

advanced:
Implement new AI provider

advanced:
Improve constraint evaluator

advanced:
Add new memory strategy

advanced:
Improve waste prediction

advanced:
Add new voice provider
```

The architecture should allow contributors to work on isolated areas.

---

# 45. DEMO SCENARIO

The final Hacktoberfest demonstration should tell one coherent story.

## Step 1 — Household

Create:

```text
4-person household
```

Profiles include different preferences.

---

## Step 2 — Inventory

Add:

```text
spinach
tomatoes
rice
lentils
carrots
yogurt
```

Make spinach close to expiry.

---

## Step 3 — Ask ShelfLife

User:

> "What should we cook tonight?"

ShelfLife analyzes:

```text
Household
+
Inventory
+
Constraints
+
Preferences
+
Expiry
+
Waste prediction
```

---

## Step 4 — Recommendation

ShelfLife recommends a meal.

Show:

```text
Meal
Time
Ingredients
Adaptations
Why chosen
```

---

## Step 5 — User changes requirement

User:

> "We only have 20 minutes."

ShelfLife adapts.

---

## Step 6 — User changes inventory

User:

> "We're out of tomatoes."

ShelfLife adapts again.

---

## Step 7 — Show waste prediction

Display:

```text
Spinach
87% waste risk
```

Explain how this influenced the recommendation.

---

## Step 8 — Kitchen Mode

User activates voice.

> "What's the next step?"

ShelfLife responds.

---

## Step 9 — Proactive behavior

Later:

> "ShelfLife noticed your spinach is likely to go unused and prepared two meal options."

This demonstrates the full product vision.

---

# 46. FINAL DEMO NARRATIVE

The demo should communicate this:

> "ShelfLife isn't another recipe chatbot."
>
> "It remembers the people in your home."
>
> "It knows what food you have."
>
> "It learns what your household actually eats."
>
> "It predicts what you're likely to waste."
>
> "It checks dietary constraints before recommending a meal."
>
> "It adapts one meal for different people."
>
> "And eventually, it can proactively tell you what to cook before food goes to waste."

---

# 47. HACKTOBERFEST VALUE PROPOSITION

The project should demonstrate:

## Open source

* modular architecture
* contributor-friendly repository
* documented AI components
* reproducible evaluation

## AI

* open-weight Gemma
* agent orchestration
* memory
* multimodal interaction
* fine-tuning
* predictive ML

## Real-world usefulness

ShelfLife addresses:

* food waste
* household meal planning
* personalization
* dietary constraints
* cooking time
* inventory management

## Technical depth

The project combines:

```text
LLM
+
Agent
+
Memory
+
Database
+
Predictive ML
+
Fine-tuning
+
Vision
+
Voice
+
Durable Workflows
+
Observability
```

without requiring physical hardware.

---

# 48. SUCCESS CRITERIA

ShelfLife should be considered successful if it can demonstrate:

### Product

* household can be configured
* inventory can be maintained
* meals can be recommended
* recommendations use actual household context
* hard constraints are validated
* meals can be adapted
* food-waste risk influences recommendations
* user feedback affects future recommendations

### AI

* Gemma is genuinely used
* Mastra genuinely orchestrates the agent
* TabPFN genuinely performs waste prediction
* Tinker genuinely supports an evaluated fine-tuning experiment

### Integrations

* ElevenLabs provides real voice functionality
* SerpApi provides real research functionality
* Temporal runs real durable workflows
* Sentry provides real traces/observability
* Render hosts a real deployment
* MongoDB Atlas stores real application data

### Open source

* repository is documented
* installation is reproducible
* contribution process is clear
* tests exist
* architecture is understandable

---

# 49. BUILD ORDER

Always follow this order unless there is a documented reason to change it.

```text
PHASE 1
Foundation + Deployment
        ↓
PHASE 2
Household + Inventory
        ↓
PHASE 3
AI Kitchen Brain
        ↓
PHASE 4
Waste Prediction
        ↓
PHASE 5
Adaptive Personalization
        ↓
PHASE 6
Multimodal Kitchen
        ↓
PHASE 7
Proactive Agent
        ↓
PHASE 8
Production + Observability + Open Source
```

---

# 50. AI CODING AGENT MASTER INSTRUCTION

Any AI coding agent working on ShelfLife should follow this instruction:

```text
You are working on ShelfLife — "The Kitchen That Remembers".

Before doing anything:

1. Read master.md completely.
2. Inspect the current repository.
3. Determine the current implementation phase.
4. Do not assume a feature exists just because master.md describes it.
5. Inspect the actual code before modifying it.
6. Preserve the architecture and product principles in master.md.
7. Do not introduce unnecessary technologies.
8. Do not force sponsor integrations where they do not provide real value.
9. Never fake sponsor integrations.
10. Never bypass deterministic hard-constraint validation.
11. Never invent household data, inventory, memories, or AI capabilities.
12. Keep AI providers and external services modular where practical.
13. Write tests for meaningful functionality.
14. Update documentation when architecture changes.
15. Keep changes small and reviewable.
16. Do not implement future phases prematurely unless explicitly instructed.
17. After implementation, run relevant tests and verify the application.
18. Explain what changed, why it changed, how it was tested, and what remains.

Product principle:

"ShelfLife is not an AI recipe generator.
ShelfLife is an AI that knows a kitchen."

The primary system loop is:

Household
→ Inventory
→ Memory
→ Constraints
→ Waste prediction
→ Meal planning
→ Adaptation
→ Validation
→ User feedback
→ Better future recommendations.

Always prioritize a working, understandable, testable product over unnecessary complexity.
```

---

# 51. PHASE EXECUTION PROMPT

When beginning a new phase, use:

```text
Read master.md first.

We are now implementing:

[PHASE NUMBER AND NAME]

Before writing code:

1. Inspect the existing repository.
2. Identify what from this phase already exists.
3. Identify missing functionality.
4. Check that the existing architecture still matches master.md.
5. List the files that need to be created or modified.
6. Explain the implementation plan briefly.
7. Do not implement future-phase functionality.

Then implement the phase incrementally.

Requirements:

- Follow master.md.
- Reuse existing code where appropriate.
- Do not duplicate functionality.
- Keep sponsor integrations genuine.
- Validate hard constraints deterministically.
- Add tests.
- Handle errors.
- Update documentation where necessary.
- Keep the UI usable.
- Do not introduce unnecessary dependencies.

After implementation:

1. Run tests.
2. Run lint/type checks where applicable.
3. Verify frontend/backend integration.
4. Verify database behavior.
5. Fix errors.
6. Summarize completed work.
7. List files changed.
8. List tests performed.
9. List anything still incomplete.

Do not move to the next phase automatically.
Stop after this phase is working.
```

---

# 52. CURRENT DEVELOPMENT STATUS

At the beginning of the project:

```text
Phase 1: NOT STARTED
Phase 2: NOT STARTED
Phase 3: NOT STARTED
Phase 4: NOT STARTED
Phase 5: NOT STARTED
Phase 6: NOT STARTED
Phase 7: NOT STARTED
Phase 8: NOT STARTED
```

Update this section as development progresses.

Example:

```text
Phase 1: COMPLETE
Phase 2: IN PROGRESS
Phase 3: NOT STARTED
...
```

---

# 53. PROJECT NORTH STAR

Every design decision should answer:

> **Does this make ShelfLife better at understanding and helping a real household manage food?**

If yes:

Proceed.

If no:

Question whether the feature belongs in ShelfLife.

The project should remain focused on one powerful idea:

# ShelfLife remembers your kitchen.

It knows:

**who you feed, what they like, what they cannot eat, what food you have, what is about to go bad, what your household tends to waste, and what meal makes sense right now.**

That is ShelfLife.

---

# END OF MASTER DOCUMENT
