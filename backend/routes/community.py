"""
Community Hub / Support Board
- Users can submit bug reports, feature requests, feedback
- Owner can respond and mark items as answered
- Searchable Q&A / FAQ that grows over time
- Direct contact link to app owner
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid

community_router = APIRouter(prefix="/community", tags=["community"])


class PostCreate(BaseModel):
    title: str
    body: str
    category: str  # bug_report, feature_request, question, feedback


class ReplyCreate(BaseModel):
    body: str


class PostUpdate(BaseModel):
    is_pinned: Optional[bool] = None
    is_answered: Optional[bool] = None
    status: Optional[str] = None  # open, in_progress, resolved, closed


def setup_community_routes(app, db, get_current_active_user, UserInDB):

    @community_router.get("/posts")
    async def list_posts(
        category: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        pinned_only: bool = False,
        skip: int = 0,
        limit: int = 50,
        current_user: UserInDB = Depends(get_current_active_user)
    ):
        """List community posts with optional filters."""
        query = {}

        if category:
            query["category"] = category
        if status:
            query["status"] = status
        if pinned_only:
            query["is_pinned"] = True
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"body": {"$regex": search, "$options": "i"}},
                {"replies.body": {"$regex": search, "$options": "i"}}
            ]

        total = await db.community_posts.count_documents(query)
        posts = await db.community_posts.find(
            query, {"_id": 0}
        ).sort([
            ("is_pinned", -1),
            ("created_at", -1)
        ]).skip(skip).limit(limit).to_list(length=limit)

        return {"posts": posts, "total": total}

    @community_router.get("/posts/{post_id}")
    async def get_post(
        post_id: str,
        current_user: UserInDB = Depends(get_current_active_user)
    ):
        """Get a single post with all replies."""
        post = await db.community_posts.find_one({"id": post_id}, {"_id": 0})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post

    @community_router.post("/posts")
    async def create_post(
        data: PostCreate,
        current_user: UserInDB = Depends(get_current_active_user)
    ):
        """Create a new community post."""
        if data.category not in ["bug_report", "feature_request", "question", "feedback"]:
            raise HTTPException(status_code=400, detail="Invalid category")

        post = {
            "id": str(uuid.uuid4()),
            "title": data.title.strip(),
            "body": data.body.strip(),
            "category": data.category,
            "status": "open",
            "is_pinned": False,
            "is_answered": False,
            "author_name": current_user.full_name or current_user.email.split("@")[0],
            "author_email": current_user.email,
            "author_tenant_id": current_user.tenant_id,
            "author_role": current_user.role,
            "replies": [],
            "upvotes": 0,
            "upvoted_by": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        await db.community_posts.insert_one(post)
        post.pop("_id", None)
        return post

    @community_router.post("/posts/{post_id}/reply")
    async def reply_to_post(
        post_id: str,
        data: ReplyCreate,
        current_user: UserInDB = Depends(get_current_active_user)
    ):
        """Reply to a community post."""
        post = await db.community_posts.find_one({"id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Determine if this is an official reply (from app owner / superadmin)
        is_official = current_user.role == "owner" and current_user.email == "thesigntistslab@gmail.com"

        reply = {
            "id": str(uuid.uuid4()),
            "body": data.body.strip(),
            "author_name": current_user.full_name or current_user.email.split("@")[0],
            "author_email": current_user.email,
            "is_official": is_official,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        update = {
            "$push": {"replies": reply},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }

        # If official reply, auto-mark as answered
        if is_official:
            update["$set"]["is_answered"] = True

        await db.community_posts.update_one({"id": post_id}, update)

        updated = await db.community_posts.find_one({"id": post_id}, {"_id": 0})
        return updated

    @community_router.post("/posts/{post_id}/upvote")
    async def upvote_post(
        post_id: str,
        current_user: UserInDB = Depends(get_current_active_user)
    ):
        """Upvote a post (toggle)."""
        post = await db.community_posts.find_one({"id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        upvoted_by = post.get("upvoted_by", [])
        user_id = current_user.id

        if user_id in upvoted_by:
            upvoted_by.remove(user_id)
        else:
            upvoted_by.append(user_id)

        await db.community_posts.update_one(
            {"id": post_id},
            {"$set": {"upvoted_by": upvoted_by, "upvotes": len(upvoted_by)}}
        )
        return {"upvotes": len(upvoted_by), "upvoted": user_id in upvoted_by}

    @community_router.put("/posts/{post_id}")
    async def update_post(
        post_id: str,
        data: PostUpdate,
        current_user: UserInDB = Depends(get_current_active_user)
    ):
        """Update post status/pin. Owner only for admin actions."""
        post = await db.community_posts.find_one({"id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        update_dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if data.is_pinned is not None:
            if current_user.role != "owner":
                raise HTTPException(status_code=403, detail="Only owners can pin posts")
            update_dict["is_pinned"] = data.is_pinned
        if data.is_answered is not None:
            update_dict["is_answered"] = data.is_answered
        if data.status is not None:
            update_dict["status"] = data.status

        await db.community_posts.update_one({"id": post_id}, {"$set": update_dict})
        updated = await db.community_posts.find_one({"id": post_id}, {"_id": 0})
        return updated

    @community_router.delete("/posts/{post_id}")
    async def delete_post(
        post_id: str,
        current_user: UserInDB = Depends(get_current_active_user)
    ):
        """Delete a post. Only post author or owner."""
        post = await db.community_posts.find_one({"id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post["author_email"] != current_user.email and current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Cannot delete this post")

        await db.community_posts.delete_one({"id": post_id})
        return {"success": True}

    @community_router.get("/stats")
    async def get_stats(current_user: UserInDB = Depends(get_current_active_user)):
        """Get community stats."""
        total = await db.community_posts.count_documents({})
        answered = await db.community_posts.count_documents({"is_answered": True})
        bugs = await db.community_posts.count_documents({"category": "bug_report"})
        features = await db.community_posts.count_documents({"category": "feature_request"})
        open_count = await db.community_posts.count_documents({"status": "open"})
        return {
            "total_posts": total,
            "answered": answered,
            "open": open_count,
            "bug_reports": bugs,
            "feature_requests": features
        }

    app.include_router(community_router, prefix="/api")
