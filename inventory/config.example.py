# Turns on debugging features in Flask
DEBUG = True
SERVER_NAME = "127.0.0.1:8080"

# Create dummy secrey key so we can use sessions
SECRET_KEY = '123456790'

# Create in-memory database
SQLALCHEMY_DATABASE_URI = 'mysql://:@localhost/inventory'
SQLALCHEMY_ECHO = True

# Flask-mail
MAIL_SERVER = ''
MAIL_PORT = 465
MAIL_USE_SSL= True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''

# Flask-Security config
SECURITY_URL_PREFIX = "/admin"
SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
SECURITY_PASSWORD_SALT = "ATGUOHAELKiubahiughaerGOJAEGj"

# Flask-Security URLs, overridden because they don't put a / at the end
SECURITY_LOGIN_URL = "/login/"
SECURITY_LOGOUT_URL = "/logout/"
SECURITY_REGISTER_URL = "/register/"
SECURITY_RESET_URL = "/reset/"

SECURITY_POST_LOGIN_VIEW = "/admin/"
SECURITY_POST_LOGOUT_VIEW = "/admin/"
SECURITY_POST_REGISTER_VIEW = "/admin/"
SECURITY_POST_RESET_VIEW = "/admin/"

# Flask-Security features
SECURITY_REGISTERABLE = True
SECURITY_RECOVERABLE = True
SECURITY_SEND_REGISTER_EMAIL = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
CSRF_ENABLED = True

# Flask-Login
# SESSION_PROTECTION = None

# Flask-APScheduler
SCHEDULER_API_ENABLED = True
JOBS = [
        {
            'id': 'monitoring_ping_job',
            'func': 'inventory.app:ping_job',
            'args': (),
            'trigger': 'interval',
            'seconds': 30
        }
]


