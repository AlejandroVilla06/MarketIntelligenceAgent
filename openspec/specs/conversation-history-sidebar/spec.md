# conversation-history-sidebar Specification

## Purpose

Responsive right sidebar displaying date-grouped conversation history with client-side search, lazy loading, visual states, and user footer. Part of the 3-column chat layout.

## Requirements

| ID | Requirement |
|----|-------------|
| R1 | **Layout Architecture**: 3-column layout on screens ≥1280px: Left Sidebar (272px) \| Chat Area (flex-1, min-w-0) \| Right Sidebar (320px). On screens 1024–1279px, left sidebar hides behind hamburger trigger, leaving Chat \| Right Sidebar. On screens <1024px, both sidebars hidden, accessible via icon triggers (hamburger for left, clock for right). Opening one mobile Sheet closes the other. |
| R2 | **Smooth Layout Transitions**: Width changes use Tailwind `transition-all duration-300`. Sidebar show/hide uses `transition-transform duration-300`. Breakpoint shifts do not cause abrupt visual jumps. Chat area uses `flex-1 min-w-0` to smoothly fill space. |
| R3 | **Conversation History List**: Right sidebar fetches conversations from `api.conversations.list()` and displays them grouped by date: "Hoy", "Ayer", "Esta semana", "Anteriores". Conversations ordered by `updated_at` DESC within each group. Empty state displays "No hay conversaciones aún". |
| R4 | **Lazy Loading / Pagination**: Initially loads 20 conversations. When user scrolls to list bottom, next 20 load. Loading indicator displays during fetch. Pagination uses `offset` and `limit` parameters via `api.conversations.list()`. If total <20, no further requests made. |
| R5 | **ConversationItem Visual States**: Active conversation has `bg-primary/10 text-primary`. Hover shows `hover:bg-muted`. Focus-visible shows `focus-visible:ring-2 focus-visible:ring-ring`. Delete button is `opacity-0 group-hover:opacity-100`. Component uses `cn()` utility. Dark/light uses Tailwind semantic classes. |
| R6 | **ConversationSearch**: Search input filters conversations client-side by title with 300ms debounce. Input displays search icon. Empty results display "No se encontraron conversaciones". |
| R7 | **New Chat Button**: "Nuevo Chat" button renders at bottom of right sidebar. Clicking calls `api.conversations.create()` and updates `chatStore` identically to left sidebar's button. |
| R8 | **User Footer**: Right sidebar displays authenticated user's email and avatar at bottom. Logout button available. |

## Scenarios

### R1: Layout Architecture

- GIVEN viewport width ≥1280px
- WHEN `/chat` page renders
- THEN left sidebar (272px), chat area, and right sidebar (320px) are all visible

- GIVEN viewport 1024–1279px
- WHEN `/chat` page renders
- THEN left sidebar is hidden; chat area fills remaining space; right sidebar (320px) is visible

- GIVEN viewport <1024px
- WHEN `/chat` page renders
- THEN only the chat area is visible; hamburger and clock icons are present in the header

### R2: Smooth Layout Transitions

- GIVEN viewport is dragged from 1300px down to 1000px
- WHEN the layout reflows at the 1280px and 1024px breakpoints
- THEN sidebar visibility changes animate smoothly over 300ms
- AND no layout flash or jump occurs

- GIVEN viewport <1024px and the clock icon is tapped
- WHEN the right sidebar Sheet opens or closes
- THEN the transition animates smoothly via `transition-transform duration-300`

### R3: Conversation History List

- GIVEN conversations updated today, yesterday, 4 days ago, and 2 weeks ago
- WHEN the right sidebar renders
- THEN four groups appear: Hoy (1), Ayer (1), Esta semana (1), Anteriores (1)

- GIVEN user has no conversations
- WHEN the right sidebar renders
- THEN "No hay conversaciones aún" is displayed

### R4: Lazy Loading / Pagination

- GIVEN user has 50 conversations
- WHEN the right sidebar mounts
- THEN `api.conversations.list({ limit: 20, offset: 0 })` is called
- AND 20 conversations render

- GIVEN 20 conversations are displayed and more exist
- WHEN user scrolls to the bottom of the list
- THEN a skeleton/spinner loading indicator appears
- AND `api.conversations.list({ limit: 20, offset: 20 })` is called
- AND next 20 conversations append to the list

- GIVEN all conversations are loaded (total = 15)
- WHEN user scrolls to the bottom
- THEN no additional fetch is triggered

### R5: ConversationItem Visual States

- GIVEN conversation "AAPL Analysis" is the current conversation
- WHEN the right sidebar renders
- THEN that entry has `bg-primary/10` background and `text-primary` text

- GIVEN the right sidebar shows conversation entries
- WHEN user hovers over an entry
- THEN its delete button fades in via `opacity-0 group-hover:opacity-100`

- GIVEN user tabs through conversation entries
- WHEN an entry receives focus
- THEN `focus-visible:ring-2 focus-visible:ring-ring` is applied

### R6: ConversationSearch

- GIVEN conversations "AAPL Analysis", "TSLA Report", "Bitcoin Trends"
- WHEN user types "AAPL" in the search input
- THEN only "AAPL Analysis" remains visible after 300ms

- GIVEN conversations "AAPL", "TSLA" exist
- WHEN user types "XYZ"
- THEN "No se encontraron conversaciones" is displayed

### R7: New Chat Button

- GIVEN user clicks "Nuevo Chat" in the right sidebar
- WHEN the API call succeeds
- THEN a new conversation is created; chat area clears; both sidebars update their lists

### R8: User Footer

- GIVEN user is authenticated with email "trader@example.com"
- WHEN the right sidebar renders
- THEN the footer shows the email and avatar
- AND a logout button is present

- GIVEN user clicks the logout button
- WHEN logout completes
- THEN user is redirected to `/login`