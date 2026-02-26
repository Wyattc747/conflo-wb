import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rfi import RFI
from app.models.submittal import Submittal
from app.models.transmittal import Transmittal
from app.models.change_order import ChangeOrder
from app.models.punch_list_item import PunchListItem
from app.models.inspection import Inspection
from app.models.bid_package import BidPackage
from app.models.meeting import Meeting
from app.models.pay_app import PayApp


# ============================================================
# FORMAT DEFINITIONS
# ============================================================
# Maps tool type to (format_string, model_class)

TOOL_MODELS = {
    "rfi": RFI,
    "submittal": Submittal,
    "transmittal": Transmittal,
    "change_order": ChangeOrder,
    "punch_list_item": PunchListItem,
    "inspection": Inspection,
    "bid_package": BidPackage,
    "meeting": Meeting,
    "pay_app": PayApp,
}

FORMATS = {
    "rfi": "RFI-{:03d}",
    "submittal": "{:03d}.{:02d}",  # base.revision
    "transmittal": "TR-{:03d}",
    "change_order_pco": "PCO-{:03d}",
    "change_order_co": "CO-{:03d}",
    "punch_list_item": "PL-{:03d}",
    "inspection": "INSP-{:03d}",
    "bid_package": "BP-{:03d}",
    "meeting": "MTG-{:03d}",
    "pay_app": "#{:d}",  # Not zero-padded
}


# ============================================================
# CORE FUNCTIONS
# ============================================================

async def get_next_number(
    db: AsyncSession,
    project_id: uuid.UUID,
    tool_type: str,
) -> int:
    """
    Get the next auto-increment number for a tool within a project.

    Uses SELECT MAX(number) + 1 with row-level locking (FOR UPDATE)
    to ensure atomicity. Numbers are never reused — soft-deleted
    records keep their numbers.

    Returns 1 if no records exist for this project/tool.
    """
    model = TOOL_MODELS.get(tool_type)
    if model is None:
        raise ValueError(f"Unknown tool type: {tool_type}")

    # Use FOR UPDATE to lock rows and prevent concurrent number conflicts
    # We select the max number from ALL records (including soft-deleted if applicable)
    result = await db.execute(
        select(func.coalesce(func.max(model.number), 0))
        .where(model.project_id == project_id)
        .with_for_update()
    )
    current_max = result.scalar_one()
    return current_max + 1


async def get_next_submittal_revision(
    db: AsyncSession,
    project_id: uuid.UUID,
    base_number: int,
) -> int:
    """
    Get the next revision number for a submittal with a given base number.

    E.g., if 001.00 and 001.01 exist, returns 2 (for 001.02).
    If base number doesn't exist yet, returns 0.
    """
    result = await db.execute(
        select(func.coalesce(func.max(Submittal.revision), -1))
        .where(
            Submittal.project_id == project_id,
            Submittal.number == base_number,
        )
        .with_for_update()
    )
    current_max = result.scalar_one()
    return current_max + 1


def format_number(tool_type: str, number: int, revision: int | None = None) -> str:
    """
    Format a tool number for display.

    Examples:
        format_number("rfi", 1) -> "RFI-001"
        format_number("rfi", 42) -> "RFI-042"
        format_number("submittal", 1, 0) -> "001.00"
        format_number("submittal", 1, 1) -> "001.01"
        format_number("change_order_pco", 5) -> "PCO-005"
        format_number("change_order_co", 5) -> "CO-005"
        format_number("pay_app", 3) -> "#3"
    """
    if tool_type == "submittal":
        fmt = FORMATS["submittal"]
        return fmt.format(number, revision if revision is not None else 0)

    # For change orders, determine PCO vs CO
    if tool_type == "change_order":
        # Default to PCO format
        fmt = FORMATS["change_order_pco"]
        return fmt.format(number)

    fmt = FORMATS.get(tool_type)
    if fmt is None:
        raise ValueError(f"Unknown tool type: {tool_type}")

    return fmt.format(number)


def format_change_order_number(number: int, is_approved: bool = False) -> str:
    """
    Format a change order number.
    PCO while draft/pending, CO when approved.

    Examples:
        format_change_order_number(1) -> "PCO-001"
        format_change_order_number(1, is_approved=True) -> "CO-001"
    """
    if is_approved:
        return FORMATS["change_order_co"].format(number)
    return FORMATS["change_order_pco"].format(number)
