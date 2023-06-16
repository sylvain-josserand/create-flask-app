import secrets

import flask
from flask import flash, render_template, g

from db.models.auth.auth_model import AuthModel

app = flask.current_app


class Invitation(AuthModel):
    table_name = "invitation"
    fields = ("id", "secret", "email", "created_by", "account_id", "role", "status", "created")

    @property
    def inviter(self):
        """Return the user that sent the invitation."""
        from db.models.auth.user import User

        return User.get_by_id(self.created_by)

    @property
    def account(self):
        """Return the account that the invitation is for."""
        from db.models.auth.account import Account

        return Account.get_by_id(self.account_id)

    @classmethod
    def insert(cls, **fields):
        if "secret" not in fields:
            # Generate a secret if none is provided
            fields["secret"] = secrets.token_hex(64)
        return super().insert(**fields)

    @classmethod
    def get_by_secret(cls, secret):
        for invitation in cls.select(secret=secret):
            return invitation
        return None

    @classmethod
    def render_template(cls, template_name, invitation_secret):
        invitation = Invitation.get_by_secret(invitation_secret)
        if not invitation:
            flash("Invitation not found.")
            return render_template(template_name)
        return render_template(template_name, email=invitation.email, invitation_secret=invitation_secret)

    def accept(self, user):
        from db.models.auth.account import Account
        from db.models.auth.user_account import UserAccount

        account = Account.get_by_id(self.account_id)
        errors = []
        if not account:
            errors.append("Invalid invitation, the account you've been invited to join doesn't exist anymore")

        # Let's check if the freshly created user is the one who was invited
        if self.email != user.email:
            errors.append("The email from the invitation doesn't match the one you just signed up with.")

        # Check if the user is already a member of the account
        if UserAccount.select(user_id=user.id, account_id=account.id):
            errors.append("You're already a member of this account")

        # Check if the invitation was already accepted or declined
        if self.status == "accepted":
            errors.append("This invitation has already been accepted")
        elif self.status == "declined":
            errors.append("This invitation has already been declined")

        if errors:
            for error_message in errors:
                flash(error_message)
            return False
        else:
            # Add the user to the account
            UserAccount.insert(user_id=g.user.id, account_id=account.id, role=self.role)

        self.update(status="accepted")
        flash("Invitation accepted. Welcome to the team! 🎉")
        return True
