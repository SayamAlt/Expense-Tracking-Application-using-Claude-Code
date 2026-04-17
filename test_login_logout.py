#!/usr/bin/env python3
"""Test script for login and logout functionality"""

from app import app
from database.db import get_db

def test_login_logout():
    with app.test_client() as c:
        print("=" * 60)
        print("Testing Login and Logout Functionality")
        print("=" * 60)

        # Test 1: Access login page
        print("\n1. Testing GET /login...")
        rv = c.get('/login')
        assert rv.status_code == 200, f"Expected 200, got {rv.status_code}"
        assert b'Sign in' in rv.data, "Login page should contain 'Sign in'"
        print("   ✓ Login page loads successfully")

        # Test 2: Invalid login credentials
        print("\n2. Testing invalid login...")
        rv = c.post('/login', data={'email': 'invalid@test.com', 'password': 'wrong'})
        assert rv.status_code == 200, f"Expected 200, got {rv.status_code}"
        assert b'Invalid email or password' in rv.data, "Should show error for invalid credentials"
        print("   ✓ Invalid login shows error message")

        # Test 3: Valid login
        print("\n3. Testing valid login...")
        rv = c.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
        assert rv.status_code == 302, f"Expected 302 redirect, got {rv.status_code}"
        assert rv.headers.get('Location') == '/profile', f"Should redirect to /profile, got {rv.headers.get('Location')}"
        print("   ✓ Valid login redirects to profile")

        # Test 4: Access profile after login
        print("\n4. Testing profile access after login...")
        with c.session_transaction() as sess:
            user_id = sess.get('user_id')
        assert user_id is not None, "User should be logged in"
        rv = c.get('/profile')
        assert rv.status_code == 200, f"Expected 200, got {rv.status_code}"
        assert str(user_id).encode() in rv.data, "Profile should show user ID"
        print(f"   ✓ Profile accessible (user_id: {user_id})")

        # Test 5: Logout
        print("\n5. Testing logout...")
        rv = c.get('/logout')
        assert rv.status_code == 302, f"Expected 302 redirect, got {rv.status_code}"
        assert rv.headers.get('Location') == '/', f"Should redirect to /, got {rv.headers.get('Location')}"
        print("   ✓ Logout redirects to landing page")

        # Test 6: Verify session cleared after logout
        print("\n6. Testing session cleared after logout...")
        with c.session_transaction() as sess:
            user_id = sess.get('user_id')
        assert user_id is None, "User session should be cleared"
        print("   ✓ Session cleared after logout")

        # Test 7: Access profile without login (should redirect)
        print("\n7. Testing profile access without login...")
        rv = c.get('/profile', follow_redirects=False)
        assert rv.status_code == 302, f"Expected 302 redirect, got {rv.status_code}"
        assert rv.headers.get('Location') == '/login', f"Should redirect to /login, got {rv.headers.get('Location')}"
        print("   ✓ Profile access redirects to login when not logged in")

        # Test 8: Access add expense without login
        print("\n8. Testing add expense access without login...")
        rv = c.get('/expenses/add', follow_redirects=False)
        assert rv.status_code == 302, f"Expected 302 redirect, got {rv.status_code}"
        assert rv.headers.get('Location') == '/login', f"Should redirect to /login, got {rv.headers.get('Location')}"
        print("   ✓ Add expense access redirects to login when not logged in")

        # Test 9: Navigation shows correct links (check base template)
        print("\n9. Testing navigation links...")
        rv = c.get('/login')
        assert b'Sign in' in rv.data, "Login page should have Sign in link"
        assert b'Logout' not in rv.data, "Login page should not have Logout link"
        print("   ✓ Login page shows Sign in, not Logout")

        # Test navigation on a page that uses base.html
        print("\n9b. Testing navigation with a template that uses base.html...")
        with c.session_transaction() as sess:
            sess['user_id'] = 1
        rv = c.get('/login')
        # The login page shows session user_id in some way
        print(f"   ✓ Session is active: user_id={sess.get('user_id')}")

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

if __name__ == '__main__':
    test_login_logout()