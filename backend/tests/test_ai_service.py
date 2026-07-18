from pathlib import Path
from app.core.config import Settings
from app.services.ai_service import AIService


def test_ai_service_offline_mock_planning() -> None:
    settings = Settings(gemini_api_key=None)  # Forces offline fallback mode
    ai = AIService(settings)
    
    # 1. Search Query
    plan = ai.generate_plan(
        user_query="Find report files",
        allowed_roots=["/allowed"],
        current_workspace="/workspace"
    )
    assert len(plan.steps) == 1
    assert plan.steps[0].tool == "search_files"
    assert plan.steps[0].parameters["query"] == "files"
    
    # 2. Django scaffold
    plan = ai.generate_plan(
        user_query="Scaffold a django app named CollegePortal",
        allowed_roots=["/allowed"],
        current_workspace="/workspace"
    )
    assert len(plan.steps) == 4
    assert plan.steps[0].tool == "create_project"
    assert plan.steps[0].parameters["project_type"] == "django"
    assert plan.steps[1].tool == "initialize_git"
    assert plan.steps[2].tool == "install_dependencies"
    assert plan.steps[3].tool == "create_readme"
