# CLAUDE.md — Conflo Project Context

> This file is auto-read by Claude Code at session start. It contains all architecture decisions, database schema, permission rules, API patterns, and conventions needed to write correct code for the Conflo platform.

## Project Overview

Conflo is a construction project management SaaS platform for mid-market general contractors ($5M-$100M annual revenue). Three portals (GC, Owner, Sub) sharing one database. Monorepo with Python FastAPI backend + TypeScript Next.js frontend.

**Business model:** Unlimited users, project-count-based tiers. $250K contract value = "major" project that counts toward tier limit. Subs and Owners access free.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async (asyncpg), Alembic |
| Frontend | TypeScript, Next.js 14 (App Router), Tailwind CSS, Shadcn/ui |
| Database | PostgreSQL 16 |
| Auth | Clerk (3 user pools: GC, Sub, Owner) |
| Payments | Stripe (Subscriptions, Checkout, Customer Portal) |
| Files | AWS S3 / Cloudflare R2 (pre-signed URLs) |
| Cache | Redis (sessions, rate limiting) |
| Email | Resend (transactional) |
| Search | PostgreSQL full-text (GIN indexes) |
| Monitoring | Sentry + Datadog/Axiom |
| CI/CD | GitHub Actions |
| Monorepo | Turborepo |

---

## Monorepo Structure

```
conflo/
├── apps/
│   ├── api/                        # Python FastAPI
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py           # pydantic-settings
│   │   │   ├── database.py         # async engine + session
│   │   │   ├── dependencies.py     # get_db, get_current_user
│   │   │   ├── models/             # SQLAlchemy ORM (1 file per entity)
│   │   │   ├── schemas/            # Pydantic request/response
│   │   │   ├── routers/            # API route handlers
│   │   │   ├── services/           # Business logic
│   │   │   │   ├── permission_engine.py
│   │   │   │   ├── phase_machine.py
│   │   │   │   ├── billing_service.py
│   │   │   │   ├── notification_service.py
│   │   │   │   ├── numbering_service.py
│   │   │   │   ├── file_service.py
│   │   │   │   ├── event_service.py
│   │   │   │   └── email_service.py
│   │   │   ├── integrations/       # QuickBooks, Bluebeam, etc.
│   │   │   └── middleware/         # auth, portal, rate limiter
│   │   ├── alembic/
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── web/                        # Next.js 14
│       ├── src/
│       │   ├── app/
│       │   │   ├── (auth)/         # login, signup, invite, onboarding
│       │   │   ├── (gc)/           # GC Portal /app/*
│       │   │   ├── (owner)/        # Owner Portal /owner/*
│       │   │   └── (sub)/          # Sub Portal /sub/*
│       │   ├── components/
│       │   │   ├── ui/             # Shadcn primitives
│       │   │   ├── shared/         # Cross-portal (DataTable, CommentThread, etc.)
│       │   │   ├── gc/             # GC-specific (GCPortalShell, etc.)
│       │   │   ├── owner/          # Owner-specific
│       │   │   └── sub/            # Sub-specific
│       │   ├── hooks/              # Per-tool data hooks
│       │   ├── lib/                # API client, utils
│       │   ├── stores/             # Zustand
│       │   └── types/
│       └── tailwind.config.ts
├── packages/shared/                # Shared TS types, enums, validation
├── turbo.json
├── docker-compose.yml              # postgres:16, redis:7
└── .github/workflows/
```

---

## Database Schema

All tables use UUID primary keys (`server_default=text('gen_random_uuid()')`). All timestamps UTC. Soft deletes via `deleted_at` on user-facing tables. Multi-tenant via `organization_id`.

### Core Entities

**organizations**
- id UUID PK, name, logo_url, address fields, phone, license_numbers JSONB, timezone VARCHAR(50) default 'America/Denver'
- stripe_customer_id UNIQUE, subscription_tier (STARTER|PROFESSIONAL|SCALE|ENTERPRISE), subscription_status (ACTIVE|PAST_DUE|CANCELLED|TRIALING), stripe_subscription_id
- contract_start_date, contract_end_date, created_at, updated_at

**users** (GC team members)
- id UUID PK, organization_id FK, clerk_user_id UNIQUE, email, name, phone, title, avatar_url
- permission_level: OWNER_ADMIN | PRE_CONSTRUCTION | MANAGEMENT | USER
- status: ACTIVE | INACTIVE | INVITED
- notification_preferences JSONB, timezone, last_active_at, created_at, updated_at, deleted_at

**projects**
- id UUID PK, organization_id FK, name, project_number, address, latitude, longitude, timezone
- project_type: COMMERCIAL | INSTITUTIONAL | HEALTHCARE | EDUCATION | INDUSTRIAL | RESIDENTIAL_MULTI | MIXED_USE | OTHER
- contract_value DECIMAL(15,2), **is_major BOOLEAN GENERATED ALWAYS AS (contract_value >= 250000) STORED**
- phase: BIDDING | BUYOUT | ACTIVE | CLOSEOUT | CLOSED
- estimated/actual start/end dates, owner_client_name/company, ae_name/company
- cost_code_template_id FK, bid_due_date, created_by_user_id FK, created_at, updated_at, deleted_at

**project_assignments** (CENTRAL ACCESS CONTROL TABLE)
- id UUID PK, project_id FK, assignee_type (GC_USER|SUB_COMPANY|OWNER_ACCOUNT), assignee_id UUID (polymorphic)
- financial_access BOOLEAN default false (USER level: grants budget/CO/pay app)
- bidding_access BOOLEAN default false (USER level: grants bid tool access)
- trade VARCHAR (for subs), contract_value DECIMAL (for subs)
- assigned_by_user_id FK, assigned_at
- **UNIQUE(project_id, assignee_type, assignee_id)**

**contacts** (GC's external directory)
- id UUID PK, organization_id FK, company_name, contact_name, email (MATCHING KEY for portal linking), phone
- category: SUBCONTRACTOR | OWNER_CLIENT | ARCHITECT_ENGINEER | VENDOR | OTHER
- trade, address, notes
- linked_sub_company_id FK nullable (auto-linked on invite acceptance)
- linked_owner_account_id FK nullable (auto-linked on invite acceptance)
- status (ACTIVE|INACTIVE), created_at

**sub_companies** (Sub Portal identity, persists across GCs)
- id UUID PK, name, address, phone, website, primary_contact_user_id FK
- trades JSONB [], certifications JSONB [], insurance_coi_url, insurance_expiry_date
- bonding_single_limit, bonding_aggregate_limit DECIMAL, license_numbers JSONB, service_area

**sub_users**
- id UUID PK, sub_company_id FK, clerk_user_id UNIQUE, email, name, phone, title
- is_primary BOOLEAN (primary manages company profile), status

**owner_accounts** - id, name, created_at
**owner_users** - id, owner_account_id FK, clerk_user_id UNIQUE, email, name, phone, title, status

**owner_portal_config** (per-project visibility toggles)
- project_id FK UNIQUE
- show_schedule, show_submittals, show_rfis, show_transmittals, show_drawings, show_punch_list (all BOOLEAN default true)
- show_budget_summary, show_daily_logs (default false)
- allow_punch_creation (default false)
- Pay Apps + Change Orders are ALWAYS visible (not toggleable)

### Tool Tables

All tool tables have: id UUID PK, organization_id FK, project_id FK, created_by (user ref), created_at, updated_at.

| Table | Number Format | Status Flow | Key Special Fields |
|-------|--------------|-------------|-------------------|
| daily_logs | Date-based (1/project/day) | DRAFT→SUBMITTED | weather_data JSONB, manpower JSONB [], work_performed TEXT, delays JSONB [] |
| rfis | RFI-{NNN} | DRAFT→OPEN→RESPONDED→CLOSED | subject, question TEXT, assigned_to, priority, cost_impact, schedule_impact, due_date |
| submittals | {NNN}.{RR} | DRAFT→SUBMITTED→UNDER_REVIEW→APPROVED\|APPROVED_AS_NOTED\|REVISE_AND_RESUBMIT\|REJECTED | spec_section, submittal_type, reviewer, submitted_by_sub_id |
| transmittals | TR-{NNN} | SENT→ACKNOWLEDGED | to_contact_ids JSONB, action_required |
| change_orders | PCO-{NNN}/CO-{NNN} | DRAFT→PENDING_SUB_PRICING→SUB_PRICING_RECEIVED→PENDING_OWNER→APPROVED\|REJECTED\|REVISION | reason, cost_breakdown JSONB, schedule_impact_days, related_rfi_ids |
| punch_list_items | PL-{NNN} | OPEN→IN_PROGRESS→COMPLETED_BY_SUB→VERIFIED_BY_GC→CLOSED | location, trade, assigned_sub_company_id, priority, before/after_photo_ids |
| inspections | INSP-{NNN} | SCHEDULED→IN_PROGRESS→COMPLETED\|FAILED | template_id, form_data JSONB, inspector_user_id |
| pay_apps | #{N} | DRAFT→SUBMITTED→UNDER_REVIEW→APPROVED\|REJECTED\|REVISION | period_start/end, sov_data JSONB (G702/G703), retention_rate, submitted_by_type |
| bid_packages | BP-{NNN} | DRAFT→PUBLISHED→CLOSED→AWARDED | trades JSONB, bid_due_date, invited_sub_ids JSONB |
| schedule_tasks | N/A | N/A | name, start/end dates, duration, predecessors JSONB, assigned_to, percent_complete |
| drawings + drawing_sheets | User-defined | N/A | set_id, sheet_number, discipline, revision, is_current_set |
| meetings | MTG-{NNN} | SCHEDULED→COMPLETED | attendees JSONB, agenda, minutes, action_items JSONB |
| todos | N/A | TODO→IN_PROGRESS→DONE | assigned_to, due_date, priority |
| procurement_items | N/A | IDENTIFIED→QUOTED→ORDERED→SHIPPED→DELIVERED→INSTALLED | vendor, po_number, cost_code, dates JSONB |
| documents | N/A | N/A | category, file_url, version, uploaded_by |

### Supporting Tables

- **comments** — Polymorphic threads: commentable_type, commentable_id, author_type (GC_USER|SUB_USER|OWNER_USER), author_id, body, is_official_response, attachment_ids JSONB, mentioned_user_ids JSONB
- **files** — org_id, project_id, s3_key, filename, mime_type, size_bytes, uploaded_by
- **photos** — file_id FK, latitude, longitude, captured_at, device_info, linked_type, linked_id
- **notifications** — user_type, user_id, type, title, body, source_type, source_id, read_at
- **event_logs** — org_id, project_id, user_type, user_id, event_type, event_data JSONB
- **audit_logs** — org_id, actor_id, action, resource_type, resource_id, before/after JSONB
- **cost_code_templates** — org_id, name, codes JSONB, is_default
- **inspection_templates** — org_id, name, fields JSONB
- **invitations** — org_id, email, user_type, permission_level, token, status, expires_at
- **integration_connections** — org_id, provider, access_token_enc, refresh_token_enc, config JSONB, status
- **budget_line_items** — project_id, cost_code, description, original, approved_changes, committed, actuals, projected
- **bid_submissions** — bid_package_id, sub_company_id, total_amount, line_items JSONB, qualifications, submitted_at

### Key Indexes
```sql
CREATE INDEX idx_users_org ON users(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_org_phase ON projects(organization_id, phase) WHERE deleted_at IS NULL;
CREATE INDEX idx_assignments_project ON project_assignments(project_id, assignee_type);
CREATE INDEX idx_assignments_assignee ON project_assignments(assignee_type, assignee_id);
CREATE INDEX idx_comments_parent ON comments(commentable_type, commentable_id, created_at);
-- Full-text search
CREATE INDEX idx_rfis_fts ON rfis USING GIN(to_tsvector('english', subject || ' ' || question));
-- Unique numbering per project per tool
CREATE UNIQUE INDEX idx_rfis_num ON rfis(project_id, number);
```

---

## Authentication

Clerk handles auth (login/signup/sessions). Our backend handles authorization.

**Three user pools:**
- GC Users → `users` table → `/app/*` portal
- Sub Users → `sub_users` table → `/sub/*` portal
- Owner Users → `owner_users` table → `/owner/*` portal

**Auth middleware flow:**
1. Extract Clerk token from `Authorization: Bearer` header
2. Verify with Clerk → get clerk_user_id + metadata.user_type
3. Lookup internal user record (users / sub_users / owner_users)
4. Attach to `request.state.user = { user_type, user_id, organization_id|sub_company_id|owner_account_id, permission_level }`
5. Portal middleware: `/api/gc/*` → gc only, `/api/sub/*` → sub only, `/api/owner/*` → owner only

**Invite flow:**
- POST /api/auth/invitations → create record + send email
- GET /invite/:token → decode, show signup form
- POST /api/auth/invitations/:token/accept → create Clerk user + sync to DB + create project_assignment
- Email matching: if email matches existing SubCompany/OwnerAccount → auto-link

---

## Permission Engine

Three dimensions: **user_type** (GC/Sub/Owner) × **permission_level** (for GC) × **project_assignment** (with conditional access flags).

### Permission Check Algorithm
```python
async def check_permission(user, project_id, tool, action, db):
    # 1. Assignment check (Owner/Admin exempt - sees all)
    assignment = await get_assignment(project_id, user.type, user.id)
    if not assignment and user.permission_level != 'OWNER_ADMIN':
        raise 403
    # 2. Phase check
    if PHASE_TOOL_MAP[project.phase][tool] == 'hidden': raise 403
    if PHASE_TOOL_MAP[project.phase][tool] == 'read_only' and action != 'read': raise 403
    # 3. Permission matrix
    allowed = MATRIX[user.type][user.permission_level][tool][action]
    # 4. Conditional access for USER level
    if not allowed and user.permission_level == 'USER':
        if tool in FINANCIAL_TOOLS and assignment.financial_access: allowed = True
        if tool in BIDDING_TOOLS and assignment.bidding_access: allowed = True
    if not allowed: raise 403
```

### GC Permission Matrix (C=Create R=Read U=Update D=Delete V=Verify)

| Tool | Owner/Admin | Pre-Con | Management | User |
|------|------------|---------|------------|------|
| Daily Logs | CRUD all | N/A | CRU own, R all | CRU own, R all |
| RFIs | CRUD all | N/A | CRUD assigned | CR, respond |
| Submittals | CRUD all | N/A | CRUD, review | CR, submit |
| Transmittals | CRUD all | N/A | CR, send | CR, send |
| Change Orders | CRUD, approve | N/A | CRUD, negotiate | View (CRUD if financial_access) |
| Schedule | CRUD all | N/A | CRUD | R, update % |
| Drawings | CRUD, set current | N/A | Upload, version | R, download |
| Punch List | CRUD, verify | N/A | CRU, verify | CR, photo (no verify) |
| Inspections | CRUD, templates | N/A | CR, conduct | CR, conduct |
| Budget | CRUD all | N/A | CRUD | R if financial_access |
| Pay Apps | CRUD, approve | N/A | CRUD | R if financial_access |
| Meetings | CRUD all | N/A | CRUD | CRUD |
| To-Do | CRUD all | N/A | CRUD | CRUD |
| Procurement | CRUD all | N/A | CRUD | CRUD |
| Look Ahead | CRUD all | N/A | CRUD | CRUD |
| Closeout | CRUD all | N/A | CRUD, assemble | Contribute |
| Bid Packages | CRUD all | CRUD | View only | View if bidding_access |
| Directory | CRUD all | R, add | CRUD | R, add |

### Phase-Based Tool Availability

| Tool Group | BIDDING | BUYOUT | ACTIVE | CLOSEOUT | CLOSED |
|-----------|---------|--------|--------|----------|--------|
| Bid tools | Active | Read-only | Read-only | Read-only | Read-only |
| Buyout tools | Hidden | Active | Read-only | Read-only | Read-only |
| Field Ops | Hidden | Active | Active | Active | Read-only |
| Communications | Limited | Active | Active | Active | Read-only |
| Planning | Hidden | Active | Active | Active | Read-only |
| Financial | Hidden | Active | Active | Active | Read-only |
| Docs/Drawings | Active | Active | Active | Active | Read-only |
| Closeout | Hidden | Hidden | Hidden | Active | Read-only |

CLOSED = terminal, all read-only, no new records, removed from tier count.

### Sub Portal Permissions
- RFIs: view assigned, create new, respond
- Submittals: submit, track status
- Change Orders: receive pricing requests, submit pricing, negotiate
- Punch List: view assigned, mark complete with photos (cannot create/verify)
- Pay Apps: create G702/G703, submit to GC, track
- Schedule: view own scope only, read-only
- Drawings: view/download relevant sheets
- Transmittals: receive, acknowledge (cannot create)
- To-Do: CRUD
- Closeout: submit docs against checklist
- Bids: view packages, submit pricing, pre-bid RFIs

### Owner Portal Permissions
- Pay Apps: review, approve, reject, revision — **ALWAYS visible**
- Change Orders: review, approve, reject, revision — **ALWAYS visible**
- Schedule: view only — GC toggle
- Punch List: view; create IF GC enables — GC toggle
- Submittals: view, respond if routed — GC toggle
- RFIs: view, respond if assigned — GC toggle
- Drawings: view, download — GC toggle
- Closeout: receive package — always visible
- Directory: view GC team — always visible

---

## Phase State Machine

```
BIDDING → BUYOUT → ACTIVE → CLOSEOUT → CLOSED
```
- **Forward-only.** No backward transitions. CLOSED is terminal.
- **Skip paths:** Project can be CREATED in any phase.
- **Who triggers:** Owner/Admin + Management. BIDDING→BUYOUT also by Owner/Client.

### Transition Side Effects
- **BIDDING→BUYOUT:** PreCon tools read-only, bid data preserved, assign Management, buyout tools unlock, notify awarded subs
- **BUYOUT→ACTIVE:** Buyout tools read-only, all 16 tools activate, User team assignable
- **ACTIVE→CLOSEOUT:** Closeout checklist prominent, notify subs for docs, other tools stay active
- **CLOSEOUT→CLOSED:** ALL read-only, archived, **removed from tier count**, notify all

---

## API Design

RESTful JSON. All endpoints: `/api/{gc|owner|sub}/*`. Auth routes: `/api/auth/*`. Webhooks: `/api/webhooks/*`.

### Standard Tool Pattern
```
GET    /api/gc/projects/:projectId/{tool}           # List (paginated)
POST   /api/gc/projects/:projectId/{tool}           # Create
GET    /api/gc/projects/:projectId/{tool}/:id       # Detail
PATCH  /api/gc/projects/:projectId/{tool}/:id       # Update
DELETE /api/gc/projects/:projectId/{tool}/:id       # Soft delete
POST   /api/gc/projects/:projectId/{tool}/:id/{action}  # Status transition
GET    /api/gc/projects/:projectId/{tool}/:id/comments   # Thread
POST   /api/gc/projects/:projectId/{tool}/:id/comments   # Add comment
```

### Query Params (all list endpoints)
`?page=1&per_page=25&sort=created_at&order=desc&status=OPEN&search=keyword`

### Response Format
```json
// Single: { "data": { "id": "uuid", ...fields }, "meta": {} }
// List:   { "data": [...], "meta": { "page": 1, "per_page": 25, "total": 150, "total_pages": 6 } }
// Error:  { "error": { "code": "PERMISSION_DENIED", "message": "..." } }
```

### Key Non-CRUD Endpoints
- `POST /api/gc/projects/:id/transition { target_phase }` — Phase change
- `POST /api/gc/projects/:id/change-orders/:id/request-sub-pricing` — CO workflow
- `POST /api/gc/projects/:id/change-orders/:id/submit-to-owner` — CO workflow
- `POST /api/gc/projects/:id/bid-packages/:id/distribute` — Send to subs
- `POST /api/gc/projects/:id/bid-packages/:id/award` — Award bid
- `POST /api/gc/files/upload-url` — Pre-signed S3 upload URL
- `POST /api/gc/files/confirm` — Confirm upload, create file record
- `POST /api/gc/billing/portal-session` — Stripe Customer Portal redirect
- `POST /api/owner/projects/:id/award` — Owner awards project (triggers BIDDING→BUYOUT)
- `POST /api/owner/projects/:id/pay-apps/:id/{approve|reject|revision}`
- `POST /api/sub/bids/:id/submit` — Submit bid
- `POST /api/sub/projects/:id/change-orders/:id/submit-pricing`

---

## Stripe Billing

| Tier | Monthly | Annual | Major Project Limit | Contract |
|------|---------|--------|-------------------|----------|
| Starter | $349 | N/A | 3 | Month-to-month |
| Professional | $2,500 | $27,500 (8% off) | 10 | 12-month |
| Scale | $4,500 | $49,500 (8% off) | 25 | 12-month |
| Enterprise | Custom | Custom | Unlimited | Custom |

**Tier enforcement:** Count major projects (is_major=true AND phase NOT CLOSED). Block new major project creation at limit. Prompt upgrade.

**Threshold crossing:** Changing contract_value across $250K rechecks tier limit.

**Webhooks:** checkout.session.completed, invoice.payment_succeeded, invoice.payment_failed (→ 7-day grace), customer.subscription.updated, customer.subscription.deleted.

---

## Numbering Service

Per-project, auto-increment, immutable. Never reuse deleted numbers. Atomic via SELECT MAX + FOR UPDATE.

| Tool | Format | Example |
|------|--------|---------|
| RFIs | RFI-{NNN} | RFI-001, RFI-042 |
| Submittals | {NNN}.{RR} | 001.00, 001.01 |
| Transmittals | TR-{NNN} | TR-001 |
| Change Orders | PCO-{NNN} / CO-{NNN} | PCO-001 → CO-001 |
| Punch List | PL-{NNN} | PL-001 |
| Inspections | INSP-{NNN} | INSP-001 |
| Bid Packages | BP-{NNN} | BP-001 |
| Meetings | MTG-{NNN} | MTG-001 |
| Pay Apps | #{N} | #1, #2, #3 |
| Daily Logs | By date | 2026-03-15 (unique per project per date) |

---

## File Storage

S3/R2 with pre-signed URLs. No file data through API server.

**Upload:** POST /files/upload-url → pre-signed PUT (5min) → client uploads to S3 → POST /files/confirm → create file record + extract photo EXIF.

**Download:** GET /files/:id/download-url → pre-signed GET (1hr), permission-checked.

**Bucket:** `conflo-files/{org_id}/{project_id}/{category}/{uuid}.{ext}`
**Sub files:** `conflo-sub-files/{sub_company_id}/...`

---

## Frontend Architecture

### Portal Shells

**GC Portal:** Top bar (logo, project switcher, search, notifications, avatar menu) + collapsible sidebar (240px/64px) + project context sidebar (tool groups) + breadcrumbs + content area.

**Owner Portal:** Top bar + horizontal tool tab bar (no sidebar). Tabs only for GC-visible tools. Card-based, zero training.

**Sub Portal:** Top bar (project switcher grouped by GC) + sidebar (Dashboard, Projects, Bids, Financials, Company, Help) + project context sidebar.

**Mobile (768px):** Hamburger menu + bottom tab bar. GC: Daily Log, RFIs, Punch, Camera, More.

### State Management
- Server Components for initial loads
- TanStack Query for interactive data (useQuery/useMutation per tool)
- Zustand for UI state (sidebar collapsed, filters)
- Context Providers for project/user scope

### Shared Components (src/components/shared/)
DataTable, CommentThread, StatusBadge, PhaseBadge, EmptyState, FileUpload, PhotoGallery, ConfirmDialog, Toast, RichTextEditor, NumberBadge, DatePicker, UserAvatar, SearchInput, WeatherWidget

### Tool Page Pattern
Every tool follows: ListPage (PageHeader + FilterBar + DataTable + EmptyState) and DetailPage (DetailHeader + fields + CommentThread + StatusActions).

---

## Notification Triggers

| Group | Events |
|-------|--------|
| Pre-Construction | new_sub_bid, bid_deadline_approaching, all_bids_received, pre_bid_rfi, project_awarded |
| Management | project_assigned, sub_pay_app_submitted, owner_pay_app_decision, rfi_response, rfi_deadline, submittal_decision, co_decision, sub_co_pricing, milestone_approaching, budget_threshold |
| User | assigned_to_project, punch_assigned, rfi_assigned, daily_log_reminder, inspection_scheduled, todo_assigned |
| Owner/Admin | bid_recommendation, tier_limit, invite_response, payment_failed |
| Sub Portal | invited_to_bid, bid_result, invited_to_project, punch_assigned, pay_app_decision, co_pricing_requested, closeout_requested |
| Owner/Client | pay_app_ready, co_submitted, closeout_delivered, schedule_updated |

---

## Key Conventions

1. **All API routes require authentication** except /api/auth/signup and /api/webhooks/*
2. **Every mutation logs to event_logs** (non-blocking) for data capture
3. **Every destructive action logs to audit_logs** with before/after values
4. **Permission check on every endpoint** via FastAPI dependency: `Depends(require_permission(tool, action))`
5. **Soft deletes everywhere** — never hard delete user-facing data
6. **Organization scoping** — every query filters by organization_id
7. **UTC timestamps** in database, project timezone for display, user timezone for notifications
8. **Brand colors:** Primary #1B2A4A, Accent #2E75B6
9. **No standalone messaging** — all communication is contextual (threads on tools)
10. **Email is the matching key** for linking contacts to Sub/Owner portal accounts

---

## Standard Trade List (25 trades, CSI-mapped)

General Conditions, Demolition, Earthwork, Paving, Landscaping, Utilities, Concrete, Masonry, Metals, Carpentry, Thermal/Moisture Protection, Doors/Windows, Finishes, Specialties, Equipment, Furnishings, Special Construction, Conveying Systems, Fire Protection, Plumbing, HVAC, Electrical, Low Voltage, Electronic Safety/Security, Other.
