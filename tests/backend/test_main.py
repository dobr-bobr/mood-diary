import pytest


def test_main_app_instance():
    """Tests that the main app instance is created."""
    try:
        from mood_diary.backend.main import app
        assert app is not None, "app object in main.py should not be None"
        from fastapi import FastAPI
        assert isinstance(app, FastAPI), "app object should be a FastAPI instance"
    except ImportError as e:
        pytest.fail(f"Failed to import app from mood_diary.backend.main: {e}")
    except Exception as e:
        pytest.fail(f"An exception occurred during app import/creation: {e}") 