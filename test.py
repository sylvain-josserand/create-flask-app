import shutil
import unittest
from pathlib import Path
from unittest.mock import patch


class TestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app

        self.app = create_app(
            {
                "TESTING": True,
                "DATA_DIR": Path("test_data"),
            }
        )
        self.client = self.app.test_client()
        import migrate

        migrate.run()

    def tearDown(self):
        shutil.rmtree(self.app.config["DATA_DIR"])

    def _test_guest_access(self):
        """Test guest access"""
        from db.models.auth.account import Account
        from db.models.auth.user import User

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<h1>Hi, Guest!</h1>", response.text)
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/signup")
        self.assertEqual(response.status_code, 200)
        self.guest_user = User.select(name="Guest")[0]
        self.guest_account = Account.select(name="Personal")[0]

    def _test_signup(self):
        """Test the signup process"""
        response = self.client.post(
            "/signup",
            data=dict(
                name="test",
                email="test@example.com",
                password="toto",
                password2="toto",
            ),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302, response.text)
        self.assertEqual(response.location, "/")
        # Follow the redirect manually
        response = self.client.get(response.location)
        self.assertEqual(response.status_code, 200)
        self.assertIn("<h1>Hi, test!</h1>", response.text)

    def _test_signup_user_exists(self):
        """Test the signup process"""
        response = self.client.post(
            "/signup",
            data=dict(
                name="test",
                email="test@example.com",
                password="toto",
                password2="toto",
            ),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("A user with that email already exists.", response.text)

    def _test_signup_missing_data(self):
        """Test the signup process"""
        response = self.client.post(
            "/signup",
            data=dict(),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Please enter a name", response.text)
        self.assertIn("Please enter a valid email address", response.text)
        self.assertIn("Please enter a password in the first password field", response.text)
        self.assertIn("Please enter a password in the second password field", response.text)

    def _signup_passwords_dont_match(self):
        """Test the signup process"""
        response = self.client.post(
            "/signup",
            data=dict(
                name="test",
                email="test@localhost",
                password="toto",
                password2="totoo",
            ),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Passwords don&#39;t match", response.text)

    def _test_logout(self):
        """Test the logout process"""
        response = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")
        # Follow the redirect manually
        response = self.client.get(response.location)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Logged out", response.text)

    def _test_login_wrong_email(self):
        """Test the login process with an unknown user"""
        response = self.client.post(
            "/login",
            data=dict(
                email="test@example.comu",
                password="toto",
            ),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("No such user", response.text)

    def _test_login_wrong_password(self):
        """Test the login process with the wrong password"""
        response = self.client.post(
            "/login",
            data=dict(
                email="test@example.com",
                password="totoo",
            ),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Incorrect password", response.text)

    def _test_login_missing_data(self):
        """Test the login process when all required data is missing"""
        response = self.client.post(
            "/login",
            data=dict(),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Please enter a valid email address", response.text)
        self.assertIn("Please enter a password", response.text)

    def _test_login(self):
        """Test the login process"""
        response = self.client.post(
            "/login",
            data=dict(
                email="test@example.com",
                password="toto",
            ),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")
        # Follow the redirect manually
        response = self.client.get(response.location)
        self.assertEqual(response.status_code, 200)

    def _test_create_account(self):
        """Test the create account process"""
        from db.models.auth.account import Account

        response = self.client.post(
            "/account_create",
            data=dict(
                name="Company A",
            ),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/profile")
        # Follow the redirect manually
        response = self.client.get(response.location)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Account created successfully!", response.text)
        self.company_a = Account.select(name="Company A")[0]

    def _test_invite_user(self):
        """Test the invite user process"""
        from db.models.auth.invitation import Invitation

        with patch("blueprints.email.SendGridAPIClient") as mock_send_email:
            response = self.client.post(
                f"/account/{self.company_a.id}/invite",
                data=dict(
                    email="invitee@localhost",
                    role="user",
                ),
                follow_redirects=False,
            )
        mock_send_email.assert_called_once()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/profile")
        # Follow the redirect manually
        response = self.client.get(response.location)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Invitation sent successfully!", response.text)
        self.assertEqual(Invitation.count(), 1)

    def _test_accept_invitation(self, action):
        """Test the accept invitation process leading to action (login or signup)"""
        from db.models.auth.invitation import Invitation
        from db.models.auth.user_account import UserAccount
        from db.models.auth.user import User

        invitation = Invitation.select(email="invitee@localhost")[0]
        response = self.client.get(
            f"/invitation/{invitation.secret}",
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/invitation_accept",
            data=dict(
                invitation_secret=invitation.secret,
            ),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.startswith(f"/{action}?invitation_secret="))
        # Follow the redirect manually
        response = self.client.get(response.location)
        self.assertEqual(response.status_code, 200)
        # Fill up the form, and submit it
        response = self.client.post(
            f"/{action}",
            data=dict(
                name="Invitee",
                email="invitee@localhost",
                password="toto",
                password2="toto",
                invitation_secret=invitation.secret,
            ),
            follow_redirects=False,
        )
        self.invitee = User.select(email="invitee@localhost")[0]
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")
        # Follow the redirect manually
        response = self.client.get(response.location)
        self.assertEqual(response.status_code, 200)
        if action == "signup":
            self.assertIn("Account created. Welcome!", response.text)
        self.assertIn("Invitation accepted. Welcome to the team!", response.text)
        self.assertEqual(User.count(email="invitee@localhost"), 1)
        self.company_a_invitee_user_account = UserAccount.select(user_id=self.invitee.id, account_id=self.company_a.id)[
            0
        ]

    def _test_accept_invitation_signup(self):
        """Test the accept invitation process leading to signup"""
        return self._test_accept_invitation("signup")

    def _test_accept_invitation_login(self):
        """Test the accept invitation process leading to login"""
        return self._test_accept_invitation("login")

    def _test_give_admin_rights(self):
        """Test the give admin rights process"""
        response = self.client.post(
            f"/user_account/{self.company_a_invitee_user_account.id}/update",
            data=dict(
                role="admin",
            ),
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/profile")
        # Follow the redirect manually
        response = self.client.get(response.location)
        self.assertEqual(response.status_code, 200)
        self.assertIn("User account updated successfully!", response.text)

    def _test_delete_account_fail_not_admin(self):
        """Test the delete account process security"""
        response = self.client.post(
            f"/account/{self.company_a.id}/delete",
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/profile")
        # Follow the redirect manually
        response = self.client.get(response.location)
        self.assertIn(
            "You don&#39;t have permission to edit this account. You must be admin to delete an account",
            response.text,
        )

    def _test_delete_account_success(self):
        """Test the delete account process security"""
        response = self.client.post(
            f"/account/{self.company_a.id}/delete",
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/profile")
        # Follow the redirect manually
        response = self.client.get(response.location)
        self.assertIn("Account deleted successfully!", response.text)

    def test_integration(self):
        """Run all subtests one after the other"""
        with self.subTest("Test guest access"):
            self._test_guest_access()
        with self.subTest("Sign up"):
            self._test_signup()
        with self.subTest("Fail to sign up with existing user"):
            self._test_signup_user_exists()
        with self.subTest("Log out"):
            self._test_logout()
        with self.subTest("Fail to sign up with existing user again, after logout"):
            self._test_signup_user_exists()
        with self.subTest("Fail to sign up with missing data"):
            self._test_signup_missing_data()
        with self.subTest("Fail to sign up with passwords that don't match"):
            self._signup_passwords_dont_match()
        with self.subTest("Fail to log in with unknown user"):
            self._test_login_wrong_email()
        with self.subTest("Fail to log in with wrong password"):
            self._test_login_wrong_password()
        with self.subTest("Fail to log in with no data"):
            self._test_login_missing_data()
        with self.subTest("Successful log in"):
            self._test_login()
        with self.subTest("Create account"):
            self._test_create_account()
        with self.subTest("Invite user"):
            self._test_invite_user()
        with self.subTest("Accept invitation: sign up"):
            self._test_accept_invitation_signup()
        with self.subTest("Delete account and fail because not admin"):
            self._test_delete_account_fail_not_admin()
        with self.subTest("Log in with the admin user"):
            self._test_login()
        with self.subTest("Delete account and succeed"):
            self._test_delete_account_success()
        with self.subTest("Create the account again"):
            self._test_create_account()
        with self.subTest("Invite the user again"):
            self._test_invite_user()
        with self.subTest("Accept invitation again, but no need to signup: just login this time"):
            self._test_accept_invitation_login()
        with self.subTest("Log out"):
            self._test_logout()
        with self.subTest("Log in with the admin user"):
            self._test_login()
        with self.subTest("Give admin right to the invitee"):
            self._test_give_admin_rights()


if __name__ == "__main__":
    unittest.main()
