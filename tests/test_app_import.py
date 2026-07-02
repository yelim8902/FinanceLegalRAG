def test_fastapi_app_imports() -> None:
    from app.main import app

    assert app.title == "Financial Regulation Compliance Monitoring Agent"
