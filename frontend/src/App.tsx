import { useEffect, useState, type FormEvent, type KeyboardEvent } from 'react'
import {
  addHouseholdMember,
  ApiError,
  consumeInventoryItem,
  createHousehold,
  createInventoryItem,
  deleteInventoryItem,
  getInventory,
  getHousehold,
  updateInventoryItem,
  updateMemberFoodProfile,
} from './services/api'
import type {
  Household,
  HouseholdMember,
  InventoryInput,
  InventoryItem,
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
        {page === 'inventory' && (
          <InventoryPage
            householdId={household.householdId}
            onBack={() => navigate('kitchen')}
          />
        )}
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
          <p className="eyebrow">Your pantry</p>
          <h2>Your pantry, at a glance</h2>
          <p>Keep track of what is on hand, what is expiring, and what you have used.</p>
          <span className="text-button">Open inventory <span aria-hidden="true">→</span></span>
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

type InventoryFormState = { [K in keyof InventoryInput]: string }

const inventoryCategories = [
  'produce',
  'dairy',
  'protein',
  'grains',
  'pantry',
  'other',
]

function sortInventory(items: InventoryItem[]): InventoryItem[] {
  return [...items].sort((left, right) => {
    if (left.expiryDate === null) return right.expiryDate === null ? 0 : 1
    if (right.expiryDate === null) return -1
    return left.expiryDate.localeCompare(right.expiryDate)
  })
}

function newInventoryForm(): InventoryFormState {
  return {
    ingredient: '',
    category: 'produce',
    quantity: '',
    unit: '',
    purchaseDate: '',
    expiryDate: '',
    storage: '',
    notes: '',
  }
}

function inventoryFormFromItem(item: InventoryItem): InventoryFormState {
  return {
    ingredient: item.ingredient,
    category: item.category,
    quantity: String(item.quantity),
    unit: item.unit,
    purchaseDate: item.purchaseDate ?? '',
    expiryDate: item.expiryDate ?? '',
    storage: item.storage ?? '',
    notes: item.notes ?? '',
  }
}

function inventoryErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Something went wrong while updating inventory. Please try again.'
}

function InventoryPage({
  householdId,
  onBack,
}: {
  householdId: string
  onBack: () => void
}) {
  const [items, setItems] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [formError, setFormError] = useState('')
  const [notice, setNotice] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [busyItemId, setBusyItemId] = useState<string | null>(null)
  const [reloadCount, setReloadCount] = useState(0)

  useEffect(() => {
    let active = true
    getInventory(householdId)
      .then((inventory) => {
        if (!active) return
        setItems(sortInventory(inventory))
        setLoadError('')
      })
      .catch((requestError: unknown) => {
        if (active) setLoadError(inventoryErrorMessage(requestError))
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [householdId, reloadCount])

  function retryLoad() {
    setLoading(true)
    setLoadError('')
    setReloadCount((count) => count + 1)
  }

  function openNewItemForm() {
    setEditingItem(null)
    setFormError('')
    setFormOpen(true)
  }

  function openEditItemForm(item: InventoryItem) {
    setEditingItem(item)
    setFormError('')
    setFormOpen(true)
  }

  async function saveItem(input: InventoryInput) {
    setFormError('')
    setNotice('')
    setSaving(true)
    try {
      if (editingItem) {
        const updated = await updateInventoryItem(
          householdId,
          editingItem.inventoryId,
          input,
        )
        setItems((current) =>
          sortInventory(
            current.map((item) =>
              item.inventoryId === updated.inventoryId ? updated : item,
            ),
          ),
        )
        setNotice(`${updated.ingredient} was updated.`)
      } else {
        const created = await createInventoryItem(householdId, input)
        setItems((current) => sortInventory([...current, created]))
        setNotice(`${created.ingredient} was added to inventory.`)
      }
      setFormOpen(false)
      setEditingItem(null)
    } catch (requestError) {
      setFormError(inventoryErrorMessage(requestError))
    } finally {
      setSaving(false)
    }
  }

  async function removeItem(item: InventoryItem) {
    setNotice('')
    setBusyItemId(item.inventoryId)
    try {
      await deleteInventoryItem(householdId, item.inventoryId)
      setItems((current) =>
        current.filter((entry) => entry.inventoryId !== item.inventoryId),
      )
      setDeleteTarget(null)
      setNotice(`${item.ingredient} was removed from inventory.`)
    } catch (requestError) {
      setLoadError(inventoryErrorMessage(requestError))
    } finally {
      setBusyItemId(null)
    }
  }

  async function recordConsumption(item: InventoryItem, quantity: number) {
    setNotice('')
    setBusyItemId(item.inventoryId)
    try {
      const updated = await consumeInventoryItem(
        householdId,
        item.inventoryId,
        quantity,
      )
      setItems((current) =>
        current.map((entry) =>
          entry.inventoryId === updated.inventoryId ? updated : entry,
        ),
      )
      setNotice(
        updated.quantity === 0
          ? `${item.ingredient} was used up.`
          : `Recorded ${quantity} ${item.unit} used from ${item.ingredient}.`,
      )
    } catch (requestError) {
      setLoadError(inventoryErrorMessage(requestError))
    } finally {
      setBusyItemId(null)
    }
  }

  const availableItems = items.filter((item) => item.quantity > 0)
  const usedUpItems = items.filter((item) => item.quantity === 0)
  const useSoonCount = availableItems.filter(
    (item) => item.status === 'USE_SOON' || item.status === 'EXPIRING',
  ).length
  const expiredCount = availableItems.filter((item) => item.status === 'EXPIRED').length

  return (
    <div className="content-column inventory-page">
      <button className="back-link" onClick={onBack}>← Kitchen Home</button>
      <div className="section-heading inventory-heading">
        <div>
          <p className="eyebrow">What’s on your shelves</p>
          <h1>Kitchen inventory</h1>
          <p>Keep quantities and dates current so nothing gets forgotten.</p>
        </div>
        <button className="button button-primary" onClick={openNewItemForm}>
          <span aria-hidden="true">＋</span> Add an item
        </button>
      </div>

      {loadError && (
        <div>
          <ErrorNotice message={loadError} />
          {!loading && (
            <button className="text-button retry-button" onClick={retryLoad}>
              Retry loading inventory
            </button>
          )}
        </div>
      )}
      {notice && <p className="success-notice" role="status">{notice}</p>}

      <section className="inventory-summary" aria-label="Inventory summary">
        <div>
          <span className="summary-number">{loading ? '—' : availableItems.length}</span>
          <span className="summary-label">items in stock</span>
        </div>
        <div>
          <span className="summary-number use-soon-number">{loading ? '—' : useSoonCount}</span>
          <span className="summary-label">use soon</span>
        </div>
        <div>
          <span className="summary-number expired-number">{loading ? '—' : expiredCount}</span>
          <span className="summary-label">past expiry</span>
        </div>
      </section>

      {formOpen && (
        <InventoryForm
          item={editingItem}
          saving={saving}
          error={formError}
          onSave={saveItem}
          onCancel={() => {
            setFormOpen(false)
            setEditingItem(null)
          }}
        />
      )}

      {loading ? (
        <section className="empty-card inventory-loading" aria-live="polite">
          <p className="eyebrow">One moment</p>
          <h2>Loading your inventory…</h2>
        </section>
      ) : availableItems.length === 0 && usedUpItems.length === 0 ? (
        <section className="empty-card inventory-empty">
          <div className="empty-mark pantry-empty-mark" aria-hidden="true">◌</div>
          <p className="eyebrow">A good place to begin</p>
          <h2>Your shelves are ready to remember.</h2>
          <p>Add ingredients with their amounts and dates. ShelfLife will keep expiry status visible here.</p>
          <button className="button button-primary" onClick={openNewItemForm}>
            Add your first ingredient
          </button>
        </section>
      ) : (
        <div className="inventory-sections">
          <section className="inventory-list-section">
            <div className="inventory-list-heading">
              <div>
                <p className="eyebrow">In the kitchen</p>
                <h2>On hand <span>{availableItems.length}</span></h2>
              </div>
              <p>Sorted by the nearest known expiry date.</p>
            </div>
            {availableItems.length === 0 ? (
              <p className="inventory-empty-note">No ingredients currently in stock.</p>
            ) : (
              <div className="inventory-grid">
                {availableItems.map((item) => (
                  <InventoryCard
                    key={item.inventoryId}
                    item={item}
                    busy={busyItemId === item.inventoryId}
                    confirmingDelete={deleteTarget === item.inventoryId}
                    onEdit={() => openEditItemForm(item)}
                    onDeleteRequest={() => setDeleteTarget(item.inventoryId)}
                    onDeleteCancel={() => setDeleteTarget(null)}
                    onDelete={() => void removeItem(item)}
                    onConsume={(quantity) => void recordConsumption(item, quantity)}
                  />
                ))}
              </div>
            )}
          </section>
          {usedUpItems.length > 0 && (
            <section className="inventory-list-section used-up-section">
              <div className="inventory-list-heading">
                <div>
                  <p className="eyebrow">Consumption history</p>
                  <h2>Used up <span>{usedUpItems.length}</span></h2>
                </div>
              </div>
              <div className="inventory-grid">
                {usedUpItems.map((item) => (
                  <InventoryCard
                    key={item.inventoryId}
                    item={item}
                    busy={busyItemId === item.inventoryId}
                    confirmingDelete={deleteTarget === item.inventoryId}
                    onEdit={() => openEditItemForm(item)}
                    onDeleteRequest={() => setDeleteTarget(item.inventoryId)}
                    onDeleteCancel={() => setDeleteTarget(null)}
                    onDelete={() => void removeItem(item)}
                    onConsume={() => undefined}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}

function InventoryForm({
  item,
  saving,
  error,
  onSave,
  onCancel,
}: {
  item: InventoryItem | null
  saving: boolean
  error: string
  onSave: (input: InventoryInput) => Promise<void>
  onCancel: () => void
}) {
  const [values, setValues] = useState<InventoryFormState>(
    item ? inventoryFormFromItem(item) : newInventoryForm(),
  )

  function update<K extends keyof InventoryFormState>(
    key: K,
    value: InventoryFormState[K],
  ) {
    setValues((current) => ({ ...current, [key]: value }))
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void onSave({
      ...values,
      quantity: Number(values.quantity),
      purchaseDate: values.purchaseDate || null,
      expiryDate: values.expiryDate || null,
      storage: values.storage || null,
      notes: values.notes.trim() || null,
    })
  }

  return (
    <form className="inventory-form" onSubmit={submit}>
      <div className="inventory-form-heading">
        <div>
          <p className="eyebrow">{item ? 'Keep it up to date' : 'Add to the shelves'}</p>
          <h2>{item ? `Edit ${item.ingredient}` : 'Add an ingredient'}</h2>
        </div>
        <button type="button" className="icon-button" onClick={onCancel} disabled={saving}>
          Close
        </button>
      </div>
      <div className="inventory-fields-grid">
        <label className="field-label" htmlFor="inventory-ingredient">
          Ingredient
          <input
            id="inventory-ingredient"
            value={values.ingredient}
            onChange={(event) => update('ingredient', event.target.value)}
            placeholder="e.g. Spinach"
            maxLength={120}
            required
          />
        </label>
        <label className="field-label" htmlFor="inventory-category">
          Category
          <select
            id="inventory-category"
            value={values.category}
            onChange={(event) => update('category', event.target.value)}
            required
          >
            {inventoryCategories.map((category) => (
              <option key={category} value={category}>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </option>
            ))}
          </select>
        </label>
        <label className="field-label" htmlFor="inventory-quantity">
          Quantity
          <input
            id="inventory-quantity"
            type="number"
            min="0.000001"
            step="any"
            value={values.quantity}
            onChange={(event) => update('quantity', event.target.value)}
            required
          />
        </label>
        <label className="field-label" htmlFor="inventory-unit">
          Unit
          <input
            id="inventory-unit"
            value={values.unit}
            onChange={(event) => update('unit', event.target.value)}
            placeholder="e.g. g, kg, pieces"
            maxLength={30}
            required
          />
        </label>
        <label className="field-label" htmlFor="inventory-purchase-date">
          Purchase date <span className="optional-label">Optional</span>
          <input
            id="inventory-purchase-date"
            type="date"
            value={values.purchaseDate}
            onChange={(event) => update('purchaseDate', event.target.value)}
          />
        </label>
        <label className="field-label" htmlFor="inventory-expiry-date">
          Expiry date <span className="optional-label">Optional</span>
          <input
            id="inventory-expiry-date"
            type="date"
            min={values.purchaseDate || undefined}
            value={values.expiryDate}
            onChange={(event) => update('expiryDate', event.target.value)}
          />
        </label>
        <label className="field-label" htmlFor="inventory-storage">
          Storage location <span className="optional-label">Optional</span>
          <select
            id="inventory-storage"
            value={values.storage}
            onChange={(event) => update('storage', event.target.value)}
          >
            <option value="">Not set</option>
            <option value="pantry">Pantry</option>
            <option value="refrigerator">Refrigerator</option>
            <option value="freezer">Freezer</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label className="field-label inventory-notes-field" htmlFor="inventory-notes">
          Notes <span className="optional-label">Optional</span>
          <textarea
            id="inventory-notes"
            value={values.notes ?? ''}
            onChange={(event) => update('notes', event.target.value)}
            maxLength={500}
            rows={2}
            placeholder="Anything useful to remember"
          />
        </label>
      </div>
      <ErrorNotice message={error} />
      <div className="form-actions inventory-form-actions">
        <button type="button" className="button button-quiet" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
        <button className="button button-primary" disabled={saving}>
          {saving ? 'Saving…' : item ? 'Save changes' : 'Add to inventory'}
        </button>
      </div>
    </form>
  )
}

function InventoryCard({
  item,
  busy,
  confirmingDelete,
  onEdit,
  onDeleteRequest,
  onDeleteCancel,
  onDelete,
  onConsume,
}: {
  item: InventoryItem
  busy: boolean
  confirmingDelete: boolean
  onEdit: () => void
  onDeleteRequest: () => void
  onDeleteCancel: () => void
  onDelete: () => void
  onConsume: (quantity: number) => void
}) {
  const [consumeQuantity, setConsumeQuantity] = useState('')
  const isUsedUp = item.quantity === 0

  function submitConsumption(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const quantity = Number(consumeQuantity)
    if (Number.isFinite(quantity) && quantity > 0) {
      onConsume(quantity)
      setConsumeQuantity('')
    }
  }

  return (
    <article className={`inventory-card-item ${isUsedUp ? 'inventory-card-used' : ''}`}>
      <div className="inventory-item-top">
        <span className={`inventory-status status-${isUsedUp ? 'used' : item.status.toLowerCase()}`}>
          {isUsedUp ? 'Used up' : item.status.replace('_', ' ')}
        </span>
        <span className="inventory-category">{item.category}</span>
      </div>
      <div className="inventory-item-title">
        <div>
          <h3>{item.ingredient}</h3>
          <p className="inventory-amount">
            {item.quantity} {item.unit}
          </p>
        </div>
        <div className="inventory-item-actions">
          <button className="icon-button" onClick={onEdit} disabled={busy}>
            Edit
          </button>
          <button
            className="icon-button icon-button-danger"
            onClick={onDeleteRequest}
            disabled={busy}
          >
            Remove
          </button>
        </div>
      </div>
      <dl className="inventory-details">
        <div>
          <dt>Expiry</dt>
          <dd>{item.expiryDate ? formatInventoryDate(item.expiryDate) : 'Not set'}</dd>
        </div>
        <div>
          <dt>Storage</dt>
          <dd>{item.storage ?? 'Not set'}</dd>
        </div>
        {item.purchaseDate && (
          <div>
            <dt>Purchased</dt>
            <dd>{formatInventoryDate(item.purchaseDate)}</dd>
          </div>
        )}
      </dl>
      {item.notes && <p className="inventory-item-notes">{item.notes}</p>}
      {!isUsedUp && (
        <form className="consume-form" onSubmit={submitConsumption}>
          <label htmlFor={`consume-${item.inventoryId}`}>Record amount used</label>
          <div>
            <input
              id={`consume-${item.inventoryId}`}
              type="number"
              min="0.000001"
              max={item.quantity}
              step="any"
              value={consumeQuantity}
              onChange={(event) => setConsumeQuantity(event.target.value)}
              required
            />
            <button
              type="submit"
              className="text-button"
              disabled={busy || !consumeQuantity}
            >
              {busy ? 'Saving…' : 'Record use'}
            </button>
          </div>
        </form>
      )}
      {item.consumptionHistory.length > 0 && (
        <details className="consumption-history">
          <summary>
            Consumption history ({item.consumptionHistory.length})
          </summary>
          <ul>
            {item.consumptionHistory.map((record, index) => (
              <li key={`${record.consumedAt}-${index}`}>
                {record.quantity} {item.unit} · {formatInventoryDate(record.consumedAt.slice(0, 10))}
              </li>
            ))}
          </ul>
        </details>
      )}
      {confirmingDelete && (
        <div className="delete-confirmation" role="group" aria-label={`Remove ${item.ingredient}`}>
          <p>Remove {item.ingredient} and its consumption history?</p>
          <button className="button button-quiet" onClick={onDeleteCancel} disabled={busy}>
            Keep item
          </button>
          <button className="button button-danger" onClick={onDelete} disabled={busy}>
            {busy ? 'Removing…' : 'Remove item'}
          </button>
        </div>
      )}
    </article>
  )
}

function formatInventoryDate(value: string): string {
  const date = new Date(`${value.slice(0, 10)}T12:00:00`)
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
}

export default App
