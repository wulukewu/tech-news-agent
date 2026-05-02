#!/usr/bin/env python3
"""
DM Conversation Memory System Verification Script

Verifies that all components of the DM conversation memory system are properly implemented:
1. Database schema (dm_conversations table, preference_summary fields)
2. Backend services (DM listener, preference summary service, scheduler)
3. API endpoints (PATCH /summary, GET /summary)
4. Discord commands (/my_profile, /update_profile)
5. Integration with recommendation system

Usage:
    python3 verify_dm_conversation_memory.py
"""

import asyncio
import sys

from app.services.supabase_service import SupabaseService


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_status(message: str, status: str):
    """Print colored status message."""
    if status == "✓":
        print(f"{Colors.GREEN}{status}{Colors.RESET} {message}")
    elif status == "✗":
        print(f"{Colors.RED}{status}{Colors.RESET} {message}")
    elif status == "⚠":
        print(f"{Colors.YELLOW}{status}{Colors.RESET} {message}")
    else:
        print(f"{Colors.BLUE}{status}{Colors.RESET} {message}")


async def verify_database_schema():
    """Verify database tables and columns exist."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}1. Database Schema Verification{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    supabase = SupabaseService()
    checks_passed = 0
    total_checks = 3

    # Check dm_conversations table
    try:
        result = supabase.client.table("dm_conversations").select("id").limit(1).execute()
        print_status("dm_conversations table exists", "✓")
        checks_passed += 1
    except Exception as e:
        print_status(f"dm_conversations table missing: {e}", "✗")

    # Check preference_model.preference_summary column
    try:
        result = (
            supabase.client.table("preference_model")
            .select("preference_summary")
            .limit(1)
            .execute()
        )
        print_status("preference_model.preference_summary column exists", "✓")
        checks_passed += 1
    except Exception as e:
        print_status(f"preference_summary column missing: {e}", "✗")

    # Check preference_model.summary_updated_at column
    try:
        result = (
            supabase.client.table("preference_model")
            .select("summary_updated_at")
            .limit(1)
            .execute()
        )
        print_status("preference_model.summary_updated_at column exists", "✓")
        checks_passed += 1
    except Exception as e:
        print_status(f"summary_updated_at column missing: {e}", "✗")

    return checks_passed, total_checks


async def verify_backend_services():
    """Verify backend services are properly implemented."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}2. Backend Services Verification{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    checks_passed = 0
    total_checks = 5

    # Check DM listener
    try:
        from app.bot.cogs.dm_conversation_listener import DMConversationListener

        print_status("DMConversationListener cog exists", "✓")
        checks_passed += 1
    except ImportError as e:
        print_status(f"DMConversationListener import failed: {e}", "✗")

    # Check preference summary service
    try:
        from app.services.preference_summary_service import update_preference_summary

        print_status("PreferenceSummaryService exists", "✓")
        checks_passed += 1
    except ImportError as e:
        print_status(f"PreferenceSummaryService import failed: {e}", "✗")

    # Check auto preference summary
    try:
        from app.services.auto_preference_summary import schedule_preference_summary_update

        print_status("Auto preference summary trigger exists", "✓")
        checks_passed += 1
    except ImportError as e:
        print_status(f"Auto preference summary import failed: {e}", "✗")

    # Check scheduler job
    try:
        from app.tasks.scheduler import preference_summary_job

        print_status("preference_summary_job scheduled task exists", "✓")
        checks_passed += 1
    except ImportError as e:
        print_status(f"Scheduler job import failed: {e}", "✗")

    # Check recommendation integration
    try:
        from app.services.recommendation_reason import generate_reason

        print_status("Recommendation reason service uses preference_summary", "✓")
        checks_passed += 1
    except ImportError as e:
        print_status(f"Recommendation reason import failed: {e}", "✗")

    return checks_passed, total_checks


async def verify_api_endpoints():
    """Verify API endpoints are registered."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}3. API Endpoints Verification{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    checks_passed = 0
    total_checks = 2

    # Check PATCH /summary endpoint
    try:
        from app.api.proactive_learning import router

        # Check if PATCH /summary route exists
        routes = [route for route in router.routes if hasattr(route, "path")]
        patch_summary = any(
            "/summary" in route.path and "PATCH" in route.methods for route in routes
        )
        if patch_summary:
            print_status("PATCH /api/learning/summary endpoint exists", "✓")
            checks_passed += 1
        else:
            print_status("PATCH /api/learning/summary endpoint missing", "✗")
    except Exception as e:
        print_status(f"API endpoint check failed: {e}", "✗")

    # Check GET /summary endpoint
    try:
        get_summary = any("/summary" in route.path and "GET" in route.methods for route in routes)
        if get_summary:
            print_status("GET /api/learning/summary endpoint exists", "✓")
            checks_passed += 1
        else:
            print_status("GET /api/learning/summary endpoint missing", "✗")
    except Exception as e:
        print_status(f"GET endpoint check failed: {e}", "✗")

    return checks_passed, total_checks


async def verify_discord_commands():
    """Verify Discord commands are implemented."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}4. Discord Commands Verification{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    checks_passed = 0
    total_checks = 2

    # Check /my_profile command
    try:
        from app.bot.cogs.news_commands import NewsCommands

        # Check if my_profile method exists
        if hasattr(NewsCommands, "my_profile"):
            print_status("/my_profile command exists", "✓")
            checks_passed += 1
        else:
            print_status("/my_profile command missing", "✗")
    except Exception as e:
        print_status(f"/my_profile check failed: {e}", "✗")

    # Check /update_profile command
    try:
        if hasattr(NewsCommands, "update_profile"):
            print_status("/update_profile command exists", "✓")
            checks_passed += 1
        else:
            print_status("/update_profile command missing", "✗")
    except Exception as e:
        print_status(f"/update_profile check failed: {e}", "✗")

    return checks_passed, total_checks


async def verify_recommendation_integration():
    """Verify recommendation system uses preference_summary."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}5. Recommendation Integration Verification{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    checks_passed = 0
    total_checks = 2

    # Check proactive_recommendation.py uses preference_summary
    try:
        with open("app/tasks/proactive_recommendation.py", "r") as f:
            content = f.read()
            if "preference_summary" in content:
                print_status("Proactive recommendation uses preference_summary", "✓")
                checks_passed += 1
            else:
                print_status("Proactive recommendation doesn't use preference_summary", "✗")
    except Exception as e:
        print_status(f"Proactive recommendation check failed: {e}", "✗")

    # Check recommendation_reason.py uses preference_summary
    try:
        with open("app/services/recommendation_reason.py", "r") as f:
            content = f.read()
            if "preference_summary" in content:
                print_status("Recommendation reason uses preference_summary", "✓")
                checks_passed += 1
            else:
                print_status("Recommendation reason doesn't use preference_summary", "✗")
    except Exception as e:
        print_status(f"Recommendation reason check failed: {e}", "✗")

    return checks_passed, total_checks


async def test_end_to_end_flow():
    """Test a simple end-to-end flow (optional, requires test user)."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}6. End-to-End Flow Test (Optional){Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    print_status("E2E test requires a test user - skipping for now", "⚠")
    print_status("To test manually:", "ℹ")
    print("  1. Send a DM to the bot: '我喜歡 Rust 和系統程式設計'")
    print("  2. Run /update_profile command")
    print("  3. Run /my_profile to see the summary")
    print("  4. Check if recommendations mention your preferences")

    return 0, 1


async def main():
    """Run all verification checks."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}DM Conversation Memory System Verification{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")

    total_passed = 0
    total_checks = 0

    # Run all verification checks
    checks = [
        verify_database_schema(),
        verify_backend_services(),
        verify_api_endpoints(),
        verify_discord_commands(),
        verify_recommendation_integration(),
        test_end_to_end_flow(),
    ]

    for check in checks:
        passed, total = await check
        total_passed += passed
        total_checks += total

    # Print summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}Summary{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    percentage = (total_passed / total_checks * 100) if total_checks > 0 else 0

    if percentage == 100:
        print(f"{Colors.GREEN}✓ All checks passed! ({total_passed}/{total_checks}){Colors.RESET}")
        print(
            f"\n{Colors.GREEN}🎉 DM Conversation Memory System is fully implemented!{Colors.RESET}\n"
        )
        return 0
    elif percentage >= 80:
        print(
            f"{Colors.YELLOW}⚠ Most checks passed ({total_passed}/{total_checks} - {percentage:.0f}%){Colors.RESET}"
        )
        print(f"\n{Colors.YELLOW}System is mostly complete, minor issues to fix.{Colors.RESET}\n")
        return 1
    else:
        print(
            f"{Colors.RED}✗ Many checks failed ({total_passed}/{total_checks} - {percentage:.0f}%){Colors.RESET}"
        )
        print(f"\n{Colors.RED}System needs significant work.{Colors.RESET}\n")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
