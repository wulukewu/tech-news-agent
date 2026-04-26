"""
Proactive Learning API

REST endpoints for managing learning conversations, preferences, and settings.
Requirements: 9.1, 9.2, 9.3
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.qa_agent.proactive_learning.behavior_analyzer import BehaviorAnalyzer
from app.qa_agent.proactive_learning.conversation_manager import ConversationManager
from app.qa_agent.proactive_learning.feedback_processor import FeedbackProcessor
from app.qa_agent.proactive_learning.learning_trigger import LearningTrigger
from app.qa_agent.proactive_learning.preference_model import PreferenceModel
from app.qa_agent.proactive_learning.weight_adjuster import WeightAdjuster
from app.schemas.responses import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning")


# ── Request schemas ──────────────────────────────────────────────────────────


class RespondRequest(BaseModel):
    response: str


class PreferencesUpdateRequest(BaseModel):
    category_weights: dict[str, float] | None = None


class SettingsUpdateRequest(BaseModel):
    learning_enabled: bool | None = None
    max_weekly_conversations: int | None = None


class BehaviorEventRequest(BaseModel):
    event_type: str  # 'read', 'rate', 'click', 'bookmark', 'skip'
    article_id: str | None = None
    category: str | None = None
    rating: int | None = None
    duration_seconds: int | None = None


class OnboardingRequest(BaseModel):
    selected_categories: list[str]


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/conversations/pending")
async def get_pending_conversations(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Return all pending learning conversations for the current user."""
    user_id = str(current_user["user_id"])
    mgr = ConversationManager()
    conversations = await mgr.get_pending_conversations(user_id)
    return success_response({"conversations": conversations, "count": len(conversations)})


@router.post("/conversations/{conversation_id}/respond")
async def respond_to_conversation(
    conversation_id: str,
    body: RespondRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Submit user response to a learning conversation.
    Processes feedback and updates preference weights.
    """
    user_id = str(current_user["user_id"])

    # Fetch conversation to get question + context
    from app.services.supabase_service import SupabaseService

    supabase = SupabaseService()
    try:
        resp = (
            supabase.client.table("learning_conversations")
            .select("*")
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        conv = resp.data
    except Exception:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    if not conv or conv.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Conversation is not pending.")

    # Mark answered
    mgr = ConversationManager()
    await mgr.mark_answered(conversation_id, body.response)

    # Process feedback and update weights
    import json

    ctx = conv.get("context_data")
    if isinstance(ctx, str):
        try:
            ctx = json.loads(ctx)
        except Exception:
            ctx = {}

    processor = FeedbackProcessor()
    signals = await processor.process(
        question=conv.get("question", ""),
        response=body.response,
        context=ctx,
    )

    updated_weights: dict[str, float] = {}
    if signals.get("weight_adjustments"):
        adjuster = WeightAdjuster()
        updated_weights = await adjuster.apply_feedback(user_id, signals["weight_adjustments"])

    return success_response(
        {
            "signals": signals,
            "updated_weights": updated_weights,
        }
    )


@router.get("/preferences")
async def get_preferences(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Return the current preference model for the user."""
    user_id = str(current_user["user_id"])
    model = PreferenceModel()
    prefs = await model.get(user_id)
    return success_response(prefs)


@router.put("/preferences")
async def update_preferences(
    body: PreferencesUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Manually set category weights."""
    user_id = str(current_user["user_id"])
    if not body.category_weights:
        raise HTTPException(status_code=422, detail="category_weights required.")
    model = PreferenceModel()
    await model.set_weights(user_id, body.category_weights)
    updated = await model.get(user_id)
    return success_response(updated)


@router.get("/settings")
async def get_settings(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Return learning agent settings for the user."""
    user_id = str(current_user["user_id"])
    model = PreferenceModel()
    prefs = await model.get(user_id)
    return success_response(
        {
            "learning_enabled": prefs.get("learning_enabled", True),
            "max_weekly_conversations": prefs.get("max_weekly_conversations", 3),
            "conversations_this_week": prefs.get("conversations_this_week", 0),
        }
    )


@router.put("/settings")
async def update_settings(
    body: SettingsUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Update learning agent settings (enabled, frequency)."""
    user_id = str(current_user["user_id"])
    update: dict[str, Any] = {}
    if body.learning_enabled is not None:
        update["learning_enabled"] = body.learning_enabled
    if body.max_weekly_conversations is not None:
        if not 1 <= body.max_weekly_conversations <= 7:
            raise HTTPException(status_code=422, detail="max_weekly_conversations must be 1-7.")
        update["max_weekly_conversations"] = body.max_weekly_conversations
    if not update:
        raise HTTPException(status_code=422, detail="No valid fields to update.")
    model = PreferenceModel()
    await model.update_settings(user_id, update)
    return success_response({"updated": update})


@router.post("/events")
async def record_behavior_event(
    body: BehaviorEventRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Record a user behavior event (read, rate, click, etc.)."""
    user_id = str(current_user["user_id"])
    analyzer = BehaviorAnalyzer()
    await analyzer.record_event(
        user_id=user_id,
        event_type=body.event_type,
        article_id=body.article_id,
        category=body.category,
        rating=body.rating,
        duration_seconds=body.duration_seconds,
    )
    return success_response({"recorded": True})


@router.post("/trigger")
async def manual_trigger(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Manually trigger behavior analysis and create a conversation if warranted."""
    user_id = str(current_user["user_id"])
    trigger = LearningTrigger()
    should, context = await trigger.should_trigger(user_id)
    if not should:
        return success_response({"triggered": False, "reason": "No trigger condition met."})

    mgr = ConversationManager()
    conv = await mgr.create_conversation(user_id, context)
    await trigger.increment_conversation_count(user_id)
    return success_response({"triggered": True, "conversation": conv})


@router.post("/onboarding")
async def complete_onboarding(
    body: OnboardingRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Initialize preference weights from user-selected categories.
    Sets selected categories to 0.8, others to 0.3.
    Also creates an initial learning conversation if none exist.
    """
    user_id = str(current_user["user_id"])

    if not body.selected_categories:
        raise HTTPException(status_code=422, detail="At least one category required.")

    # Build initial weights
    ALL_CATEGORIES = [
        "AI/ML",
        "Web Development",
        "DevOps",
        "Security",
        "Cloud",
        "Mobile",
        "Data Science",
        "Open Source",
        "Startup",
        "Hardware",
    ]
    weights: dict[str, float] = {}
    for cat in ALL_CATEGORIES:
        weights[cat] = 0.8 if cat in body.selected_categories else 0.3
    for cat in body.selected_categories:
        if cat not in weights:
            weights[cat] = 0.8

    model = PreferenceModel()
    await model.set_weights(user_id, weights)

    # Create initial conversation if none pending
    mgr = ConversationManager()
    existing = await mgr.get_pending_conversations(user_id)
    initial_conv = None
    if not existing:
        context = {
            "reason": "onboarding",
            "selected_categories": body.selected_categories,
        }
        initial_conv = await mgr.create_conversation(user_id, context)

    updated = await model.get(user_id)
    return success_response(
        {
            "weights": updated.get("category_weights", {}),
            "initial_conversation": initial_conv,
        }
    )


# ── Preference Summary ────────────────────────────────────────────────────────


class UpdateSummaryRequest(BaseModel):
    summary: str


@router.get("/summary")
async def get_preference_summary(current_user: dict[str, Any] = Depends(get_current_user)):
    """Get user's preference summary and category weights."""
    from app.services.supabase_service import SupabaseService

    supabase = SupabaseService()
    user_id = str(current_user["user_id"])  # Convert UUID to string
    try:
        resp = (
            supabase.client.table("preference_model")
            .select("preference_summary, category_weights, summary_updated_at")
            .eq("user_id", user_id)
            .execute()
        )
        data = resp.data[0] if resp.data else {}
    except Exception:
        data = {}

    import json

    weights = data.get("category_weights") or {}
    if isinstance(weights, str):
        weights = json.loads(weights)

    return success_response(
        {
            "preference_summary": data.get("preference_summary"),
            "category_weights": weights,
            "summary_updated_at": data.get("summary_updated_at"),
        }
    )


@router.patch("/summary")
async def update_preference_summary_endpoint(
    body: UpdateSummaryRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Manually update user's preference summary."""
    from datetime import UTC, datetime

    from app.services.supabase_service import SupabaseService

    supabase = SupabaseService()
    user_id = str(current_user["user_id"])  # Convert UUID to string
    try:
        # First check if record exists
        existing = (
            supabase.client.table("preference_model").select("id").eq("user_id", user_id).execute()
        )

        if existing.data:
            # Update existing record
            supabase.client.table("preference_model").update(
                {
                    "preference_summary": body.summary.strip(),
                    "summary_updated_at": datetime.now(UTC).isoformat(),
                    "updated_at": datetime.now(UTC).isoformat(),
                }
            ).eq("user_id", user_id).execute()
        else:
            # Insert new record
            supabase.client.table("preference_model").insert(
                {
                    "user_id": user_id,
                    "preference_summary": body.summary.strip(),
                    "summary_updated_at": datetime.now(UTC).isoformat(),
                    "updated_at": datetime.now(UTC).isoformat(),
                }
            ).execute()
    except Exception as exc:
        logger.error("Failed to update preference summary: %s", exc)
        raise HTTPException(status_code=500, detail="無法更新偏好摘要")

    return success_response({"preference_summary": body.summary.strip()})
