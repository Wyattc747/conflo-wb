import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.organization import Organization
from app.models.user import User
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.sub_company import SubCompany
from app.models.sub_user import SubUser
from app.models.owner_account import OwnerAccount
from app.models.owner_user import OwnerUser
from app.models.owner_portal_config import OwnerPortalConfig
from app.models.notification import Notification


# ============================================================
# IDS
# ============================================================

ORG_ID = uuid.uuid4()
ADMIN_USER_ID = uuid.uuid4()
PRECON_USER_ID = uuid.uuid4()
MGMT_USER_ID = uuid.uuid4()
FIELD_USER_ID = uuid.uuid4()
PROJECT_ID = uuid.uuid4()
BIDDING_PROJECT_ID = uuid.uuid4()
SUB_COMPANY_ID = uuid.uuid4()
SUB_USER_ID = uuid.uuid4()
OWNER_ACCOUNT_ID = uuid.uuid4()
OWNER_USER_ID = uuid.uuid4()


# ============================================================
# USER CONTEXT DICTS (as attached to request.state.user)
# ============================================================

@pytest.fixture
def admin_user():
    return {
        "user_type": "gc",
        "user_id": ADMIN_USER_ID,
        "organization_id": ORG_ID,
        "permission_level": "OWNER_ADMIN",
    }

@pytest.fixture
def precon_user():
    return {
        "user_type": "gc",
        "user_id": PRECON_USER_ID,
        "organization_id": ORG_ID,
        "permission_level": "PRE_CONSTRUCTION",
    }

@pytest.fixture
def management_user():
    return {
        "user_type": "gc",
        "user_id": MGMT_USER_ID,
        "organization_id": ORG_ID,
        "permission_level": "MANAGEMENT",
    }

@pytest.fixture
def field_user():
    return {
        "user_type": "gc",
        "user_id": FIELD_USER_ID,
        "organization_id": ORG_ID,
        "permission_level": "USER",
    }

@pytest.fixture
def sub_user():
    return {
        "user_type": "sub",
        "user_id": SUB_USER_ID,
        "sub_company_id": SUB_COMPANY_ID,
        "permission_level": None,
    }

@pytest.fixture
def owner_user():
    return {
        "user_type": "owner",
        "user_id": OWNER_USER_ID,
        "owner_account_id": OWNER_ACCOUNT_ID,
        "permission_level": None,
    }


# ============================================================
# MOCK PROJECT OBJECTS
# ============================================================

@pytest.fixture
def active_project():
    """Project in ACTIVE phase."""
    project = MagicMock(spec=Project)
    project.id = PROJECT_ID
    project.organization_id = ORG_ID
    project.name = "Test Active Project"
    project.phase = "ACTIVE"
    project.deleted_at = None
    project.contract_value = 500000
    project.is_major = True
    return project

@pytest.fixture
def bidding_project():
    """Project in BIDDING phase."""
    project = MagicMock(spec=Project)
    project.id = BIDDING_PROJECT_ID
    project.organization_id = ORG_ID
    project.name = "Test Bidding Project"
    project.phase = "BIDDING"
    project.deleted_at = None
    project.contract_value = 100000
    project.is_major = False
    return project

@pytest.fixture
def closed_project():
    """Project in CLOSED phase."""
    project = MagicMock(spec=Project)
    project.id = uuid.uuid4()
    project.organization_id = ORG_ID
    project.name = "Test Closed Project"
    project.phase = "CLOSED"
    project.deleted_at = None
    return project

@pytest.fixture
def closeout_project():
    project = MagicMock(spec=Project)
    project.id = uuid.uuid4()
    project.organization_id = ORG_ID
    project.name = "Test Closeout Project"
    project.phase = "CLOSEOUT"
    project.deleted_at = None
    return project

@pytest.fixture
def buyout_project():
    project = MagicMock(spec=Project)
    project.id = uuid.uuid4()
    project.organization_id = ORG_ID
    project.name = "Test Buyout Project"
    project.phase = "BUYOUT"
    project.deleted_at = None
    return project


# ============================================================
# MOCK ASSIGNMENTS
# ============================================================

@pytest.fixture
def gc_assignment():
    """GC_USER assignment with no special access."""
    a = MagicMock(spec=ProjectAssignment)
    a.project_id = PROJECT_ID
    a.assignee_type = "GC_USER"
    a.assignee_id = FIELD_USER_ID
    a.financial_access = False
    a.bidding_access = False
    return a

@pytest.fixture
def gc_assignment_financial():
    """GC_USER assignment with financial_access."""
    a = MagicMock(spec=ProjectAssignment)
    a.project_id = PROJECT_ID
    a.assignee_type = "GC_USER"
    a.assignee_id = FIELD_USER_ID
    a.financial_access = True
    a.bidding_access = False
    return a

@pytest.fixture
def gc_assignment_bidding():
    """GC_USER assignment with bidding_access."""
    a = MagicMock(spec=ProjectAssignment)
    a.project_id = PROJECT_ID
    a.assignee_type = "GC_USER"
    a.assignee_id = FIELD_USER_ID
    a.financial_access = False
    a.bidding_access = True
    return a

@pytest.fixture
def sub_assignment():
    a = MagicMock(spec=ProjectAssignment)
    a.project_id = PROJECT_ID
    a.assignee_type = "SUB_COMPANY"
    a.assignee_id = SUB_COMPANY_ID
    a.financial_access = False
    a.bidding_access = False
    return a

@pytest.fixture
def owner_assignment():
    a = MagicMock(spec=ProjectAssignment)
    a.project_id = PROJECT_ID
    a.assignee_type = "OWNER_ACCOUNT"
    a.assignee_id = OWNER_ACCOUNT_ID
    a.financial_access = False
    a.bidding_access = False
    return a


# ============================================================
# MOCK OWNER PORTAL CONFIG
# ============================================================

@pytest.fixture
def default_portal_config():
    """Default portal config -- most things visible."""
    config = MagicMock(spec=OwnerPortalConfig)
    config.show_schedule = True
    config.show_submittals = True
    config.show_rfis = True
    config.show_transmittals = True
    config.show_drawings = True
    config.show_punch_list = True
    config.show_budget_summary = False
    config.show_daily_logs = False
    config.allow_punch_creation = False
    return config

@pytest.fixture
def restricted_portal_config():
    """Restricted portal config -- nothing toggled on."""
    config = MagicMock(spec=OwnerPortalConfig)
    config.show_schedule = False
    config.show_submittals = False
    config.show_rfis = False
    config.show_transmittals = False
    config.show_drawings = False
    config.show_punch_list = False
    config.show_budget_summary = False
    config.show_daily_logs = False
    config.allow_punch_creation = False
    return config


# ============================================================
# MOCK DB SESSION HELPER
# ============================================================

@pytest.fixture
def mock_db():
    """Create a mock AsyncSession."""
    db = AsyncMock()
    return db
