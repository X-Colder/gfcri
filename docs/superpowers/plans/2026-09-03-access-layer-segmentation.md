# Access Layer Segmentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make anonymous, free, personal-paid, and institutional users receive distinct data capabilities without exposing product-mode labels on the base data experience.

**Architecture:** Keep the public dashboard as a shared data surface, but make the backend authoritative through a small entitlement contract. The frontend consumes the returned capabilities and uses them for navigation, paywalls, and contextual labels. Institutional access is derived from an active institutional account or membership; organization billing remains a separate follow-up because the current system has institutional lead capture rather than an organization checkout flow.

**Tech Stack:** FastAPI, PostgreSQL session/auth tables, Vue 3, Pinia, TypeScript, pytest/unittest, Vite.

## Global Constraints

- Anonymous and free users must receive only the base risk data contract.
- Frontend hiding is not an authorization boundary; premium fields must be redacted server-side.
- Existing public endpoint paths remain compatible.
- Existing uncommitted OIDC and institutional-auth work must not be reverted or included in unrelated commits.
- Database changes, if needed, must be idempotent and preserve existing institutional memberships.

---

### Task 1: Define the entitlement contract

**Files:**
- Create: `src/security/entitlements.py`
- Modify: `api/routers/auth.py`
- Test: `tests/test_entitlements.py`

**Interfaces:**
- Produces `build_entitlements(user) -> dict`.
- Produces `has_entitlement(user, key) -> bool`.
- Auth payload includes `entitlements`, `institutional_access`, and `institutional_memberships`.

- [ ] Write tests covering free, trial, personal pro, institutional account, and institutional membership.
- [ ] Run `pytest tests/test_entitlements.py -q` and verify the tests fail because the helper is missing.
- [ ] Implement the entitlement constants and deterministic builder.
- [ ] Add institutional membership metadata to the session payload without changing session tokens.
- [ ] Include capability fields in `/api/auth/register`, `/api/auth/login`, and `/api/auth/me`.
- [ ] Run `pytest tests/test_entitlements.py -q`.

### Task 2: Enforce the base-versus-premium data boundary

**Files:**
- Create: `src/security/data_visibility.py`
- Modify: `api/routers/risk_index.py`
- Modify: `api/routers/core_themes.py`
- Test: `tests/test_data_visibility.py`

**Interfaces:**
- Produces `visible_risk_index(data, user) -> dict`.
- Base users retain index date, GFCRI value, alert level, and sub-index scores.
- Premium users retain full chain, node, divergence, and spillover details.

- [ ] Write tests proving anonymous/free responses omit node contributions, active chains, divergence, and detailed spillover links.
- [ ] Run the focused test and verify the expected failure.
- [ ] Implement redaction at the API response boundary.
- [ ] Apply the same visibility decision to latest and history endpoints.
- [ ] Prevent unauthenticated causal expansion from returning premium causal details.
- [ ] Run the focused tests and existing API tests.

### Task 3: Make frontend auth state and navigation entitlement-driven

**Files:**
- Modify: `frontend/src/composables/useAuth.ts`
- Modify: `frontend/src/components/layout/NavSidebar.vue`
- Modify: `frontend/src/composables/useProductMode.ts`
- Modify: `frontend/src/views/DashboardView.vue`
- Modify: `frontend/src/views/AnalysisView.vue`
- Modify: `frontend/src/components/common/Paywall.vue`

- [ ] Hydrate opaque `gfcri_sess_*` tokens through `/api/auth/me` instead of parsing them as JWTs.
- [ ] Expose `hasEntitlement` and `isInstitutionalAccess` computed state.
- [ ] Remove public-facing global/personal/institutional labels from the base data surface.
- [ ] Show plan labels only in the authenticated account context; show institutional context only inside the institutional workspace.
- [ ] Keep pricing and institutional lead routes as the explicit commercial entry points.
- [ ] Ensure free users see a generic upgrade/trial paywall and institutional users see institutional access messaging only when relevant.
- [ ] Run the frontend type check and production build.

### Task 4: Close premium route authorization gaps

**Files:**
- Create: `api/access.py`
- Modify: `api/routers/reports.py`
- Modify: `api/routers/inference.py`
- Modify: `api/routers/stress_test.py`
- Modify: `api/routers/causal_discovery.py`
- Test: `tests/test_access_dependencies.py`

- [ ] Add reusable `require_entitlement` dependencies for deep analysis and institutional access.
- [ ] Write tests for anonymous, free, personal pro, and institutional requests.
- [ ] Add server-side authorization to premium report, inference, stress-test, and causal-discovery routes.
- [ ] Keep public base routes unauthenticated.
- [ ] Run focused backend tests and confirm 401/403 payloads are structured.

### Task 5: Release verification and deployment

**Files:**
- Modify: `docs/personal-commercial-ops-checklist.md`
- Test: existing backend and frontend test suites

- [ ] Run backend tests, frontend build, and `git diff --check`.
- [ ] Build the API/frontend images without touching PostgreSQL volumes.
- [ ] Verify anonymous base response, free account response, personal trial/pro response, and institutional response.
- [ ] Verify direct API access cannot retrieve premium fields without entitlement.
- [ ] Deploy only required services with rollback to the previous release.
- [ ] Re-run public health, risk, history, and frontend smoke checks.
