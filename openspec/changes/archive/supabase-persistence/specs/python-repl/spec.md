# Delta for python-repl

## ADDED Requirements

### Requirement: Cross-Session History Access (R8)

The CalculationExecutor SHALL support retrieving conversation history from previous sessions to enable context-aware financial calculations. History access SHALL be filtered by the active `user_id` to maintain user isolation. Calculations MAY reference historical data for comparative analysis. Historical context SHALL be limited to the last 10 conversations for performance.

#### Scenario: Retrieve history from previous sessions

- GIVEN user `u1` has 5 conversations with financial data from prior sessions
- WHEN CalculationExecutor queries historical conversations for user `u1`
- THEN all 5 conversations SHALL be accessible, ordered by `updated_at DESC`

#### Scenario: History is user-isolated

- GIVEN user A has 3 conversations and user B has 4 conversations
- WHEN CalculationExecutor queries history for user A
- THEN only user A's 3 conversations SHALL be returned; user B's data SHALL NOT appear

#### Scenario: Historical data used in calculations

- GIVEN a previous conversation contains "NPV for project X = $10,000"
- WHEN user asks "compare this week's NPV with last week's"
- THEN CalculationExecutor SHALL include the historical NPV value in the calculation context

#### Scenario: History limited to last 10 conversations

- GIVEN user has 25 conversations in the database
- WHEN CalculationExecutor retrieves historical context
- THEN at most 10 conversations SHALL be included in the context window

#### Scenario: Empty history for new user

- GIVEN a new user with zero previous conversations
- WHEN CalculationExecutor queries history
- THEN an empty result set SHALL be returned without error
