from flask import Flask, url_for, redirect, render_template, request, abort, flash
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user


# Create customized model view class
class ProtectedModelView(ModelView):
    def __init__(self,  *args, required_roles = ['superuser'], **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.required_roles = required_roles

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        for role in self.required_roles:
            if current_user.has_role(role):
                return True
        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))