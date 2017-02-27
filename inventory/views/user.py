from inventory.views.protected import ProtectedModelView
from flask_security import current_user,utils
from wtforms import TextField

class MyPassField(TextField):
    def process_data(self, value):
        self.data = ''  # even if password is already set, don't show hash here
        # or else it will be double-hashed on save
        self.orig_hash = value

    def process_formdata(self, valuelist):
        value = ''
        if valuelist:
            value = valuelist[0]
        if value:
            self.data = utils.encrypt_password(value)
        else:
            self.data = self.orig_hash


class UserAdminView(ProtectedModelView):
    def __init__(self,  *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)

    column_formatters = dict(password=lambda view, column, model, p: model.password[:25] +" (..)")

    form_overrides = dict(
        password=MyPassField,
    )
    form_widget_args = dict(
        password=dict(
            placeholder='Enter new password here to change password',
        ),
    )
    column_list = ("first_name","last_name","email","password","active","roles","confirmed_at")
    column_labels = dict(first_name="Vorname",last_name="Nachname",email="Email",password="Passwort",active="Status",roles="Berechtigungen",confirmed_at="Bestätigt am")