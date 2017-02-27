from flask_security.forms import RegisterForm, Required, StringField

class ExtendedRegisterForm(RegisterForm):
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

    first_name = StringField(label="Vorname", id="first_name", validators=[Required()])
    last_name = StringField(label="Nachname", id="last_name", validators=[Required()])