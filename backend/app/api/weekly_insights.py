"""
Weekly Insights API

REST endpoints for generating and retrieving weekly insight reports.
Requirements: 7.1, 7.3
"""

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.qa_agent.weekly_insights.report_generator import InsightReportGenerator
from app.schemas.responses import success_response
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateRequest(BaseModel):
    days: int = 7
    end_date: str | None = None  # ISO 8601 string


@router.post("/weekly-insights/generate")
async def generate_weekly_insights(
    body: GenerateRequest = GenerateRequest(),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Manually trigger weekly insights report generation.

    Runs the full pipeline (collect → analyze → cluster → trend → report)
    and returns the generated report.
    """
    user_id = str(current_user.get("id", ""))

    end_date: datetime | None = None
    if body.end_date:
        try:
            end_date = datetime.fromisoformat(body.end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid end_date format. Use ISO 8601.",
            )

    try:
        generator = InsightReportGenerator()
        report = await generator.generate(
            days=body.days,
            end_date=end_date,
            user_id=user_id or None,
        )
        return success_response(report)
    except Exception as exc:
        logger.error("Failed to generate weekly insights: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate weekly insights report.",
        )


@router.get("/weekly-insights/latest")
async def get_latest_insights(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Return the most recently generated weekly insights report."""
    try:
        supabase = SupabaseService()
        response = (
            supabase.client.table("weekly_insights")
            .select("*")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return success_response(None)
        return success_response(_deserialize_report(rows[0]))
    except Exception as exc:
        logger.error("Failed to fetch latest insights: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch latest insights.")


@router.get("/weekly-insights/history")
async def get_insights_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Return paginated list of historical weekly insight reports."""
    try:
        supabase = SupabaseService()
        offset = (page - 1) * page_size
        response = (
            supabase.client.table("weekly_insights")
            .select("id, period_start, period_end, article_count, executive_summary, created_at")
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = response.data or []
        return success_response({"reports": rows, "page": page, "page_size": page_size})
    except Exception as exc:
        logger.error("Failed to fetch insights history: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch insights history.")


@router.get("/weekly-insights/{report_id}")
async def get_insights_by_id(
    report_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Return a specific weekly insights report by ID."""
    try:
        supabase = SupabaseService()
        response = (
            supabase.client.table("weekly_insights")
            .select("*")
            .eq("id", report_id)
            .single()
            .execute()
        )
        row = response.data
        if not row:
            raise HTTPException(status_code=404, detail="Report not found.")
        return success_response(_deserialize_report(row))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch insights report %s: %s", report_id, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch insights report.")


@router.get("/weekly-insights/trends/data")
async def get_trends_data(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Return trend data from the latest report for chart rendering."""
    try:
        supabase = SupabaseService()
        response = (
            supabase.client.table("weekly_insights")
            .select("trend_data, period_start, period_end")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return success_response({"trends": [], "period_start": None, "period_end": None})

        row = rows[0]
        trend_data = row.get("trend_data")
        if isinstance(trend_data, str):
            trend_data = json.loads(trend_data)

        return success_response(
            {
                "trends": trend_data or [],
                "period_start": row.get("period_start"),
                "period_end": row.get("period_end"),
            }
        )
    except Exception as exc:
        logger.error("Failed to fetch trends data: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch trends data.")


def _deserialize_report(row: dict[str, Any]) -> dict[str, Any]:
    """Parse JSON string fields back to Python objects."""
    for field in ("clusters", "trends", "missed_articles", "trend_data"):
        val = row.get(field)
        if isinstance(val, str):
            try:
                row[field] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                row[field] = []
    return row
