import flask_admin, flask_wtf, os
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_admin import helpers as admin_helpers
from flask_security import Security, SQLAlchemyUserDatastore, current_user

from flask_mail import Mail
from inventory.models import db, User, Role, Ip, Inventory, Location, Networkdevice, Otherdevice, Networkdevicetype, Otherdevicetype
from inventory.views.protected import ProtectedModelView
from inventory.views.ip import IpAddressesView
from inventory.views.user import UserAdminView
from inventory.views.register import ExtendedRegisterForm
from inventory.views.networkdevice import InventoryNetworkDevicesView
from inventory.views.otherdevice import InventoryOtherDevicesView

from flask_apscheduler import APScheduler
#from inventory.jobs.job1 import job1

# Create Flask application
app = Flask(__name__)
# Load configuration stuff
app.config.from_pyfile('config.py')
# Connect app with db
db.init_app(app)

mail = Mail(app)

flask_wtf.CSRFProtect(app)



# Setup Flask-Security


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, register_form = ExtendedRegisterForm)

# Setup IP-Monitoring Job
from inventory.jobs.monitoring import ping_job  # important: Not delete, needed to import the in the config file specified job
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true': # Prevent second execution of job in debug-mode
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

# Flask views
@app.route('/')
def index():
    return render_template('index.html')



# Create admin
admin = flask_admin.Admin(
    app,
    'VKM: IT-Inventar',
    base_template='mybase.html',
    template_mode='bootstrap3'
)

# Add model views
admin.add_view(UserAdminView(User, db.session, name='Benutzer/Verantwortliche', category='Nutzerverwaltung'))
admin.add_view(ProtectedModelView(Role, db.session, name='Berechtigungen', category='Nutzerverwaltung'))

admin.add_view(IpAddressesView(Ip, db.session, category='Ip-Addressverwaltung', name='Alle IPs', endpoint='ip_all'))
admin.add_view(IpAddressesView(Ip, db.session, category='Ip-Addressverwaltung', name='Freie IPs', endpoint='ip_free'))
admin.add_view(IpAddressesView(Ip, db.session, category='Ip-Addressverwaltung', name='Belegte IPs', endpoint='ip_notfree'))

admin.add_view(IpAddressesView(Ip, db.session, category='Lizenzen', name='Alle Softwarelizenzen', endpoint='todo3'))  # TODO

admin.add_view(InventoryNetworkDevicesView(Inventory, db.session, endpoint='inv_network_active', category='Inventar',name='Netzwerkfähige Geräte'))
admin.add_view(InventoryOtherDevicesView(Inventory, db.session, endpoint='inv_other_active', category='Inventar',name='Andere inventarisierte Geräte')) #TODO
admin.add_view(InventoryNetworkDevicesView(Inventory, db.session, endpoint='inv_network_inactive', category='Inventar',name='Netzwerkfähige Geräte (ausgemustert)'))
admin.add_view(InventoryOtherDevicesView(Inventory, db.session, endpoint='inv_other_inactive', category='Inventar',name='Andere inventarisierte Geräte (ausgemustert)')) #TODO

admin.add_view(ProtectedModelView(Inventory, db.session, category='Erweitert', name='Alle Inventarnummern (ohne zugeordnete Geräte)'))
admin.add_view(ProtectedModelView(Networkdevice, db.session, category='Erweitert', name='Netzwerkfähige Geräte (ohne Inventarnummer)'))
admin.add_view(ProtectedModelView(Otherdevice, db.session, category='Erweitert', name='Andere Geräte (ohne Inventarnummer)'))
admin.add_view(ProtectedModelView(Networkdevicetype, db.session, category='Erweitert', name='Typen netzwerkfähiger Geräte'))
admin.add_view(ProtectedModelView(Otherdevicetype, db.session, category='Erweitert', name='Typen anderer Geräte'))
admin.add_view(ProtectedModelView(Location, db.session, category='Erweitert', name='Verfügbare Standorte'))
admin.add_view(ProtectedModelView(Ip, db.session, category='Erweitert', name='Verfügbare IPs'))



# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )
