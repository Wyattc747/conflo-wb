"""
Seed test data for Conflo development and QA testing.

Run with:
    python -m app.services.seed_test_data

Creates a complete demo environment with:
- 1 organization (Acme Construction Co.)
- 4 GC users (one per permission level)
- 2 sub companies with users
- 1 owner account with user
- 3 projects (ACTIVE, BIDDING, CLOSEOUT)
- Full sample data for the active project (all tool tables)
- Owner portal config, notifications, cost code template

All UUIDs are deterministic (uuid5-based) so the script is idempotent.
"""

import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.database import async_session_factory
from app.models import (
    Organization,
    User,
    Project,
    ProjectAssignment,
    Contact,
    SubCompany,
    SubUser,
    OwnerAccount,
    OwnerUser,
    OwnerPortalConfig,
    DailyLog,
    RFI,
    Submittal,
    Transmittal,
    ChangeOrder,
    PunchListItem,
    Inspection,
    InspectionTemplate,
    PayApp,
    BidPackage,
    BidSubmission,
    ScheduleTask,
    Drawing,
    DrawingSheet,
    Meeting,
    Todo,
    ProcurementItem,
    Document,
    DocumentFolder,
    Notification,
    BudgetLineItem,
    CostCodeTemplate,
)

# ---------------------------------------------------------------------------
# Deterministic UUID helper
# ---------------------------------------------------------------------------

def _id(label: str) -> uuid.UUID:
    """Generate a deterministic UUID from a label for idempotent seeding."""
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"conflo-demo-{label}")


def _dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """Shortcut for timezone-aware UTC datetime."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixed IDs
# ---------------------------------------------------------------------------

# Organization
ORG_ID = _id("org")

# GC Users
ADMIN_ID = _id("user-admin")
PRECON_ID = _id("user-precon")
MGMT_ID = _id("user-mgmt")
FIELD_ID = _id("user-field")

# Sub Companies
SUB1_CO_ID = _id("sub-company-1")
SUB2_CO_ID = _id("sub-company-2")

# Sub Users
SUB1_USER_ID = _id("sub-user-1")
SUB2_USER_ID = _id("sub-user-2")

# Owner
OWNER_ACCT_ID = _id("owner-account")
OWNER_USER_ID = _id("owner-user")

# Projects
PROJ_ACTIVE_ID = _id("project-active")
PROJ_BIDDING_ID = _id("project-bidding")
PROJ_CLOSEOUT_ID = _id("project-closeout")

# Cost Code Template
CCT_ID = _id("cost-code-template")


async def seed():
    async with async_session_factory() as db:
        # ------------------------------------------------------------------
        # Idempotency check
        # ------------------------------------------------------------------
        result = await db.execute(
            select(Organization).where(Organization.name == "Acme Construction Co.")
        )
        if result.scalar_one_or_none():
            print("Demo data already exists. Skipping.")
            return

        # ==================================================================
        # 1. Organization
        # ==================================================================
        org = Organization(
            id=ORG_ID,
            name="Acme Construction Co.",
            phone="(303) 555-0100",
            timezone="America/Denver",
            subscription_tier="PROFESSIONAL",
            subscription_status="ACTIVE",
            stripe_customer_id="cus_demo_acme",
            stripe_subscription_id="sub_demo_acme",
            onboarding_completed=True,
            address_line1="1234 Construction Blvd",
            city="Denver",
            state="CO",
            zip_code="80202",
        )
        db.add(org)

        # ==================================================================
        # 2. GC Users (4 permission levels)
        # ==================================================================
        users = [
            User(
                id=ADMIN_ID,
                organization_id=ORG_ID,
                clerk_user_id="clerk_demo_admin",
                email="admin@demo.conflo.app",
                name="Alex Morgan",
                phone="(303) 555-0101",
                title="President",
                permission_level="OWNER_ADMIN",
                status="ACTIVE",
                timezone="America/Denver",
            ),
            User(
                id=PRECON_ID,
                organization_id=ORG_ID,
                clerk_user_id="clerk_demo_precon",
                email="precon@demo.conflo.app",
                name="Jordan Rivera",
                phone="(303) 555-0102",
                title="Pre-Construction Manager",
                permission_level="PRE_CONSTRUCTION",
                status="ACTIVE",
                timezone="America/Denver",
            ),
            User(
                id=MGMT_ID,
                organization_id=ORG_ID,
                clerk_user_id="clerk_demo_mgmt",
                email="mgmt@demo.conflo.app",
                name="Sam Chen",
                phone="(303) 555-0103",
                title="Project Manager",
                permission_level="MANAGEMENT",
                status="ACTIVE",
                timezone="America/Denver",
            ),
            User(
                id=FIELD_ID,
                organization_id=ORG_ID,
                clerk_user_id="clerk_demo_field",
                email="field@demo.conflo.app",
                name="Taylor Kim",
                phone="(303) 555-0104",
                title="Field Engineer",
                permission_level="USER",
                status="ACTIVE",
                timezone="America/Denver",
            ),
        ]
        db.add_all(users)

        # ==================================================================
        # 3. Sub Companies + Sub Users
        # ==================================================================
        sub1 = SubCompany(
            id=SUB1_CO_ID,
            name="Summit Electric LLC",
            trades=["Electrical"],
            phone="(303) 555-0200",
            address="567 Voltage Ave, Denver, CO 80203",
            service_area="Colorado Front Range",
        )
        sub2 = SubCompany(
            id=SUB2_CO_ID,
            name="Mountain Plumbing Inc.",
            trades=["Plumbing"],
            phone="(303) 555-0300",
            address="890 Pipe Dr, Denver, CO 80204",
            service_area="Denver Metro",
        )
        db.add_all([sub1, sub2])

        sub_user1 = SubUser(
            id=SUB1_USER_ID,
            sub_company_id=SUB1_CO_ID,
            clerk_user_id="clerk_demo_sub",
            email="sub@demo.conflo.app",
            name="Chris Watts",
            phone="(303) 555-0201",
            title="Project Manager",
            is_primary=True,
            status="ACTIVE",
        )
        sub_user2 = SubUser(
            id=SUB2_USER_ID,
            sub_company_id=SUB2_CO_ID,
            clerk_user_id="clerk_demo_sub2",
            email="sub2@demo.conflo.app",
            name="Pat Rivera",
            phone="(303) 555-0301",
            title="Estimator",
            is_primary=True,
            status="ACTIVE",
        )
        db.add_all([sub_user1, sub_user2])

        # ==================================================================
        # 4. Owner Account + Owner User
        # ==================================================================
        owner_acct = OwnerAccount(
            id=OWNER_ACCT_ID,
            name="Downtown Development Partners",
        )
        db.add(owner_acct)

        owner_user = OwnerUser(
            id=OWNER_USER_ID,
            owner_account_id=OWNER_ACCT_ID,
            clerk_user_id="clerk_demo_owner",
            email="owner@demo.conflo.app",
            name="Morgan Lee",
            phone="(303) 555-0400",
            title="Development Director",
            status="ACTIVE",
        )
        db.add(owner_user)

        # ==================================================================
        # 11. Cost Code Template (created before projects so FK works)
        # ==================================================================
        cost_code_template = CostCodeTemplate(
            id=CCT_ID,
            organization_id=ORG_ID,
            name="CSI MasterFormat Standard",
            is_default=True,
            codes=[
                {"code": "01-000", "description": "General Conditions"},
                {"code": "02-000", "description": "Existing Conditions / Demolition"},
                {"code": "03-000", "description": "Concrete"},
                {"code": "04-000", "description": "Masonry"},
                {"code": "05-000", "description": "Metals"},
                {"code": "06-000", "description": "Wood, Plastics, and Composites"},
                {"code": "07-000", "description": "Thermal & Moisture Protection"},
                {"code": "08-000", "description": "Openings (Doors & Windows)"},
                {"code": "09-000", "description": "Finishes"},
                {"code": "10-000", "description": "Specialties"},
                {"code": "11-000", "description": "Equipment"},
                {"code": "12-000", "description": "Furnishings"},
                {"code": "14-000", "description": "Conveying Equipment"},
                {"code": "15-000", "description": "Mechanical (Plumbing)"},
                {"code": "16-000", "description": "Electrical"},
                {"code": "21-000", "description": "Fire Suppression"},
                {"code": "22-000", "description": "Plumbing"},
                {"code": "23-000", "description": "HVAC"},
                {"code": "26-000", "description": "Electrical"},
                {"code": "27-000", "description": "Communications"},
                {"code": "28-000", "description": "Electronic Safety & Security"},
                {"code": "31-000", "description": "Earthwork"},
                {"code": "32-000", "description": "Exterior Improvements"},
                {"code": "33-000", "description": "Utilities"},
            ],
        )
        db.add(cost_code_template)

        # ==================================================================
        # 5. Three Projects
        # ==================================================================
        proj_active = Project(
            id=PROJ_ACTIVE_ID,
            organization_id=ORG_ID,
            name="Downtown Office Tower",
            project_number="2026-001",
            phase="ACTIVE",
            contract_value=Decimal("12500000.00"),
            project_type="COMMERCIAL",
            address="100 Main St",
            city="Denver",
            state="CO",
            zip_code="80202",
            timezone="America/Denver",
            estimated_start_date=_dt(2026, 1, 15),
            estimated_end_date=_dt(2027, 6, 30),
            actual_start_date=_dt(2026, 1, 20),
            owner_client_name="Morgan Lee",
            owner_client_company="Downtown Development Partners",
            ae_name="Lisa Park",
            ae_company="Park & Associates Architects",
            cost_code_template_id=CCT_ID,
            created_by_user_id=ADMIN_ID,
        )
        proj_bidding = Project(
            id=PROJ_BIDDING_ID,
            organization_id=ORG_ID,
            name="Riverside Medical Center",
            project_number="2026-002",
            phase="BIDDING",
            contract_value=Decimal("8750000.00"),
            project_type="HEALTHCARE",
            address="250 River Rd",
            city="Boulder",
            state="CO",
            zip_code="80301",
            timezone="America/Denver",
            estimated_start_date=_dt(2026, 5, 1),
            estimated_end_date=_dt(2027, 12, 31),
            bid_due_date=_dt(2026, 3, 15),
            owner_client_name="Dr. James Hartley",
            owner_client_company="Riverside Health Group",
            ae_name="Michael Torres",
            ae_company="Torres Medical Design",
            cost_code_template_id=CCT_ID,
            created_by_user_id=ADMIN_ID,
        )
        proj_closeout = Project(
            id=PROJ_CLOSEOUT_ID,
            organization_id=ORG_ID,
            name="Mountain View Apartments",
            project_number="2026-003",
            phase="CLOSEOUT",
            contract_value=Decimal("3200000.00"),
            project_type="RESIDENTIAL_MULTI",
            address="500 Mountain View Dr",
            city="Golden",
            state="CO",
            zip_code="80401",
            timezone="America/Denver",
            estimated_start_date=_dt(2025, 3, 1),
            estimated_end_date=_dt(2026, 2, 28),
            actual_start_date=_dt(2025, 3, 10),
            owner_client_name="Sarah Nguyen",
            owner_client_company="Mountain View Properties LLC",
            ae_name="David Kim",
            ae_company="Kim Residential Design",
            cost_code_template_id=CCT_ID,
            created_by_user_id=ADMIN_ID,
        )
        db.add_all([proj_active, proj_bidding, proj_closeout])

        # ==================================================================
        # 6. Project Assignments
        # ==================================================================
        assignments = []

        # All GC users to all 3 projects
        for i, user_id in enumerate([ADMIN_ID, PRECON_ID, MGMT_ID, FIELD_ID]):
            for j, proj_id in enumerate([PROJ_ACTIVE_ID, PROJ_BIDDING_ID, PROJ_CLOSEOUT_ID]):
                assignments.append(
                    ProjectAssignment(
                        id=_id(f"assign-gc-{i}-proj-{j}"),
                        project_id=proj_id,
                        assignee_type="GC_USER",
                        assignee_id=user_id,
                        financial_access=(user_id in [ADMIN_ID, MGMT_ID]),
                        bidding_access=(user_id in [ADMIN_ID, PRECON_ID]),
                        assigned_by_user_id=ADMIN_ID,
                    )
                )

        # Summit Electric -> Downtown Office Tower + Mountain View Apartments
        assignments.append(
            ProjectAssignment(
                id=_id("assign-sub1-proj-active"),
                project_id=PROJ_ACTIVE_ID,
                assignee_type="SUB_COMPANY",
                assignee_id=SUB1_CO_ID,
                trade="Electrical",
                contract_value=Decimal("1850000.00"),
                assigned_by_user_id=ADMIN_ID,
            )
        )
        assignments.append(
            ProjectAssignment(
                id=_id("assign-sub1-proj-closeout"),
                project_id=PROJ_CLOSEOUT_ID,
                assignee_type="SUB_COMPANY",
                assignee_id=SUB1_CO_ID,
                trade="Electrical",
                contract_value=Decimal("420000.00"),
                assigned_by_user_id=ADMIN_ID,
            )
        )

        # Mountain Plumbing -> Downtown Office Tower
        assignments.append(
            ProjectAssignment(
                id=_id("assign-sub2-proj-active"),
                project_id=PROJ_ACTIVE_ID,
                assignee_type="SUB_COMPANY",
                assignee_id=SUB2_CO_ID,
                trade="Plumbing",
                contract_value=Decimal("975000.00"),
                assigned_by_user_id=ADMIN_ID,
            )
        )

        # Owner -> Downtown Office Tower
        assignments.append(
            ProjectAssignment(
                id=_id("assign-owner-proj-active"),
                project_id=PROJ_ACTIVE_ID,
                assignee_type="OWNER_ACCOUNT",
                assignee_id=OWNER_ACCT_ID,
                assigned_by_user_id=ADMIN_ID,
            )
        )

        db.add_all(assignments)

        # ==================================================================
        # 7. Contacts
        # ==================================================================
        contacts = [
            Contact(
                id=_id("contact-1"),
                organization_id=ORG_ID,
                company_name="Summit Electric LLC",
                contact_name="Chris Watts",
                email="sub@demo.conflo.app",
                phone="(303) 555-0201",
                category="SUBCONTRACTOR",
                trade="Electrical",
                linked_sub_company_id=SUB1_CO_ID,
                status="ACTIVE",
            ),
            Contact(
                id=_id("contact-2"),
                organization_id=ORG_ID,
                company_name="Mountain Plumbing Inc.",
                contact_name="Pat Rivera",
                email="sub2@demo.conflo.app",
                phone="(303) 555-0301",
                category="SUBCONTRACTOR",
                trade="Plumbing",
                linked_sub_company_id=SUB2_CO_ID,
                status="ACTIVE",
            ),
            Contact(
                id=_id("contact-3"),
                organization_id=ORG_ID,
                company_name="Downtown Development Partners",
                contact_name="Morgan Lee",
                email="owner@demo.conflo.app",
                phone="(303) 555-0400",
                category="OWNER_CLIENT",
                linked_owner_account_id=OWNER_ACCT_ID,
                status="ACTIVE",
            ),
            Contact(
                id=_id("contact-4"),
                organization_id=ORG_ID,
                company_name="Park & Associates Architects",
                contact_name="Lisa Park",
                email="lpark@parkarchitects.com",
                phone="(303) 555-0500",
                category="ARCHITECT_ENGINEER",
                status="ACTIVE",
            ),
            Contact(
                id=_id("contact-5"),
                organization_id=ORG_ID,
                company_name="Rocky Mountain Concrete",
                contact_name="Mike Johnson",
                email="mjohnson@rmconcrete.com",
                phone="(303) 555-0600",
                category="SUBCONTRACTOR",
                trade="Concrete",
                status="ACTIVE",
            ),
        ]
        db.add_all(contacts)

        # ==================================================================
        # 8. Sample Data for Active Project (Downtown Office Tower)
        # ==================================================================
        P = PROJ_ACTIVE_ID  # shorthand

        # ------------------------------------------------------------------
        # 8a. Daily Logs (3 logs, recent dates)
        # ------------------------------------------------------------------
        today = _dt(2026, 2, 26)
        daily_logs = [
            DailyLog(
                id=_id("daily-log-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=FIELD_ID,
                log_date=_dt(2026, 2, 24),
                status="SUBMITTED",
                weather_data={
                    "high_temp": 42,
                    "low_temp": 28,
                    "conditions": "Partly Cloudy",
                    "wind": "10 mph NW",
                    "precipitation": "None",
                },
                manpower=[
                    {"trade": "Electrical", "count": 6, "hours": 8},
                    {"trade": "Plumbing", "count": 4, "hours": 8},
                    {"trade": "General Labor", "count": 8, "hours": 8},
                ],
                work_performed=(
                    "Continued electrical rough-in on floors 3-4. "
                    "Plumbing stack installation in progress on floor 2. "
                    "General cleanup and material staging for next week."
                ),
                delays=[],
            ),
            DailyLog(
                id=_id("daily-log-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=FIELD_ID,
                log_date=_dt(2026, 2, 25),
                status="SUBMITTED",
                weather_data={
                    "high_temp": 38,
                    "low_temp": 22,
                    "conditions": "Snow Showers",
                    "wind": "15 mph N",
                    "precipitation": "2 inches snow",
                },
                manpower=[
                    {"trade": "Electrical", "count": 6, "hours": 6},
                    {"trade": "Concrete", "count": 3, "hours": 4},
                    {"trade": "General Labor", "count": 5, "hours": 6},
                ],
                work_performed=(
                    "Reduced crew due to weather. Electrical work continued indoors. "
                    "Concrete pour on level 5 deck postponed to Friday. "
                    "Snow removal and site access maintenance."
                ),
                delays=[
                    {
                        "reason": "Weather",
                        "description": "Snow showers caused 2-hour delay in morning start",
                        "hours_lost": 2,
                    }
                ],
            ),
            DailyLog(
                id=_id("daily-log-3"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=FIELD_ID,
                log_date=_dt(2026, 2, 26),
                status="DRAFT",
                weather_data={
                    "high_temp": 45,
                    "low_temp": 30,
                    "conditions": "Clear",
                    "wind": "5 mph SW",
                    "precipitation": "None",
                },
                manpower=[
                    {"trade": "Electrical", "count": 8, "hours": 8},
                    {"trade": "Plumbing", "count": 5, "hours": 8},
                    {"trade": "Concrete", "count": 6, "hours": 8},
                    {"trade": "General Labor", "count": 10, "hours": 8},
                ],
                work_performed=(
                    "Full crew back on site. Concrete pour on level 5 deck completed. "
                    "Electrical rough-in floors 3-4 nearing completion. "
                    "Plumbing stack installation floor 2 completed, starting floor 3."
                ),
                delays=[],
            ),
        ]
        db.add_all(daily_logs)

        # ------------------------------------------------------------------
        # 8b. RFIs (5 RFIs, mixed statuses)
        # ------------------------------------------------------------------
        rfis = [
            RFI(
                id=_id("rfi-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=1,
                subject="Structural steel connection detail at grid line D-4",
                question=(
                    "Drawing S-201 shows a moment connection at grid D-4, but the "
                    "structural notes call for a shear connection at all perimeter columns. "
                    "Please clarify which connection type is required."
                ),
                assigned_to=MGMT_ID,
                priority="HIGH",
                cost_impact=True,
                schedule_impact=True,
                due_date=_dt(2026, 2, 20),
                status="CLOSED",
                official_response=(
                    "Use moment connection as shown on S-201. The structural notes "
                    "have been updated in Addendum 3. Moment connection is required "
                    "at all perimeter columns on grid lines C and D."
                ),
                responded_by=ADMIN_ID,
                responded_at=_dt(2026, 2, 19),
            ),
            RFI(
                id=_id("rfi-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=FIELD_ID,
                number=2,
                subject="Elevator shaft waterproofing specification",
                question=(
                    "The spec calls for a liquid-applied membrane in the elevator pit, "
                    "but the detail on A-401 shows a sheet membrane. Which product "
                    "should be used? Carlisle 860 or CETCO Voltex DS?"
                ),
                assigned_to=MGMT_ID,
                priority="NORMAL",
                cost_impact=False,
                schedule_impact=False,
                due_date=_dt(2026, 3, 1),
                status="RESPONDED",
                official_response=(
                    "Use Carlisle 860 liquid-applied membrane per spec section 07 14 00. "
                    "Drawing A-401 will be revised in the next drawing set."
                ),
                responded_by=MGMT_ID,
                responded_at=_dt(2026, 2, 25),
            ),
            RFI(
                id=_id("rfi-3"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=3,
                subject="Mechanical room clearance above ductwork",
                question=(
                    "The mechanical room on floor 2 has only 7'-6\" clearance above "
                    "the main trunk duct. Code requires 7'-0\" minimum. The current "
                    "routing conflicts with the fire sprinkler main. Can we route the "
                    "sprinkler main below the duct?"
                ),
                assigned_to=ADMIN_ID,
                priority="HIGH",
                cost_impact=True,
                schedule_impact=True,
                due_date=_dt(2026, 3, 5),
                status="OPEN",
            ),
            RFI(
                id=_id("rfi-4"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=FIELD_ID,
                number=4,
                subject="Exterior window sill flashing detail",
                question=(
                    "The window schedule calls for aluminum sill flashing, but the "
                    "curtain wall shop drawings show an integrated drip edge. Please "
                    "confirm if a separate sill flashing is still required."
                ),
                assigned_to=MGMT_ID,
                priority="NORMAL",
                cost_impact=False,
                schedule_impact=False,
                due_date=_dt(2026, 3, 10),
                status="OPEN",
            ),
            RFI(
                id=_id("rfi-5"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=5,
                subject="Parking garage lighting layout discrepancy",
                question=(
                    "Electrical drawing E-101 shows 48 LED fixtures in the B1 parking "
                    "garage, but the lighting schedule lists 36. Which count is correct? "
                    "The photometric study was based on 48 fixtures."
                ),
                assigned_to=FIELD_ID,
                priority="LOW",
                cost_impact=True,
                schedule_impact=False,
                due_date=_dt(2026, 3, 15),
                status="OPEN",
            ),
        ]
        db.add_all(rfis)

        # ------------------------------------------------------------------
        # 8c. Submittals (3 submittals)
        # ------------------------------------------------------------------
        submittals = [
            Submittal(
                id=_id("submittal-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=1,
                revision=0,
                title="Structural Steel Shop Drawings - Floors 1-5",
                description="Fabrication drawings for all structural steel members floors 1 through 5.",
                spec_section="05 12 00",
                submittal_type="SHOP_DRAWING",
                submitted_by_sub_id=None,
                assigned_to=MGMT_ID,
                status="APPROVED",
                reviewer_id=ADMIN_ID,
                review_notes="Approved. Proceed with fabrication.",
                reviewed_at=_dt(2026, 2, 10),
                due_date=_dt(2026, 2, 5),
                lead_time_days=45,
            ),
            Submittal(
                id=_id("submittal-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=2,
                revision=0,
                title="Electrical Switchgear Submittals",
                description="Main switchgear and distribution panels for floors 1-10.",
                spec_section="26 24 00",
                submittal_type="PRODUCT_DATA",
                submitted_by_sub_id=SUB1_CO_ID,
                assigned_to=MGMT_ID,
                status="SUBMITTED",
                due_date=_dt(2026, 3, 1),
                lead_time_days=60,
            ),
            Submittal(
                id=_id("submittal-3"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=3,
                revision=1,
                parent_submittal_id=_id("submittal-3-rev0"),
                title="Curtain Wall System Mock-up",
                description="Full-scale mock-up details and performance test results for curtain wall system.",
                spec_section="08 44 00",
                submittal_type="SAMPLE",
                submitted_by_sub_id=None,
                assigned_to=ADMIN_ID,
                status="REVISE_AND_RESUBMIT",
                reviewer_id=ADMIN_ID,
                review_notes="Thermal break detail does not match spec. Revise gasket material to meet U-value requirement.",
                reviewed_at=_dt(2026, 2, 20),
                due_date=_dt(2026, 2, 15),
                lead_time_days=30,
            ),
        ]
        # Also add the parent submittal for the revision chain
        parent_submittal = Submittal(
            id=_id("submittal-3-rev0"),
            organization_id=ORG_ID,
            project_id=P,
            created_by=MGMT_ID,
            number=3,
            revision=0,
            title="Curtain Wall System Mock-up",
            spec_section="08 44 00",
            submittal_type="SAMPLE",
            status="REVISE_AND_RESUBMIT",
            reviewer_id=ADMIN_ID,
            review_notes="Initial submission — gasket material insufficient.",
            reviewed_at=_dt(2026, 2, 12),
            due_date=_dt(2026, 2, 10),
        )
        db.add(parent_submittal)
        db.add_all(submittals)

        # ------------------------------------------------------------------
        # 8d. Change Orders (2 change orders)
        # ------------------------------------------------------------------
        change_orders = [
            ChangeOrder(
                id=_id("co-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=1,
                title="Additional structural reinforcement at elevator shaft",
                order_type="PCO",
                reason="Design change per RFI-001 response requiring moment connections",
                description="Additional steel tonnage and welding labor for upgraded connections at grid D-4.",
                priority="HIGH",
                total_amount=Decimal("45000.00"),
                gc_amount=Decimal("45000.00"),
                markup_percent=Decimal("10.00"),
                markup_amount=Decimal("4500.00"),
                schedule_impact_days=5,
                cost_breakdown=[
                    {"description": "Additional steel (2.5 tons)", "amount": 22500},
                    {"description": "Welding labor (120 hrs)", "amount": 18000},
                    {"description": "Engineering review", "amount": 4500},
                ],
                status="DRAFT",
            ),
            ChangeOrder(
                id=_id("co-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=ADMIN_ID,
                number=2,
                title="Owner-requested lobby finish upgrade",
                order_type="CO",
                reason="Owner requested upgrade from porcelain tile to natural stone in main lobby",
                description="Change from 24x24 porcelain tile to honed marble in main lobby and elevator lobbies floors 1-3.",
                priority="NORMAL",
                total_amount=Decimal("125000.00"),
                gc_amount=Decimal("125000.00"),
                markup_percent=Decimal("10.00"),
                markup_amount=Decimal("12500.00"),
                schedule_impact_days=0,
                cost_breakdown=[
                    {"description": "Material difference (marble vs porcelain)", "amount": 85000},
                    {"description": "Additional labor (specialized installer)", "amount": 32000},
                    {"description": "Design coordination", "amount": 8000},
                ],
                status="APPROVED",
                owner_decision="APPROVED",
                owner_decision_by=OWNER_USER_ID,
                owner_decision_at=_dt(2026, 2, 15),
                owner_decision_notes="Approved. Please proceed with marble selection samples.",
                submitted_to_owner_at=_dt(2026, 2, 10),
            ),
        ]
        db.add_all(change_orders)

        # ------------------------------------------------------------------
        # 8e. Pay App (1 pay app)
        # ------------------------------------------------------------------
        pay_app = PayApp(
            id=_id("payapp-1"),
            organization_id=ORG_ID,
            project_id=P,
            created_by=MGMT_ID,
            number=1,
            pay_app_type="GC_TO_OWNER",
            period_start=_dt(2026, 1, 1),
            period_end=_dt(2026, 1, 31),
            retention_rate=Decimal("10.00"),
            original_contract_sum=Decimal("12500000.00"),
            net_change_orders=Decimal("125000.00"),
            contract_sum_to_date=Decimal("12625000.00"),
            total_completed=Decimal("1890000.00"),
            total_retainage=Decimal("189000.00"),
            total_earned_less_retainage=Decimal("1701000.00"),
            previous_certificates=Decimal("0.00"),
            net_payment_due=Decimal("1701000.00"),
            balance_to_finish=Decimal("10735000.00"),
            sov_data=[
                {
                    "item": "01-000",
                    "description": "General Conditions",
                    "scheduled_value": 750000,
                    "previous_completed": 0,
                    "this_period": 150000,
                    "stored_materials": 0,
                },
                {
                    "item": "03-000",
                    "description": "Concrete",
                    "scheduled_value": 2800000,
                    "previous_completed": 0,
                    "this_period": 840000,
                    "stored_materials": 50000,
                },
                {
                    "item": "16-000",
                    "description": "Electrical",
                    "scheduled_value": 1850000,
                    "previous_completed": 0,
                    "this_period": 370000,
                    "stored_materials": 25000,
                },
            ],
            status="SUBMITTED",
            submitted_by_type="GC_USER",
            submitted_by_id=MGMT_ID,
            submitted_at=_dt(2026, 2, 5),
        )
        db.add(pay_app)

        # ------------------------------------------------------------------
        # 8f. Punch List Items (4 items)
        # ------------------------------------------------------------------
        punch_items = [
            PunchListItem(
                id=_id("punch-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=1,
                title="Damaged drywall in stairwell B, floor 3",
                description="Large gouge in drywall approximately 12\" x 8\" from material delivery.",
                location="Stairwell B, Floor 3",
                trade="Finishes",
                priority="NORMAL",
                assigned_sub_company_id=None,
                status="OPEN",
                due_date=_dt(2026, 3, 15),
            ),
            PunchListItem(
                id=_id("punch-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=2,
                title="Electrical outlet not functioning - Suite 401",
                description="Duplex outlet on north wall of Suite 401 has no power. Breaker is on.",
                location="Suite 401, North Wall",
                trade="Electrical",
                priority="HIGH",
                assigned_sub_company_id=SUB1_CO_ID,
                status="IN_PROGRESS",
                due_date=_dt(2026, 3, 1),
            ),
            PunchListItem(
                id=_id("punch-3"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=FIELD_ID,
                number=3,
                title="Plumbing leak at floor 2 restroom",
                description="Slow drip at supply line connection under sink #3 in men's restroom floor 2.",
                location="Floor 2, Men's Restroom",
                trade="Plumbing",
                priority="HIGH",
                assigned_sub_company_id=SUB2_CO_ID,
                status="COMPLETED_BY_SUB",
                due_date=_dt(2026, 2, 28),
                completion_notes="Tightened compression fitting and replaced supply hose. Leak resolved.",
                completed_by=SUB2_USER_ID,
                completed_at=_dt(2026, 2, 24),
            ),
            PunchListItem(
                id=_id("punch-4"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=4,
                title="Fire caulking missing at floor 1 penetration",
                description="Firestopping caulk missing around electrical conduit penetration through rated wall at floor 1 electrical room.",
                location="Floor 1, Electrical Room",
                trade="Fire Protection",
                priority="CRITICAL",
                assigned_sub_company_id=SUB1_CO_ID,
                status="VERIFIED_BY_GC",
                due_date=_dt(2026, 2, 20),
                completion_notes="Applied 3M CP25WB+ firestopping caulk per UL System W-L-7079.",
                completed_by=SUB1_USER_ID,
                completed_at=_dt(2026, 2, 18),
                verification_notes="Verified firestopping installation. Passes visual inspection.",
                verified_by=MGMT_ID,
                verified_at=_dt(2026, 2, 19),
            ),
        ]
        db.add_all(punch_items)

        # ------------------------------------------------------------------
        # 8g. Inspections (2 inspections)
        # ------------------------------------------------------------------
        insp_template = InspectionTemplate(
            id=_id("insp-template-1"),
            organization_id=ORG_ID,
            name="Concrete Pour Inspection",
            is_default=True,
            fields=[
                {"name": "Concrete Mix Design Verified", "type": "checkbox"},
                {"name": "Rebar Placement Verified", "type": "checkbox"},
                {"name": "Formwork Condition", "type": "select", "options": ["Good", "Fair", "Poor"]},
                {"name": "Slump Test Result", "type": "number", "unit": "inches"},
                {"name": "Air Content", "type": "number", "unit": "%"},
                {"name": "Temperature", "type": "number", "unit": "°F"},
                {"name": "Notes", "type": "text"},
            ],
        )
        db.add(insp_template)

        inspections = [
            Inspection(
                id=_id("inspection-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=1,
                title="Level 5 Concrete Deck Pour Inspection",
                template_id=_id("insp-template-1"),
                category="CONCRETE",
                scheduled_date=_dt(2026, 2, 27),
                scheduled_time="08:00 AM",
                location="Floor 5, Deck",
                inspector_user_id=MGMT_ID,
                inspector_name="Sam Chen",
                inspector_company="Acme Construction Co.",
                status="SCHEDULED",
            ),
            Inspection(
                id=_id("inspection-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=2,
                title="Electrical Rough-In Inspection - Floors 3-4",
                template_id=_id("insp-template-1"),
                category="ELECTRICAL",
                scheduled_date=_dt(2026, 2, 22),
                scheduled_time="10:00 AM",
                location="Floors 3-4",
                inspector_user_id=FIELD_ID,
                inspector_name="Taylor Kim",
                inspector_company="Acme Construction Co.",
                status="COMPLETED",
                overall_result="PASS",
                completed_date=_dt(2026, 2, 22),
                form_data={
                    "checklist": [
                        {"item": "Wire gauge verified", "result": "PASS"},
                        {"item": "Box fill calculations", "result": "PASS"},
                        {"item": "Grounding continuity", "result": "PASS"},
                        {"item": "Conduit support spacing", "result": "PASS"},
                    ]
                },
                checklist_results=[
                    {"item": "Wire gauge verified", "result": "PASS"},
                    {"item": "Box fill calculations", "result": "PASS"},
                    {"item": "Grounding continuity", "result": "PASS"},
                    {"item": "Conduit support spacing", "result": "PASS"},
                ],
                notes="All rough-in work on floors 3-4 meets code. Cleared for insulation and drywall.",
            ),
        ]
        db.add_all(inspections)

        # ------------------------------------------------------------------
        # 8h. Budget Line Items (5 items)
        # ------------------------------------------------------------------
        budget_items = [
            BudgetLineItem(
                id=_id("budget-1"),
                project_id=P,
                cost_code="01-000",
                description="General Conditions",
                original_amount=Decimal("750000.00"),
                approved_changes=Decimal("0.00"),
                committed=Decimal("650000.00"),
                actuals=Decimal("150000.00"),
                projected=Decimal("750000.00"),
            ),
            BudgetLineItem(
                id=_id("budget-2"),
                project_id=P,
                cost_code="03-000",
                description="Concrete",
                original_amount=Decimal("2800000.00"),
                approved_changes=Decimal("45000.00"),
                committed=Decimal("2650000.00"),
                actuals=Decimal("890000.00"),
                projected=Decimal("2845000.00"),
            ),
            BudgetLineItem(
                id=_id("budget-3"),
                project_id=P,
                cost_code="16-000",
                description="Electrical",
                original_amount=Decimal("1850000.00"),
                approved_changes=Decimal("0.00"),
                committed=Decimal("1850000.00"),
                actuals=Decimal("395000.00"),
                projected=Decimal("1850000.00"),
            ),
            BudgetLineItem(
                id=_id("budget-4"),
                project_id=P,
                cost_code="15-000",
                description="Mechanical / Plumbing",
                original_amount=Decimal("975000.00"),
                approved_changes=Decimal("0.00"),
                committed=Decimal("975000.00"),
                actuals=Decimal("210000.00"),
                projected=Decimal("975000.00"),
            ),
            BudgetLineItem(
                id=_id("budget-5"),
                project_id=P,
                cost_code="22-000",
                description="Plumbing",
                original_amount=Decimal("620000.00"),
                approved_changes=Decimal("0.00"),
                committed=Decimal("580000.00"),
                actuals=Decimal("125000.00"),
                projected=Decimal("620000.00"),
            ),
        ]
        db.add_all(budget_items)

        # ------------------------------------------------------------------
        # 8i. Meetings (2 meetings)
        # ------------------------------------------------------------------
        meetings = [
            Meeting(
                id=_id("meeting-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=1,
                title="Weekly OAC Progress Meeting #12",
                meeting_type="PROGRESS",
                scheduled_date=_dt(2026, 3, 3),
                start_time=_dt(2026, 3, 3, 10, 0),
                end_time=_dt(2026, 3, 3, 11, 30),
                location="Job Site Trailer, Conference Room",
                attendees=[
                    {"name": "Alex Morgan", "company": "Acme Construction", "role": "GC"},
                    {"name": "Sam Chen", "company": "Acme Construction", "role": "PM"},
                    {"name": "Morgan Lee", "company": "Downtown Development Partners", "role": "Owner"},
                    {"name": "Lisa Park", "company": "Park & Associates", "role": "Architect"},
                ],
                agenda=(
                    "1. Safety report\n"
                    "2. Schedule update & look-ahead\n"
                    "3. RFI status review\n"
                    "4. Submittal status review\n"
                    "5. Change order discussion\n"
                    "6. Old business\n"
                    "7. New business"
                ),
                recurring=True,
                recurrence_rule="WEEKLY",
                status="SCHEDULED",
            ),
            Meeting(
                id=_id("meeting-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                number=2,
                title="Electrical Coordination Meeting",
                meeting_type="COORDINATION",
                scheduled_date=_dt(2026, 2, 24),
                start_time=_dt(2026, 2, 24, 14, 0),
                end_time=_dt(2026, 2, 24, 15, 0),
                location="Job Site Trailer",
                attendees=[
                    {"name": "Sam Chen", "company": "Acme Construction", "role": "PM"},
                    {"name": "Taylor Kim", "company": "Acme Construction", "role": "Field Eng"},
                    {"name": "Chris Watts", "company": "Summit Electric", "role": "Sub PM"},
                ],
                agenda=(
                    "1. Floors 3-4 rough-in schedule\n"
                    "2. Switchgear delivery timeline\n"
                    "3. RFI-005 parking garage lighting\n"
                    "4. Manpower plan for next 2 weeks"
                ),
                minutes=(
                    "Floors 3-4 rough-in on track for completion by March 7. "
                    "Switchgear delivery confirmed for March 20. "
                    "RFI-005 response pending from architect — follow up by Feb 28. "
                    "Summit to increase crew from 6 to 10 starting March 1."
                ),
                action_items=[
                    {"description": "Follow up on RFI-005 with architect", "assigned_to": "Sam Chen", "due_date": "2026-02-28"},
                    {"description": "Confirm switchgear staging area", "assigned_to": "Taylor Kim", "due_date": "2026-03-01"},
                    {"description": "Submit updated manpower schedule", "assigned_to": "Chris Watts", "due_date": "2026-02-27"},
                ],
                minutes_published=True,
                minutes_published_at=_dt(2026, 2, 25),
                status="COMPLETED",
            ),
        ]
        db.add_all(meetings)

        # ------------------------------------------------------------------
        # 8j. Todos (4 todos)
        # ------------------------------------------------------------------
        todos = [
            Todo(
                id=_id("todo-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                title="Order concrete test cylinders for level 5 pour",
                description="Need 6 sets of cylinders for the level 5 deck pour scheduled for Feb 27.",
                assigned_to=FIELD_ID,
                due_date=_dt(2026, 2, 26),
                priority="HIGH",
                category="Procurement",
                status="DONE",
                completed_at=_dt(2026, 2, 25),
            ),
            Todo(
                id=_id("todo-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                title="Submit updated 3-week look-ahead schedule",
                description="Update and distribute 3-week look-ahead to all subs and owner.",
                assigned_to=MGMT_ID,
                due_date=_dt(2026, 2, 28),
                priority="NORMAL",
                category="Schedule",
                status="IN_PROGRESS",
            ),
            Todo(
                id=_id("todo-3"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=ADMIN_ID,
                title="Review sub pay app from Summit Electric",
                description="Review and approve/reject Summit Electric's January pay application.",
                assigned_to=MGMT_ID,
                due_date=_dt(2026, 3, 5),
                priority="NORMAL",
                category="Financial",
                status="OPEN",
            ),
            Todo(
                id=_id("todo-4"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=FIELD_ID,
                title="Schedule fire alarm rough-in inspection",
                description="Coordinate with AHJ for fire alarm rough-in inspection on floors 1-2.",
                assigned_to=FIELD_ID,
                due_date=_dt(2026, 3, 10),
                priority="HIGH",
                category="Inspections",
                status="OPEN",
            ),
        ]
        db.add_all(todos)

        # ------------------------------------------------------------------
        # 8k. Documents (3 documents with folder)
        # ------------------------------------------------------------------
        doc_folder = DocumentFolder(
            id=_id("doc-folder-1"),
            organization_id=ORG_ID,
            project_id=P,
            name="Contracts",
            is_system=True,
            created_by=ADMIN_ID,
        )
        db.add(doc_folder)

        documents = [
            Document(
                id=_id("document-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=ADMIN_ID,
                title="Prime Contract - Downtown Office Tower",
                category="Contracts",
                description="Executed AIA A101 prime contract between Acme Construction and Downtown Development Partners.",
                folder_id=_id("doc-folder-1"),
                version=1,
                tags=["contract", "executed", "AIA"],
                uploaded_by=ADMIN_ID,
            ),
            Document(
                id=_id("document-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                title="Geotechnical Report",
                category="Reports",
                description="Geotechnical investigation report by Terracon Consultants, dated Dec 2025.",
                version=1,
                tags=["geotech", "soils", "report"],
                uploaded_by=MGMT_ID,
            ),
            Document(
                id=_id("document-3"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                title="Building Permit - City of Denver",
                category="Permits",
                description="Issued building permit #BP-2026-00142 from the City and County of Denver.",
                version=1,
                tags=["permit", "building", "city"],
                uploaded_by=MGMT_ID,
            ),
        ]
        db.add_all(documents)

        # ------------------------------------------------------------------
        # 8l. Schedule Tasks (5 tasks with dependencies)
        # ------------------------------------------------------------------
        schedule_tasks = [
            ScheduleTask(
                id=_id("task-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                name="Foundations & Below-Grade",
                wbs_code="1.0",
                sort_order=1,
                start_date=_dt(2026, 1, 20),
                end_date=_dt(2026, 3, 15),
                duration=40,
                baseline_start=_dt(2026, 1, 15),
                baseline_end=_dt(2026, 3, 10),
                baseline_duration=38,
                percent_complete=85,
                actual_start=_dt(2026, 1, 20),
                is_critical=True,
                predecessors=[],
            ),
            ScheduleTask(
                id=_id("task-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                name="Structural Steel Erection",
                wbs_code="2.0",
                sort_order=2,
                start_date=_dt(2026, 3, 1),
                end_date=_dt(2026, 6, 30),
                duration=85,
                baseline_start=_dt(2026, 3, 1),
                baseline_end=_dt(2026, 6, 15),
                baseline_duration=75,
                percent_complete=15,
                actual_start=_dt(2026, 3, 3),
                is_critical=True,
                predecessors=[{"task_id": str(_id("task-1")), "type": "FS", "lag": 0}],
            ),
            ScheduleTask(
                id=_id("task-3"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                name="Electrical Rough-In Floors 1-5",
                wbs_code="3.0",
                sort_order=3,
                start_date=_dt(2026, 2, 15),
                end_date=_dt(2026, 4, 30),
                duration=52,
                baseline_start=_dt(2026, 2, 15),
                baseline_end=_dt(2026, 4, 15),
                baseline_duration=42,
                percent_complete=40,
                actual_start=_dt(2026, 2, 17),
                assigned_to_sub_id=SUB1_CO_ID,
                is_critical=False,
                predecessors=[{"task_id": str(_id("task-1")), "type": "SS", "lag": 20}],
            ),
            ScheduleTask(
                id=_id("task-4"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                name="Plumbing Rough-In Floors 1-5",
                wbs_code="4.0",
                sort_order=4,
                start_date=_dt(2026, 2, 15),
                end_date=_dt(2026, 5, 15),
                duration=63,
                baseline_start=_dt(2026, 2, 15),
                baseline_end=_dt(2026, 5, 1),
                baseline_duration=52,
                percent_complete=30,
                actual_start=_dt(2026, 2, 18),
                assigned_to_sub_id=SUB2_CO_ID,
                is_critical=False,
                predecessors=[{"task_id": str(_id("task-1")), "type": "SS", "lag": 20}],
            ),
            ScheduleTask(
                id=_id("task-5"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                name="Level 5 Concrete Deck Pour",
                wbs_code="1.5",
                sort_order=5,
                start_date=_dt(2026, 2, 27),
                end_date=_dt(2026, 2, 27),
                duration=1,
                baseline_start=_dt(2026, 2, 25),
                baseline_end=_dt(2026, 2, 25),
                baseline_duration=1,
                percent_complete=0,
                milestone=True,
                is_critical=True,
                predecessors=[{"task_id": str(_id("task-1")), "type": "FS", "lag": -15}],
            ),
        ]
        db.add_all(schedule_tasks)

        # ------------------------------------------------------------------
        # 8m. Procurement Items (3 items)
        # ------------------------------------------------------------------
        procurement_items = [
            ProcurementItem(
                id=_id("procurement-1"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                name="Main Electrical Switchgear",
                description="4000A main switchgear with integrated metering, Square D QED-2 series.",
                category="Electrical",
                spec_section="26 24 00",
                vendor="Summit Electric LLC",
                vendor_contact="Chris Watts",
                vendor_phone="(303) 555-0201",
                vendor_email="sub@demo.conflo.app",
                po_number="PO-2026-042",
                cost_code="16-000",
                estimated_cost=Decimal("285000.00"),
                actual_cost=Decimal("278000.00"),
                lead_time_days=90,
                required_on_site_date=_dt(2026, 3, 20),
                order_by_date=_dt(2025, 12, 20),
                expected_delivery_date=_dt(2026, 3, 18),
                status="SHIPPED",
                tracking_number="1Z999AA10123456784",
                assigned_to=FIELD_ID,
                sub_company_id=SUB1_CO_ID,
                dates={
                    "ordered": "2025-12-18",
                    "confirmed": "2025-12-22",
                    "shipped": "2026-03-10",
                },
            ),
            ProcurementItem(
                id=_id("procurement-2"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=MGMT_ID,
                name="Curtain Wall System",
                description="Aluminum-framed curtain wall system, floors 1-10, Kawneer 1600 series.",
                category="Openings",
                spec_section="08 44 00",
                vendor="Western Glass & Glazing",
                vendor_contact="Janet Moore",
                vendor_phone="(303) 555-0700",
                cost_code="08-000",
                estimated_cost=Decimal("1200000.00"),
                lead_time_days=120,
                required_on_site_date=_dt(2026, 5, 1),
                order_by_date=_dt(2026, 1, 1),
                status="ORDERED",
                assigned_to=MGMT_ID,
                dates={
                    "ordered": "2026-01-05",
                    "confirmed": "2026-01-12",
                },
            ),
            ProcurementItem(
                id=_id("procurement-3"),
                organization_id=ORG_ID,
                project_id=P,
                created_by=FIELD_ID,
                name="Elevator Cab Finishes",
                description="Custom elevator cab interiors for 4 passenger elevators. Stainless steel and glass panels.",
                category="Conveying",
                spec_section="14 21 00",
                vendor="Otis Elevator Co.",
                vendor_contact="Rob Martinez",
                vendor_phone="(303) 555-0800",
                cost_code="14-000",
                estimated_cost=Decimal("180000.00"),
                lead_time_days=150,
                required_on_site_date=_dt(2026, 8, 1),
                order_by_date=_dt(2026, 3, 1),
                status="IDENTIFIED",
                assigned_to=MGMT_ID,
                dates={},
            ),
        ]
        db.add_all(procurement_items)

        # ------------------------------------------------------------------
        # 8n. Bid Package + Submissions (for bidding project)
        # ------------------------------------------------------------------
        bid_package = BidPackage(
            id=_id("bidpkg-1"),
            organization_id=ORG_ID,
            project_id=PROJ_BIDDING_ID,
            created_by=PRECON_ID,
            number=1,
            title="Electrical Systems - Riverside Medical Center",
            description=(
                "Complete electrical systems including power distribution, lighting, "
                "low voltage, fire alarm, and emergency generator for the Riverside "
                "Medical Center project."
            ),
            trade="Electrical",
            trades=["Electrical", "Low Voltage", "Fire Protection"],
            bid_due_date=_dt(2026, 3, 15, 17, 0),
            pre_bid_meeting_date=_dt(2026, 3, 5, 10, 0),
            estimated_value=Decimal("2200000.00"),
            requirements=(
                "Bidders must be licensed electrical contractors in the State of Colorado. "
                "Minimum 5 years healthcare construction experience required. "
                "Must provide proof of bonding capacity for full contract value."
            ),
            invited_sub_ids=[str(SUB1_CO_ID)],
            status="PUBLISHED",
        )
        db.add(bid_package)

        bid_submissions = [
            BidSubmission(
                id=_id("bidsub-1"),
                bid_package_id=_id("bidpkg-1"),
                sub_company_id=SUB1_CO_ID,
                total_amount=Decimal("2150000.00"),
                line_items=[
                    {"description": "Power Distribution", "amount": 850000},
                    {"description": "Lighting Systems", "amount": 520000},
                    {"description": "Low Voltage / Data", "amount": 380000},
                    {"description": "Fire Alarm", "amount": 280000},
                    {"description": "Emergency Generator", "amount": 120000},
                ],
                qualifications=(
                    "Summit Electric has 12 years of healthcare electrical experience "
                    "including Denver Health Expansion and St. Luke's Medical Pavilion."
                ),
                schedule_duration_days=180,
                exclusions="Tax, permit fees, temporary power beyond initial setup.",
                status="SUBMITTED",
                submitted_at=_dt(2026, 3, 12),
            ),
            BidSubmission(
                id=_id("bidsub-2"),
                bid_package_id=_id("bidpkg-1"),
                sub_company_id=SUB2_CO_ID,
                total_amount=Decimal("2350000.00"),
                line_items=[
                    {"description": "Power Distribution", "amount": 920000},
                    {"description": "Lighting Systems", "amount": 580000},
                    {"description": "Low Voltage / Data", "amount": 410000},
                    {"description": "Fire Alarm", "amount": 300000},
                    {"description": "Emergency Generator", "amount": 140000},
                ],
                qualifications=(
                    "Mountain Plumbing cross-trades into electrical through our sister "
                    "company Mountain Electric Division. 8 years healthcare experience."
                ),
                schedule_duration_days=200,
                status="SUBMITTED",
                submitted_at=_dt(2026, 3, 14),
            ),
        ]
        db.add_all(bid_submissions)

        # ==================================================================
        # 9. Owner Portal Config (active project)
        # ==================================================================
        owner_config = OwnerPortalConfig(
            id=_id("owner-config-active"),
            project_id=PROJ_ACTIVE_ID,
            show_schedule=True,
            show_submittals=True,
            show_rfis=True,
            show_transmittals=True,
            show_drawings=True,
            show_punch_list=True,
            show_budget_summary=True,
            show_daily_logs=False,
            allow_punch_creation=False,
        )
        db.add(owner_config)

        # ==================================================================
        # 10. Notifications (5 for admin user)
        # ==================================================================
        notifications = [
            Notification(
                id=_id("notification-1"),
                user_type="GC_USER",
                user_id=ADMIN_ID,
                type="rfi_response",
                title="RFI-002 has been responded to",
                body="Sam Chen responded to RFI-002: Elevator shaft waterproofing specification.",
                source_type="RFI",
                source_id=_id("rfi-2"),
                project_id=PROJ_ACTIVE_ID,
                read_at=_dt(2026, 2, 25, 14, 0),
            ),
            Notification(
                id=_id("notification-2"),
                user_type="GC_USER",
                user_id=ADMIN_ID,
                type="pay_app_submitted",
                title="Pay App #1 submitted for review",
                body="Sam Chen submitted Pay App #1 for Downtown Office Tower (Jan 2026). Net payment due: $1,701,000.00.",
                source_type="PAY_APP",
                source_id=_id("payapp-1"),
                project_id=PROJ_ACTIVE_ID,
                read_at=None,
            ),
            Notification(
                id=_id("notification-3"),
                user_type="GC_USER",
                user_id=ADMIN_ID,
                type="co_decision",
                title="Change Order CO-002 approved by owner",
                body="Morgan Lee approved CO-002: Owner-requested lobby finish upgrade ($125,000.00).",
                source_type="CHANGE_ORDER",
                source_id=_id("co-2"),
                project_id=PROJ_ACTIVE_ID,
                read_at=_dt(2026, 2, 16, 9, 0),
            ),
            Notification(
                id=_id("notification-4"),
                user_type="GC_USER",
                user_id=ADMIN_ID,
                type="submittal_decision",
                title="Submittal 003.01 requires revision",
                body="Curtain Wall System Mock-up was marked Revise and Resubmit. Thermal break detail does not match spec.",
                source_type="SUBMITTAL",
                source_id=_id("submittal-3"),
                project_id=PROJ_ACTIVE_ID,
                read_at=None,
            ),
            Notification(
                id=_id("notification-5"),
                user_type="GC_USER",
                user_id=ADMIN_ID,
                type="bid_submitted",
                title="New bid received for BP-001",
                body="Summit Electric LLC submitted a bid of $2,150,000 for Electrical Systems - Riverside Medical Center.",
                source_type="BID_SUBMISSION",
                source_id=_id("bidsub-1"),
                project_id=PROJ_BIDDING_ID,
                read_at=None,
            ),
        ]
        db.add_all(notifications)

        # ==================================================================
        # Commit all data
        # ==================================================================
        await db.commit()

        print("=" * 60)
        print("  Demo data seeded successfully!")
        print("=" * 60)
        print()
        print(f"  Organization: Acme Construction Co.")
        print(f"  Org ID:       {ORG_ID}")
        print()
        print(f"  GC Users (4):")
        print(f"    admin@demo.conflo.app  — Alex Morgan    (OWNER_ADMIN)")
        print(f"    precon@demo.conflo.app — Jordan Rivera  (PRE_CONSTRUCTION)")
        print(f"    mgmt@demo.conflo.app   — Sam Chen       (MANAGEMENT)")
        print(f"    field@demo.conflo.app  — Taylor Kim     (USER)")
        print()
        print(f"  Sub Users (2):")
        print(f"    sub@demo.conflo.app    — Chris Watts    (Summit Electric LLC)")
        print(f"    sub2@demo.conflo.app   — Pat Rivera     (Mountain Plumbing Inc.)")
        print()
        print(f"  Owner User (1):")
        print(f"    owner@demo.conflo.app  — Morgan Lee     (Downtown Development Partners)")
        print()
        print(f"  Projects (3):")
        print(f"    2026-001  Downtown Office Tower       ACTIVE    $12,500,000")
        print(f"    2026-002  Riverside Medical Center    BIDDING   $8,750,000")
        print(f"    2026-003  Mountain View Apartments    CLOSEOUT  $3,200,000")
        print()
        print(f"  Active Project Data:")
        print(f"    Daily Logs:      3")
        print(f"    RFIs:            5  (1 Closed, 1 Responded, 3 Open)")
        print(f"    Submittals:      4  (1 Approved, 1 Submitted, 2 Revise & Resubmit)")
        print(f"    Change Orders:   2  (1 Draft, 1 Approved)")
        print(f"    Pay Apps:        1  (Submitted)")
        print(f"    Punch List:      4  (1 Open, 1 In Progress, 1 Completed, 1 Verified)")
        print(f"    Inspections:     2  (1 Scheduled, 1 Completed)")
        print(f"    Budget Items:    5")
        print(f"    Meetings:        2  (1 Scheduled, 1 Completed)")
        print(f"    Todos:           4  (2 Open, 1 In Progress, 1 Done)")
        print(f"    Documents:       3")
        print(f"    Schedule Tasks:  5")
        print(f"    Procurement:     3  (Identified, Ordered, Shipped)")
        print()
        print(f"  Bidding Project Data:")
        print(f"    Bid Packages:    1  (Published)")
        print(f"    Bid Submissions: 2")
        print()
        print(f"  Notifications:     5  (3 unread, 2 read)")
        print(f"  Cost Code Template: CSI MasterFormat Standard (24 codes)")
        print(f"  Owner Portal Config: Active project — most tools visible")
        print()


if __name__ == "__main__":
    asyncio.run(seed())
