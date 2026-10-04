import { useEffect, useState, type FormEvent, type KeyboardEvent } from 'react'
import {
  addHouseholdMember,
  ApiError,
  createHousehold,
  getHousehold,
  updateMemberFoodProfile,
} from './services/api'
import type {
  Household,
  HouseholdMember,
  MemberFoodProfile,
  SpiceLevel,
} from './types/api'
import './App.css'

const HOUSEHOLD_STORAGE_KEY = 'shelflife.householdId'

type Page = 'welcome' | 'member' | 'kitchen' | 'household' | 'inventory' | 'reconnecting'
type MemberMode = 'first' | 'add' | 'edit'
type ProfileField = keyof Omit<MemberFoodProfile, 'spiceLevel'>

const profileGroups: {
  title: string
  description: string
  fields: { key: ProfileField; label: string; placeholder: string }[]
}[] = [
  {
    title: 'Hard constraints',
    description: 'Safety-first information such as allergies and foods to avoid.',
    fields: [
      { key: 'allergies', label: 'Allergies', placeholder: 'e.g. peanuts' },
      {
        key: 'prohibitedFoods',
        label: 'Foods to avoid',
        placeholder: 'e.g. shellfish',
      },
      {
        key: 'dietaryRestrictions',
        label: 'Dietary restrictions',
        placeholder: 'e.g. vegetarian',
      },
    ],
  },
  {
    title: 'Soft preferences',
    description: 'Helpful likes and dislikes that are not safety restrictions.',
    fields: [
      { key: 'dislikes', label: 'Dislikes', placeholder: 'e.g. olives' },
      {
        key: 'preferredFoods',
        label: 'Favorite foods',
        placeholder: 'e.g. lentils',
      },
      {
        key: 'texturePreferences',
        label: 'Texture preferences',
        placeholder: 'e.g. crunchy',
      },
      {
        key: 'cuisinePreferences',
        label: 'Cuisine preferences',
        placeholder: 'e.g. Korean',
      },
    ],
  },
]

function emptyProfile(): MemberFoodProfile {
  return {
    allergies: [],
    prohibitedFoods: [],
    dietaryRestrictions: [],
    dislikes: [],
    preferredFoods: [],
    spiceLevel: null,
    texturePreferences: [],
    cuisinePreferences: [],
  }
}

function profileFromMember(member: HouseholdMember): MemberFoodProfile {
  return {
    allergies: member.allergies,
    prohibitedFoods: member.prohibitedFoods,
    dietaryRestrictions: member.dietaryRestrictions,
    dislikes: member.dislikes,
    preferredFoods: member.preferredFoods,
    spiceLevel: member.spiceLevel,
    texturePreferences: member.texturePreferences,
    cuisinePreferences: member.cuisinePreferences,
  }
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Something went wrong. Please try again.'
}

function readSavedHouseholdId(): string | null {
  try {
    return window.localStorage.getItem(HOUSEHOLD_STORAGE_KEY)
  } catch {
    return null
  }
}

function clearSavedHouseholdId() {
  try {
    window.localStorage.removeItem(HOUSEHOLD_STORAGE_KEY)
  } catch {
    return
  }
}

function App() {
  const [householdId, setHouseholdId] = useState<string | null>(readSavedHouseholdId)
  const [page, setPage] = useState<Page>(householdId ? 'reconnecting' : 'welcome')
  const [household, setHousehold] = useState<Household | null>(null)
  const [householdName, setHouseholdName] = useState('')
  const [memberMode, setMemberMode] = useState<MemberMode>('first')
  const [editingMember, setEditingMember] = useState<HouseholdMember | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const savedId = readSavedHouseholdId()
    if (!savedId) return

    let active = true
    getHousehold(savedId)
      .then((savedHousehold) => {
        if (!active) return
        setHousehold(savedHousehold)
        setPage('kitchen')
      })
      .catch((requestError: unknown) => {
        if (!active) return
        if (requestError instanceof ApiError && requestError.status === 404) {
          clearSavedHouseholdId()
          setHouseholdId(null)
          setPage('welcome')
        } else {
          setError(errorMessage(requestError))
        }
      })

    return () => {
      active = false
    }
  }, [])

  async function handleCreateHousehold(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const created = await createHousehold({ name: householdName.trim() })
      setHousehold(created)
      setHouseholdId(created.householdId)
      try {
        window.localStorage.setItem(HOUSEHOLD_STORAGE_KEY, created.householdId)
      } catch {
        setError(
          'Your kitchen is ready, but this browser could not remember it. Keep this tab open to continue.',
        )
      }
      setMemberMode('first')
      setEditingMember(null)
      setPage('member')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  function openMemberForm(mode: MemberMode, member: HouseholdMember | null = null) {
    setMemberMode(mode)
    setEditingMember(member)
    setError('')
    setPage('member')
  }

  async function handleSaveMember(
    event: FormEvent<HTMLFormElement>,
    name: string,
    profile: MemberFoodProfile,
  ) {
    event.preventDefault()
    if (!householdId || !household) {
      setError('Create or reconnect to a household before adding a member.')
      return
    }

    setError('')
    setLoading(true)
    try {
      if (memberMode === 'edit' && editingMember) {
        const updated = await updateMemberFoodProfile(
          householdId,
          editingMember.personId,
          profile,
        )
        setHousehold({
          ...household,
          members: household.members.map((member) =>
            member.personId === updated.personId ? updated : member,
          ),
        })
      } else {
        const added = await addHouseholdMember(householdId, { name, ...profile })
        setHousehold({ ...household, members: [...household.members, added] })
      }
      setEditingMember(null)
      setPage(memberMode === 'first' ? 'kitchen' : 'household')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  async function reconnect() {
    if (!householdId) {
      setPage('welcome')
      return
    }
    setError('')
    setLoading(true)
    try {
      const savedHousehold = await getHousehold(householdId)
      setHousehold(savedHousehold)
      setPage('kitchen')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }

  function navigate(nextPage: Page) {
    setError('')
    setPage(nextPage)
  }

  if (page === 'welcome') {
    return (
      <main className="welcome-page">
        <section className="welcome-card">
          <Brand />
          <div className="welcome-copy">
            <p className="eyebrow">A little more ease, every day</p>
            <h1>Your kitchen, remembered.</h1>
            <p>
              Start with your household. ShelfLife keeps the food details that
              matter to your home together in one place.
            </p>
          </div>
          <form className="household-form" onSubmit={handleCreateHousehold}>
            <label htmlFor="household-name">What should we call your household?</label>
            <div className="form-row">
              <input
                id="household-name"
                name="householdName"
                value={householdName}
                onChange={(event) => setHouseholdName(event.target.value)}
                placeholder="e.g. The Rivera home"
                maxLength={120}
                required
              />
              <button className="button button-primary" disabled={loading}>
                {loading ? 'Creating…' : 'Create a kitchen'}
              </button>
            </div>
          </form>
          <ErrorNotice message={error} />
        </section>
      </main>
    )
  }

  if (page === 'reconnecting') {
    return (
      <main className="welcome-page">
        <section className="welcome-card reconnect-card">
          <Brand />
          <h1>Finding your kitchen</h1>
          <p>We’re reconnecting to your saved household.</p>
          <ErrorNotice message={error} />
          <button
            className="button button-primary"
            onClick={() => void reconnect()}
            disabled={loading}
          >
            {loading ? 'Connecting…' : 'Try again'}
          </button>
        </section>
      </main>
    )
  }

  if (!household) return null

  return (
    <div className="app-shell">
      <header className="topbar">
        <Brand compact />
        <nav className="main-nav" aria-label="Main navigation">
          <button
            className={page === 'kitchen' ? 'nav-link active' : 'nav-link'}
            onClick={() => navigate('kitchen')}
          >
            Kitchen Home
          </button>
          <button
            className={page === 'household' || page === 'member' ? 'nav-link active' : 'nav-link'}
            onClick={() => navigate('household')}
          >
            Household
          </button>
          <button
            className={page === 'inventory' ? 'nav-link active' : 'nav-link'}
            onClick={() => navigate('inventory')}
          >
            Inventory
          </button>
        </nav>
        <div className="household-chip">
          <span className="status-dot" />
          {household.name}
        </div>
      </header>

      <main className="page-content">
        {page === 'kitchen' && (
          <KitchenHome
            household={household}
            onManage={() => navigate('household')}
            onInventory={() => navigate('inventory')}
          />
        )}
        {page === 'household' && (
          <HouseholdPage
            household={household}
            onAddMember={() => openMemberForm('add')}
            onEditMember={(member) => openMemberForm('edit', member)}
          />
        )}
        {page === 'member' && (
          <MemberForm
            mode={memberMode}
            member={editingMember}
            householdName={household.name}
            loading={loading}
            error={error}
            onSave={handleSaveMember}
            onCancel={() => navigate(memberMode === 'first' ? 'kitchen' : 'household')}
          />
        )}
        {page === 'inventory' && <InventoryPlaceholder onBack={() => navigate('kitchen')} />}
      </main>
      <footer className="app-footer">
        <span>ShelfLife</span>
        <span>Thoughtful kitchens start with what matters to you.</span>
      </footer>
    </div>
  )
}

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <a className={compact ? 'brand brand-compact' : 'brand'} href="/" aria-label="ShelfLife home">
      <span className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      <span className="brand-name">ShelfLife</span>
    </a>
  )
}

function ErrorNotice({ message }: { message: string }) {
  if (!message) return null
  return (
    <p className="error-notice" role="alert">
      {message}
    </p>
  )
}

function KitchenHome({
  household,
  onManage,
  onInventory,
}: {
  household: Household
  onManage: () => void
  onInventory: () => void
}) {
  return (
    <div className="content-column">
      <section className="hero-panel">
        <p className="eyebrow">Your kitchen, your rhythm</p>
        <h1>Welcome to {household.name}.</h1>
        <p>
          A calmer kitchen starts with remembering the people around your table.
        </p>
        <button className="button button-light" onClick={onManage}>
          View your household <span aria-hidden="true">→</span>
        </button>
        <div className="hero-illustration" aria-hidden="true">
          <span className="sun-shape" />
          <span className="bowl-shape" />
          <span className="leaf-shape leaf-one" />
          <span className="leaf-shape leaf-two" />
        </div>
      </section>
      <div className="overview-grid">
        <section className="overview-card people-card">
          <div className="card-icon people-icon" aria-hidden="true">⌂</div>
          <p className="eyebrow">Around your table</p>
          <h2>{household.members.length} household {household.members.length === 1 ? 'member' : 'members'}</h2>
          <p>
            {household.members.length
              ? 'Food needs and preferences are kept together for your household.'
              : 'Add the people you cook for and note what matters to them.'}
          </p>
          <button className="text-button" onClick={onManage}>
            {household.members.length ? 'Manage household' : 'Add your first member'} <span aria-hidden="true">→</span>
          </button>
        </section>
        <button className="overview-card inventory-card" onClick={onInventory}>
          <div className="card-icon pantry-icon" aria-hidden="true">◌</div>
          <p className="eyebrow">Coming soon</p>
          <h2>Your pantry, at a glance</h2>
          <p>Inventory tools are not available yet. This is where that future work will live.</p>
          <span className="text-button">About inventory <span aria-hidden="true">→</span></span>
        </button>
      </div>
    </div>
  )
}

function HouseholdPage({
  household,
  onAddMember,
  onEditMember,
}: {
  household: Household
  onAddMember: () => void
  onEditMember: (member: HouseholdMember) => void
}) {
  return (
    <div className="content-column">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Your kitchen circle</p>
          <h1>{household.name}</h1>
          <p>Hard constraints and soft preferences are kept distinct.</p>
        </div>
        <button className="button button-primary" onClick={onAddMember}>
          <span aria-hidden="true">＋</span> Add a member
        </button>
      </div>
      {household.members.length === 0 ? (
        <section className="empty-card">
          <div className="empty-mark" aria-hidden="true">⌂</div>
          <h2>Your table is ready</h2>
          <p>Add a household member to save their food needs and preferences.</p>
          <button className="button button-primary" onClick={onAddMember}>Add the first member</button>
        </section>
      ) : (
        <div className="member-grid">
          {household.members.map((member) => (
            <MemberCard key={member.personId} member={member} onEdit={() => onEditMember(member)} />
          ))}
        </div>
      )}
    </div>
  )
}

function MemberCard({
  member,
  onEdit,
}: {
  member: HouseholdMember
  onEdit: () => void
}) {
  const hardConstraints = [
    ['Allergies', member.allergies],
    ['Foods to avoid', member.prohibitedFoods],
    ['Dietary restrictions', [...member.dietaryRestrictions, ...member.constraints]],
  ] as const
  const softPreferences = [
    ['Dislikes', member.dislikes],
    ['Favorite foods', [...member.preferredFoods, ...member.preferences]],
    ['Textures', [...member.texturePreferences, ...(member.texture ? [member.texture] : [])]],
    ['Cuisines', member.cuisinePreferences],
    ['Spice', member.spiceLevel ? [member.spiceLevel] : []],
  ] as const

  return (
    <article className="member-card">
      <div className="member-heading">
        <div className="avatar" aria-hidden="true">{member.name.trim().charAt(0).toUpperCase()}</div>
        <div>
          <h2>{member.name}</h2>
          <p>Household member</p>
        </div>
        <button className="icon-button" onClick={onEdit} aria-label={`Edit ${member.name}'s food profile`}>
          Edit
        </button>
      </div>
      <div className="profile-section hard-section">
        <h3><span className="section-dot" />Hard constraints</h3>
        {hardConstraints.map(([label, values]) => (
          <ProfileRow key={label} label={label} values={values} />
        ))}
      </div>
      <div className="profile-section soft-section">
        <h3><span className="section-dot" />Soft preferences</h3>
        {softPreferences.map(([label, values]) => (
          <ProfileRow key={label} label={label} values={values} />
        ))}
      </div>
    </article>
  )
}

function ProfileRow({ label, values }: { label: string; values: readonly string[] }) {
  return (
    <div className="profile-row">
      <span>{label}</span>
      <strong>{values.length ? values.join(', ') : 'Not set'}</strong>
    </div>
  )
}

function MemberForm({
  mode,
  member,
  householdName,
  loading,
  error,
  onSave,
  onCancel,
}: {
  mode: MemberMode
  member: HouseholdMember | null
  householdName: string
  loading: boolean
  error: string
  onSave: (
    event: FormEvent<HTMLFormElement>,
    name: string,
    profile: MemberFoodProfile,
  ) => Promise<void>
  onCancel: () => void
}) {
  const [name, setName] = useState(member?.name ?? '')
  const [profile, setProfile] = useState<MemberFoodProfile>(
    member ? profileFromMember(member) : emptyProfile(),
  )
  const title = mode === 'edit' ? 'Update food profile' : 'Who’s around your table?'

  function updateList(field: ProfileField, values: string[]) {
    setProfile((current) => ({ ...current, [field]: values }))
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    void onSave(event, name.trim(), profile)
  }

  return (
    <div className="content-column form-content">
      <button className="back-link" onClick={onCancel}>← Back</button>
      <div className="section-heading form-heading">
        <div>
          <p className="eyebrow">{householdName}</p>
          <h1>{title}</h1>
          <p>
            {mode === 'edit'
              ? 'Keep the details that help ShelfLife care for this household member.'
              : 'Share a name and the food details that help ShelfLife feel at home.'}
          </p>
        </div>
        <span className="step-indicator">{mode === 'first' ? '01 / 02' : 'Household'}</span>
      </div>
      <form className="member-form" onSubmit={handleSubmit}>
        {mode !== 'edit' && (
          <label className="field-label member-name-field" htmlFor="member-name">
            Member name
            <input
              id="member-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="e.g. Alex"
              maxLength={120}
              required
            />
          </label>
        )}
        <div className="profile-form-grid">
          {profileGroups.map((group, index) => (
            <section className={`profile-form-card ${index === 0 ? 'hard-form-card' : 'soft-form-card'}`} key={group.title}>
              <div className="profile-form-title">
                <span className="section-dot" />
                <div>
                  <h2>{group.title}</h2>
                  <p>{group.description}</p>
                </div>
              </div>
              {group.fields.map(({ key, label, placeholder }) => (
                <TagInput
                  key={key}
                  field={key}
                  label={label}
                  placeholder={placeholder}
                  values={profile[key]}
                  onChange={updateList}
                />
              ))}
            </section>
          ))}
          <section className="profile-form-card spice-form-card">
            <div className="profile-form-title">
              <span className="spice-symbol" aria-hidden="true">✳</span>
              <div>
                <h2>Spice preference</h2>
                <p>A gentle guide to how much heat they enjoy.</p>
              </div>
            </div>
            <label className="field-label" htmlFor="spice-level">
              Preferred spice level
              <select
                id="spice-level"
                value={profile.spiceLevel ?? ''}
                onChange={(event) =>
                  setProfile((current) => ({
                    ...current,
                    spiceLevel: (event.target.value || null) as SpiceLevel | null,
                  }))
                }
              >
                <option value="">Not set</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </label>
          </section>
        </div>
        <ErrorNotice message={error} />
        <div className="form-actions">
          <button type="button" className="button button-quiet" onClick={onCancel} disabled={loading}>
            {mode === 'first' ? 'Do this later' : 'Cancel'}
          </button>
          <button className="button button-primary" disabled={loading}>
            {loading
              ? 'Saving…'
              : mode === 'edit'
                ? 'Save food profile'
                : mode === 'first'
                  ? 'Save and open Kitchen Home'
                  : 'Add to household'}
            {!loading && <span aria-hidden="true">→</span>}
          </button>
        </div>
      </form>
    </div>
  )
}

function TagInput({
  field,
  label,
  placeholder,
  values,
  onChange,
}: {
  field: ProfileField
  label: string
  placeholder: string
  values: string[]
  onChange: (field: ProfileField, values: string[]) => void
}) {
  const [value, setValue] = useState('')

  function addValue() {
    const normalized = value.trim()
    if (!normalized || values.some((item) => item.toLowerCase() === normalized.toLowerCase())) {
      setValue('')
      return
    }
    onChange(field, [...values, normalized])
    setValue('')
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter') {
      event.preventDefault()
      addValue()
    }
  }

  return (
    <div className="field-label tag-field">
      <label htmlFor={`profile-${field}`}>{label}</label>
      <div className="tag-entry">
        <input
          id={`profile-${field}`}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          maxLength={80}
        />
        <button type="button" className="add-tag-button" onClick={addValue} aria-label={`Add ${label.toLowerCase()}`}>
          +
        </button>
      </div>
      {values.length > 0 && (
        <ul className="tag-list" aria-label={`${label} selected`}>
          {values.map((item) => (
            <li key={item}>
              {item}
              <button
                type="button"
                onClick={() => onChange(field, values.filter((value) => value !== item))}
                aria-label={`Remove ${item} from ${label.toLowerCase()}`}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function InventoryPlaceholder({ onBack }: { onBack: () => void }) {
  return (
    <div className="content-column">
      <button className="back-link" onClick={onBack}>← Back</button>
      <section className="empty-card inventory-empty">
        <div className="empty-mark pantry-empty-mark" aria-hidden="true">◌</div>
        <p className="eyebrow">A future shelf</p>
        <h1>Your inventory is coming soon.</h1>
        <p>
          Pantry tracking is not available yet. For now, ShelfLife is helping
          you get the household details in place first.
        </p>
        <span className="coming-soon-pill">Coming soon</span>
      </section>
    </div>
  )
}

export default App
