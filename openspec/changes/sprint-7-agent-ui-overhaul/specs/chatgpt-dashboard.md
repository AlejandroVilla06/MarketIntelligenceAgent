# Spec: ChatGPT-like Dashboard

## Purpose

Rediseñar el dashboard de Streamlit para que se parezca a ChatGPT: sidebar con historial de conversaciones, pantalla de bienvenida con sugerencias, input tipo ChatGPT, y tema oscuro profesional.

## Requirements

### Requirement: Sidebar with Chat History

The dashboard SHALL display a persistent sidebar with conversation history, similar to ChatGPT.

#### Scenario: Sidebar visible with history
- GIVEN the dashboard is loaded
- WHEN the user looks at the sidebar
- THEN the sidebar SHALL be visible on the left side
- AND SHALL display previous conversation entries as clickable items
- AND SHALL have a "New Chat" button at the top
- AND SHALL show the current date and time

#### Scenario: New chat creation
- GIVEN the sidebar is visible
- WHEN the user clicks "New Chat"
- THEN the current conversation SHALL be saved to history
- AND a new blank conversation SHALL start
- AND the welcome screen SHALL be displayed

#### Scenario: Resume old conversation
- GIVEN the sidebar has history entries
- WHEN the user clicks a history item
- THEN the messages from that conversation SHALL be loaded
- AND the user can continue from where they left off

### Requirement: Welcome Screen

The dashboard SHALL display a welcoming landing screen with suggested questions when no conversation is active.

#### Scenario: Welcome screen on first load
- GIVEN the user opens the dashboard for the first time
- WHEN no conversation history exists
- THEN the main area SHALL display:
  - App logo/icon
  - Title: "Market Intelligence Agent"
  - Subtitle explaining capabilities
  - 4-6 suggested question buttons in a grid

#### Scenario: Suggested questions are clickable
- GIVEN the welcome screen with suggestions
- WHEN the user clicks a suggestion
- THEN the suggestion text SHALL be sent as a query
- AND the agent SHALL respond

### Requirement: Chat Input

The input area SHALL be fixed at the bottom, styled like ChatGPT with auto-resize and send button.

#### Scenario: Input fixed at bottom
- GIVEN the dashboard is loaded
- WHEN the user scrolls
- THEN the input area SHALL remain fixed at the bottom
- AND SHALL have a subtle gradient overlay above it

#### Scenario: Send message
- GIVEN the user has typed a message
- WHEN they press Enter or click Send
- THEN the message SHALL appear as a user bubble
- AND a typing indicator SHALL appear
- AND the agent response SHALL appear

### Requirement: Message Display

Messages SHALL be displayed as styled bubbles with clear user/assistant distinction.

#### Scenario: User message bubble
- GIVEN the user sent a message
- WHEN it is displayed
- THEN it SHALL appear right-aligned with a distinct background color
- AND SHALL have the user's label

#### Scenario: Assistant message
- GIVEN the agent generated a response
- WHEN it is displayed
- THEN it SHALL appear left-aligned
- AND SHALL render markdown content (headings, lists, code)
- AND SHALL show a model/agent label

## Non-Functional Requirements

### Performance
- The sidebar SHALL render without blocking the main chat area
- History items SHALL be stored in session state (not persisted to disk)

### Constraints
- All styling SHALL use the external `dashboard.css` file (NOT inline CSS)
- The sidebar SHALL use Streamlit native `st.sidebar` with custom CSS, NOT `st.container` hacks
