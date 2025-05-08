from mood_diary.frontend.shared.helper.check_passwords import compare_passwords

def test_passwords_match():
    assert compare_passwords("password123","password123") is True

def test_passwords_do_not_match():
    assert compare_passwords("password123", "Password123") is False

def test_passwords_different_lengths():
    assert compare_passwords("pass", "password") is False

def test_empty_passwords_match():
    assert compare_passwords("", "") is True

def test_one_empty_password():
    assert compare_passwords("password123", "") is False

def test_other_empty_password():
    assert compare_passwords("", "password123") is False
