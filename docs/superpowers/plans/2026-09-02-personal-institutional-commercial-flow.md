# Personal and Institutional Commercial Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make GFCRI's personal and institutional products visibly distinct, give each audience a complete entry path, and deploy the verified changes to production.

**Architecture:** Keep personal billing on the existing Stripe checkout path. Add a small institutional lead-capture path backed by PostgreSQL instead of pretending institutional plans are self-serve subscriptions. Derive institutional access from the authenticated account on the server; use the frontend only to present the appropriate public sales or workspace view.

**Tech Stack:** FastAPI, PostgreSQL, Vue 3, TypeScript, Vue Router, Docker Compose, Python `unittest`.

## Global Constraints

- Preserve the existing personal prices: `$19/month` and `$149/year`.
- Institutional checkout must not be represented as a working Stripe subscription until institutional billing exists.
- Institutional API access must require an authenticated institutional account.
- Do not remove or recreate the production PostgreSQL volume.
- Preserve the deployment-specific Dockerfile and Compose changes already present in the worktree.
- Personal users must see a usable sales/lead path for institutions, not a dead-end permission error.

---

### Task 1: Define Failing Backend Tests

**Files:**
- Create: `tests/test_commercial_flow.py`
- Test: `api/routers/billing.py`, `api/routers/auth.py`, `api/routers/institutional_radar.py`

**Interfaces:**
- `InstitutionalLeadRequest` validates company, work email, and use case.
- `require_institutional_user()` rejects missing or personal users and accepts institutional users.
- `billing_catalog()` reports whether personal Stripe checkout is configured without exposing secrets.

- [ ] **Step 1: Write the failing tests**

```python
import unittest

from api.routers.auth import require_institutional_user
from api.routers.billing import InstitutionalLeadRequest, billing_catalog


class CommercialFlowTests(unittest.TestCase):
    def test_institutional_lead_requires_company_work_email_and_use_case(self):
        request = InstitutionalLeadRequest(
            company_name="Northstar Capital",
            work_email="risk@northstar.example",
            full_name="Ava Chen",
            role="Portfolio Risk",
            team_size="3-10",
            use_case="Weekly investment committee macro-risk review",
            deployment="Hosted",
            language="en",
        )
        self.assertEqual(request.company_name, "Northstar Capital")

        with self.assertRaises(ValueError):
            InstitutionalLeadRequest(
                company_name="",
                work_email="not-an-email",
                use_case="",
            )

    def test_institutional_guard_requires_institutional_account(self):
        with self.assertRaises(Exception) as personal_error:
            require_institutional_user({"account_type": "personal"})
        self.assertEqual(getattr(personal_error.exception, "status_code", None), 403)

        self.assertEqual(
            require_institutional_user({"account_type": "institutional"}),
            {"account_type": "institutional"},
        )

    def test_billing_catalog_has_public_plan_metadata_without_secret_values(self):
        catalog = billing_catalog()
        self.assertIn("personal", catalog)
        self.assertIn("institutional", catalog)
        self.assertIn("monthly", catalog["personal"])
        self.assertIn("pilot", catalog["institutional"])
        self.assertNotIn("stripe_secret_key", str(catalog).lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_commercial_flow -v`

Expected: FAIL because the lead model, institutional guard, and public catalog do not exist yet.

### Task 2: Implement Backend Commercial Flow

**Files:**
- Modify: `api/routers/auth.py`
- Modify: `api/routers/billing.py`
- Modify: `api/routers/institutional_radar.py`
- Modify: `api/main.py` only if a new router is introduced

**Interfaces:**
- `require_institutional_user(user=None) -> dict` returns the authenticated institutional payload or raises `401/403`.
- `GET /api/billing/catalog` returns public plan metadata and boolean checkout availability.
- `POST /api/billing/institutional-leads` stores a validated lead and returns `{status, lead_id}`.
- `GET /api/institutional-radar/latest` requires institutional access.

- [ ] **Step 1: Add the minimal backend implementation**

Implement the guard in `api/routers/auth.py`:

```python
def require_institutional_user(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if user.get("account_type") != "institutional":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "INSTITUTIONAL_ACCESS_REQUIRED",
                "message": "Institutional account required.",
            },
        )
    return user
```

Add `InstitutionalLeadRequest`, `billing_catalog()`, the lead table in `_ensure_billing_schema()`, and the lead endpoint to `api/routers/billing.py`. Validate string lengths, require an `@` in `work_email`, store status `new`, and never return credentials or raw configuration.

Add `user=Depends(require_institutional_user)` to the institutional radar endpoint. Do not gate public methodology or core-theme endpoints in this task.

- [ ] **Step 2: Run the focused tests**

Run: `python -m unittest tests.test_commercial_flow -v`

Expected: all three tests pass.

### Task 3: Build the Audience-Separated Frontend Entry

**Files:**
- Create: `frontend/src/api/institutionalLead.ts`
- Create: `frontend/src/views/InstitutionalEntryView.vue`
- Modify: `frontend/src/views/PricingView.vue`
- Modify: `frontend/src/views/InstitutionalView.vue` only if workspace-only assumptions require it
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/components/layout/NavSidebar.vue`
- Modify: `frontend/src/composables/useProductMode.ts`
- Modify: `frontend/src/composables/useI18n.ts`

**Interfaces:**
- `submitInstitutionalLead(payload)` posts to `/billing/institutional-leads`.
- `/institutional` renders a public institutional sales page for non-institutional users and the existing workspace for institutional users.
- `/pricing` always exposes personal plans and a separate institutional section.
- Institutional navigation is shown only for institutional accounts, not for a local-storage mode toggle.

- [ ] **Step 1: Add the frontend API client**

```ts
import client from './client'

export interface InstitutionalLeadPayload {
  company_name: string
  work_email: string
  full_name: string
  role: string
  team_size: string
  use_case: string
  deployment: string
  message: string
  language: 'zh' | 'en'
}

export async function submitInstitutionalLead(payload: InstitutionalLeadPayload) {
  const { data } = await client.post('/billing/institutional-leads', payload)
  return data as { status: string; lead_id: number }
}
```

- [ ] **Step 2: Add a failing UI build check**

Run: `npm run build --prefix frontend`

Expected: fail until the new component imports, route, and translation keys are wired correctly.

- [ ] **Step 3: Implement the public institutional entry**

Add `InstitutionalEntryView.vue` that selects `InstitutionalView` only for `isInstitutionalAccount`; otherwise it renders a clear institutional value proposition, the three institutional offer levels, starting prices, and a lead form with success/error states.

Update `PricingView.vue` so personal plans remain `$0`, `$19/month`, and `$149/year`, while institutional offers use `Request a Pilot` / `Contact Sales` instead of personal checkout buttons. Show annual savings explicitly.

Update `NavSidebar.vue` and `useProductMode.ts` so institutional mode is derived from the authenticated account type. Remove the ability for an unauthenticated or personal user to unlock institutional navigation by changing local storage.

Add bilingual copy for:

- `For Individuals`
- `For Teams & Institutions`
- `Request a Pilot`
- `from $3,000 / 30 days`
- `from $1,500/month, billed annually`
- `from $30,000/year + setup`
- lead-form validation, success, and failure messages

- [ ] **Step 4: Run the frontend build**

Run: `npm run build --prefix frontend`

Expected: exit code `0` with the new pricing and institutional entry bundled.

### Task 4: Production Verification and Deployment

**Files:**
- Remote: `/opt/gfcri/current` application files
- Remote: `/opt/gfcri/releases/<new-release>` release directory

- [ ] **Step 1: Run repository checks**

Run:

```powershell
python -m unittest tests.test_commercial_flow -v
git diff --check
npm run build --prefix frontend
```

Expected: all backend tests pass, no whitespace errors, frontend build exits `0`.

- [ ] **Step 2: Upload the verified release**

Create a new release directory under `/opt/gfcri/releases/`, copy the changed backend/frontend files and the deployment Compose/Dockerfile files, preserve `/opt/gfcri/.env`, and atomically update `/opt/gfcri/current`.

- [ ] **Step 3: Rebuild and restart only required services**

Run `sudo docker compose build frontend` and `sudo docker compose up -d --no-build api frontend`. Do not run `down -v`, remove volumes, or restart PostgreSQL unless required by a verified failure.

- [ ] **Step 4: Verify production behavior**

Run:

```bash
sudo docker compose config --quiet
sudo docker compose ps
curl -fsS http://127.0.0.1/api/health
curl -fsS http://127.0.0.1/billing/catalog
curl -fsSI http://127.0.0.1/
```

Also submit one test institutional lead, verify a numeric `lead_id`, and verify a personal token receives `403` from `/api/institutional-radar/latest`.

