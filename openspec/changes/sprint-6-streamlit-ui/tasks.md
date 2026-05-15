# Tasks: Sprint 6 - Streamlit UI

## Phase 1: Foundation

- [x] 1.1 Verify streamlit is in requirements.txt (add if missing)
- [x] 1.2 Create `.streamlit/config.toml` with dark theme configuration
- [x] 1.3 Create `src/ui/__init__.py` with module exports
- [x] 1.4 Create `src/ui/app.py` with basic Streamlit setup and imports

## Phase 2: Core Implementation

### 2.1 Theme and Styling
- [x] 2.1.1 Configure base dark theme in config.toml
- [x] 2.1.2 Add custom CSS for steel blue (#4682B4) accents
- [ ] 2.1.3 Apply custom font (optional: clean sans-serif)

### 2.2 Session State Management
- [x] 2.2.1 Initialize orchestrator in session_state on first run
- [x] 2.2.2 Create helper function to get orchestrator from state
- [x] 2.2.3 Implement query history in session_state

### 2.3 Sidebar Metrics
- [x] 2.3.1 Create `src/ui/components/sidebar.py` with metrics display (integrated in app.py)
- [x] 2.3.2 Implement Ollama status indicator (connected/disconnected)
- [x] 2.3.3 Implement cache stats display (hits, misses, hit_rate)
- [x] 2.3.4 Implement document counts per collection
- [x] 2.3.5 Implement latency benchmarks display (TTFT, p50, p90, p99)

### 2.4 Chat Interface
- [x] 2.4.1 Create `src/ui/components/chat.py` with input component (integrated in app.py)
- [x] 2.4.2 Implement query submission handler
- [x] 2.4.3 Add loading spinner during processing
- [x] 2.4.4 Display response with proper formatting
- [x] 2.4.5 Implement chat history display

### 2.5 Metrics Utilities
- [x] 2.5.1 Create `src/ui/utils/metrics.py` for data retrieval
- [x] 2.5.2 Implement get_ollama_status() function
- [x] 2.5.3 Implement get_cache_stats() function
- [x] 2.5.4 Implement get_document_counts() function
- [x] 2.5.5 Implement get_latency_metrics() function

## Phase 3: Integration

- [x] 3.1 Connect chat input to orchestrator.ask()
- [x] 3.2 Wire sidebar metrics to orchestrator status
- [x] 3.3 Add error handling for failed queries
- [x] 3.4 Add "Reset" button to clear chat history and re-index

## Phase 4: Testing

- [x] 4.1 Test: Streamlit app launches without errors
- [x] 4.2 Test: Dark theme applied correctly
- [x] 4.3 Test: Sidebar shows all metrics
- [x] 4.4 Test: Query sent to orchestrator returns response
- [x] 4.5 Test: Loading spinner appears during processing
- [x] 4.6 Test: Session state persists between page interactions

## Phase 5: Cleanup

- [x] 5.1 Remove debug print statements
- [x] 5.2 Add docstrings to all public functions
- [x] 5.3 Verify all imports work correctly (code review)
- [x] 5.4 Test with `streamlit run src/ui/app.py`