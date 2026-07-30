# Goals - Apex Home Services

## Project Goals

### Phase 1: Foundation
- [x] Initialize Git repository with proper configuration
- [x] Set up Python virtual environment with required dependencies
- [x] Create memory-bank system for persistent context
- [ ] Complete Docker Compose setup for commercial mirrors (Invoice Ninja, n8n)
- [ ] Build and test core FastAPI application

### Phase 2: Core Features
- [ ] Implement SQLite database with Lead, Invoice, CallLog models
- [ ] Connect local LLM engine (Qwen via OpenAI-compatible endpoint)
- [ ] Build Invoice Ninja API client with fallback mode
- [ ] Implement calendar service for booking

### Phase 3: Integrations
- [ ] Create Vapi.ai webhook handler for voice call webhooks
- [ ] Build SMS/messaging webhook router
- [ ] Implement invoice parsing endpoint
- [ ] Create dashboard stats endpoint

### Phase 4: UI & Dashboard
- [ ] Build single-page web dashboard with 4 tabs
- [ ] Implement interactive simulator (voice, SMS, invoice)
- [ ] Create lead & dispatch board
- [ ] Build invoice & revenue tracker
- [ ] Add integration health status indicators

### Phase 5: Deployment & Testing
- [ ] Create executable run.sh startup script
- [ ] Verify all endpoints via curl/tests
- [ ] Document setup in README.md
- [ ] Initial production-ready Git commit

---
*Last updated: 2026-07-30 - Project initialization complete*