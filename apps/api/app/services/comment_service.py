import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.event_log import EventLog
from app.models.notification import Notification
from app.schemas.comment import CommentCreate, CommentUpdate


VALID_COMMENTABLE_TYPES = {
    "rfi", "daily_log", "submittal", "transmittal", "change_order",
    "punch_list_item", "inspection", "pay_app", "meeting",
}


async def create_comment(
    db: AsyncSession,
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    user: dict,
    data: CommentCreate,
) -> Comment:
    if data.commentable_type not in VALID_COMMENTABLE_TYPES:
        raise HTTPException(400, f"Invalid commentable type: {data.commentable_type}")

    comment = Comment(
        organization_id=organization_id,
        commentable_type=data.commentable_type,
        commentable_id=data.commentable_id,
        author_type=user.get("user_type", "GC_USER"),
        author_id=user["user_id"],
        body=data.body,
        mentioned_user_ids=data.mentions,
        attachment_ids=data.attachments,
    )
    db.add(comment)

    # Notify mentioned users
    for mentioned_id in data.mentions:
        notification = Notification(
            user_type="GC_USER",
            user_id=mentioned_id,
            type="comment_mention",
            title=f"You were mentioned in a comment",
            body=data.body[:100],
            source_type=data.commentable_type,
            source_id=data.commentable_id,
        )
        db.add(notification)

    # Event log
    event = EventLog(
        organization_id=organization_id,
        project_id=project_id,
        user_type=user.get("user_type", "GC_USER"),
        user_id=user["user_id"],
        event_type="comment_created",
        event_data={
            "commentable_type": data.commentable_type,
            "commentable_id": str(data.commentable_id),
        },
    )
    db.add(event)

    await db.flush()
    return comment


async def list_comments(
    db: AsyncSession,
    commentable_type: str,
    commentable_id: uuid.UUID,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[Comment], int]:
    query = select(Comment).where(
        Comment.commentable_type == commentable_type,
        Comment.commentable_id == commentable_id,
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Comment.created_at.asc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_comment(
    db: AsyncSession,
    comment_id: uuid.UUID,
) -> Comment:
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(404, "Comment not found")
    return comment


async def update_comment(
    db: AsyncSession,
    comment_id: uuid.UUID,
    user: dict,
    data: CommentUpdate,
) -> Comment:
    comment = await get_comment(db, comment_id)
    if comment.author_id != user["user_id"]:
        raise HTTPException(403, "You can only edit your own comments")
    comment.body = data.body
    await db.flush()
    return comment


async def delete_comment(
    db: AsyncSession,
    comment_id: uuid.UUID,
    user: dict,
) -> None:
    comment = await get_comment(db, comment_id)
    if comment.author_id != user["user_id"]:
        raise HTTPException(403, "You can only delete your own comments")
    await db.delete(comment)
    await db.flush()


def format_comment_response(
    comment: Comment,
    author_name: str | None = None,
) -> dict:
    return {
        "id": comment.id,
        "commentable_type": comment.commentable_type,
        "commentable_id": comment.commentable_id,
        "body": comment.body,
        "author_type": comment.author_type,
        "author_id": comment.author_id,
        "author_name": author_name,
        "is_official_response": comment.is_official_response,
        "mentions": comment.mentioned_user_ids,
        "attachments": comment.attachment_ids,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }
