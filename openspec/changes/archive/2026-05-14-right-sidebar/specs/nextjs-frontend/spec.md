# Delta for nextjs-frontend

## MODIFIED Requirements

### Requirement: Conversation Sidebar (R6)

The system SHALL render a left sidebar with conversation list (title + delete) and a right sidebar with date-grouped history. The left sidebar SHALL provide quick nav and conversation CRUD; the right sidebar SHALL provide chronological context with client-side search. Both sidebars SHALL share the "New Chat" action. On desktop (≥ 1280px), both SHALL be visible. On tablet (1024–1279px), the left sidebar SHALL hide behind a hamburger; the right SHALL remain visible. On mobile (< 1024px), both SHALL be hidden with distinct icon triggers: hamburger (left) and clock (right). Opening one mobile Sheet SHALL close the other.
(Previously: Left sidebar with conversation list, new chat, and hamburger toggle for mobile.)

#### Scenario: Left sidebar click loads conversation

- GIVEN sidebar shows conversation "AAPL Analysis"
- WHEN user clicks it
- THEN chat area loads that conversation's messages

#### Scenario: Right sidebar click loads conversation

- GIVEN right sidebar shows "TSLA Report" under "Hoy"
- WHEN user clicks it
- THEN chat area loads that conversation's messages
- AND left sidebar highlights the same conversation

#### Scenario: New Chat creates conversation

- GIVEN user clicks "New Chat" from either sidebar
- WHEN conversation is created
- THEN both sidebars add a new entry; chat area clears to empty

#### Scenario: Mobile hamburger opens left sidebar

- GIVEN viewport < 1024px
- WHEN `/chat` page loads
- THEN left sidebar is hidden; hamburger menu icon is visible in the header

#### Scenario: Mobile clock opens right sidebar

- GIVEN viewport < 1024px
- WHEN user taps the clock icon
- THEN right sidebar slides in via Sheet; any open left sidebar Sheet closes

#### Scenario: Mobile left-right mutual exclusion

- GIVEN right sidebar Sheet is open on mobile
- WHEN user taps the hamburger icon
- THEN the right Sheet closes and the left Sheet opens

### Requirement: Responsive Design (R9)

The system SHALL render a 3-column layout at ≥ 1280px, 2-column (Chat | Right Sidebar) at 1024–1279px, and single-column at < 1024px. Layout transitions SHALL use Tailwind `transition-all duration-300` and `transition-transform duration-300`. Right sidebar SHALL have a clock icon trigger on mobile. Chat input SHALL remain visible with virtual keyboard open. Usable at ≥ 320px.
(Previously: 2-column layout with left sidebar hidden on mobile via hamburger.)

#### Scenario: Mobile hamburger opens left sidebar

- GIVEN viewport < 1024px
- WHEN user taps the hamburger icon
- THEN left sidebar slides in from the left

#### Scenario: Mobile clock opens right sidebar

- GIVEN viewport < 1024px
- WHEN user taps the clock icon in the header
- THEN right sidebar slides in from the right via Sheet

#### Scenario: Mobile keyboard visibility

- GIVEN mobile user at `/chat` taps the chat input
- WHEN the virtual keyboard opens
- THEN the input field remains visible above the keyboard

#### Scenario: Smooth resize transition

- GIVEN viewport is resized from 1300px to 1000px
- WHEN breakpoints at 1280px and 1024px trigger layout changes
- THEN sidebar visibility changes animate smoothly without abrupt jumps

## ADDED Requirements

### Requirement: Layout Transitions (R10)

The left sidebar SHALL use `transition-transform duration-300` for show/hide. The right sidebar SHALL use `transition-all duration-300` for width changes. The chat area SHALL use `flex-1 min-w-0` to smoothly fill available space. Breakpoint shifts SHALL NOT cause abrupt visual jumps.

#### Scenario: Sidebar width animates

- GIVEN user resizes the viewport across the 1280px breakpoint
- WHEN the left sidebar toggles between hidden and visible
- THEN the transition animates over 300ms without layout flash

#### Scenario: Chat area smoothly fills space

- GIVEN the right sidebar is toggled on mobile via Sheet
- WHEN the Sheet opens or closes
- THEN the chat area gracefully adjusts to the remaining space
