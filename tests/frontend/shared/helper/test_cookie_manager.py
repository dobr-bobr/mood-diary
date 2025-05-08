from mood_diary.frontend.shared.helper.cookie_manager import get_cookie_manager
import pytest

PATCH_TARGET_STX = "mood_diary.frontend.shared.helper.cookie_manager.stx"
PATCH_TARGET_ST = "mood_diary.frontend.shared.helper.cookie_manager.st"


def test_get_cookie_manager_returns_cookie_manager_instance(mocker):
    mock_stx = mocker.patch(PATCH_TARGET_STX)
    mock_st = mocker.patch(PATCH_TARGET_ST)

    expected_cookie_manager_instance = mocker.MagicMock()
    mock_stx.CookieManager.return_value = expected_cookie_manager_instance

    original_get_cookie_manager = getattr(
        get_cookie_manager, "__wrapped__", None
    )

    if original_get_cookie_manager is None:
        pytest.skip(
            "Cannot access the original function (__wrapped__) of the fragment for testing."
        )
        return

    cookie_manager_instance = original_get_cookie_manager()

    mock_stx.CookieManager.assert_called_once()
    assert cookie_manager_instance is expected_cookie_manager_instance
