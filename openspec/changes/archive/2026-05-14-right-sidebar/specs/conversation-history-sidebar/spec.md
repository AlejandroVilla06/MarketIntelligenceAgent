# conversation-history-sidebar Specification

## Purpose

Responsive right sidebar displaying date-grouped conversation history with client-side search, lazy loading, visual states, and user footer. Part of the 3-column chat layout.

## Requirements

### Requirement: Layout Architecture (R1)

The system SHALL render a 3-column layout on screens ≥ 1280px: Left Sidebar (272px) | Chat Area (flex-1, min-w-0) | Right Sidebar (320px). On screens 1024–1279px, the left sidebar SHALL be hidden behind a hamburger trigger, leaving Chat | Right Sidebar. On screens < 1024px, both sidebars SHALL be hidden, accessible via icon triggers (hamburger for left, clock for right). Opening one mobile Sheet SHALL close the other.

#### Scenario: Desktop 3-column layout

- GIVEN viewport width ≥ 1280px
- WHEN `/chat` page renders
- THEN left sidebar (272px), chat area, and right sidebar (320px) are all visible

#### Scenario: Tablet hides left sidebar

- GIVEN viewport 1024–1279px
- WHEN `/chat` page renders
- THEN left sidebar is hidden; chat area fills remaining space; right sidebar (320px) is visible

#### Scenario: Mobile hides both sidebars

- GIVEN viewport < 1024px
- WHEN `/chat` page renders
- THEN only the chat area is visible; hamburger and clock icons are present in the header

---

### Requirement: Smooth Layout Transitions (R2)

Width changes SHALL use Tailwind `transition-all duration-300`. Sidebar show/hide SHALL use `transition-transform duration-300`. Breakpoint shifts SHALL NOT cause abrupt visual jumps. The chat area SHALL use `flex-1 min-w-0` to smoothly fill available space.

#### Scenario: Resize across breakpoints

- GIVEN viewport is dragged from 1300px down to 1000px
- WHEN the layout reflows at the 1280px and 1024px breakpoints
- THEN sidebar visibility changes animate smoothly over 300ms
- AND no layout flash or jump occurs

#### Scenario: Mobile Sheet open/close

- GIVEN viewport < 1024px and the clock icon is tapped
- WHEN the right sidebar Sheet opens or closes
- THEN the transition animates smoothly via `transition-transform duration-300`

---

### Requirement: Conversation History List (R3)

The right sidebar SHALL fetch conversations from `api.conversations.list()` and display them grouped by date: "Hoy", "Ayer", "Esta semana", "Anteriores". Conversations SHALL be ordered by `updated_at` DESC within each group. Empty state SHALL display "No hay conversaciones aún".

#### Scenario: Conversations grouped by date

- GIVEN conversations updated today, yesterday, 4 days ago, and 2 weeks ago
- WHEN the right sidebar renders
- THEN four groups appear: Hoy (1), Ayer (1), Esta semana (1), Anteriores (1)

#### Scenario: Empty state

- GIVEN user has no conversations
- WHEN the right sidebar renders
- THEN "No hay conversaciones aún" is displayed

---

### Requirement: Lazy Loading / Pagination (R4)

The system SHALL initially load 20 conversations. When the user scrolls to the list bottom, the next 20 SHALL load. A loading indicator SHALL display during fetch. Pagination SHALL use `offset` and `limit` parameters via `api.conversations.list()`. If total < 20, no further requests SHALL be made.

#### Scenario: Initial load of first 20

- GIVEN user has 50 conversations
- WHEN the right sidebar mounts
- THEN `api.conversations.list({ limit: 20, offset: 0 })` is called
- AND 20 conversations render

#### Scenario: Scroll triggers next page

- GIVEN 20 conversations are displayed and more exist
- WHEN user scrolls to the bottom of the list
- THEN a skeleton/spinner loading indicator appears
- AND `api.conversations.list({ limit: 20, offset: 20 })` is called
- AND next 20 conversations append to the list

#### Scenario: No more pages

- GIVEN all conversations are loaded (total = 15)
- WHEN user scrolls to the bottom
- THEN no additional fetch is triggered

---

### Requirement: ConversationItem Visual States (R5)

Active conversation SHALL have `bg-primary/10 text-primary`. Hover SHALL show `hover:bg-muted`. Focus-visible SHALL show `focus-visible:ring-2 focus-visible:ring-ring`. Delete button SHALL be `opacity-0 group-hover:opacity-100`. The component SHALL use `cn()` utility for conditional class merging. Dark/light SHALL use Tailwind semantic classes.

#### Scenario: Active conversation selected

- GIVEN conversation "AAPL Analysis" is the current conversation
- WHEN the right sidebar renders
- THEN that entry has `bg-primary/10` background and `text-primary` text

#### Scenario: Hover reveals delete button

- GIVEN the right sidebar shows conversation entries
- WHEN user hovers over an entry
- THEN its delete button fades in via `opacity-0 group-hover:opacity-100`

#### Scenario: Keyboard focus

- GIVEN user tabs through conversation entries
- WHEN an entry receives focus
- THEN `focus-visible:ring-2 focus-visible:ring-ring` is applied

---

### Requirement: ConversationSearch (R6)

A search input SHALL filter conversations client-side by title with a 300ms debounce. The input SHALL display a search icon. Empty results SHALL display "No se encontraron conversaciones".

#### Scenario: Search filters by title

- GIVEN conversations "AAPL Analysis", "TSLA Report", "Bitcoin Trends"
- WHEN user types "AAPL" in the search input
- THEN only "AAPL Analysis" remains visible after 300ms

#### Scenario: No matching results

- GIVEN conversations "AAPL", "TSLA" exist
- WHEN user types "XYZ"
- THEN "No se encontraron conversaciones" is displayed

---

### Requirement: New Chat Button (R7)

A "Nuevo Chat" button SHALL render at the bottom of the right sidebar. Clicking it SHALL call `api.conversations.create()` and update `chatStore` identically to the left sidebar's button.

#### Scenario: New Chat from right sidebar

- GIVEN user clicks "Nuevo Chat" in the right sidebar
- WHEN the API call succeeds
- THEN a new conversation is created; chat area clears; both sidebars update their lists

---

### Requirement: User Footer (R8)

The right sidebar SHALL display the authenticated user's email and avatar at the bottom. A logout button SHALL be available.

#### Scenario: User footer renders

- GIVEN user is authenticated with email "trader@example.com"
- WHEN the right sidebar renders
- THEN the footer shows the email and avatar
- AND a logout button is present

#### Scenario: Logout

- GIVEN user clicks the logout button
- WHEN logout completes
- THEN user is redirected to `/login`
