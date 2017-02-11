import flask_admin
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_admin import helpers as admin_helpers
from flask_security import Security, SQLAlchemyUserDatastore, current_user

from inventory.models import db, User, Role, Ip, Inventory, Location, Networkdevice, Otherdevice, Networkdevicetype, Otherdevicetype
from inventory.views import MyModelView, InventoryNetworkDevicesView, IpAddressesView

# Create Flask application
app = Flask(__name__)
# Load configuration stuff
app.config.from_pyfile('config.py')
# Connect app with db
db.init_app(app)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Flask views
@app.route('/')
def index():
    return render_template('index.html')

# Create admin
admin = flask_admin.Admin(
    app,
    'VKM: IT-Inventar',
    base_template='my_master.html',
    template_mode='bootstrap3',
)

# Add model views
admin.add_view(MyModelView(User, db.session, category='Nutzerverwaltung', name='Benutzer/Verantwortliche'))
admin.add_view(MyModelView(Role, db.session, category='Nutzerverwaltung', name='Berechtigungen'))

admin.add_view(IpAddressesView(Ip, db.session, category='Ip-Addressverwaltung', name='Alle IPs', endpoint='ip_all'))
admin.add_view(IpAddressesView(Ip, db.session, category='Ip-Addressverwaltung', name='Freie IPs', endpoint='ip_free'))
admin.add_view(IpAddressesView(Ip, db.session, category='Ip-Addressverwaltung', name='Belegte IPs', endpoint='ip_notfree'))

admin.add_view(IpAddressesView(Ip, db.session, category='Lizenzen', name='Alle Softwarelizenzen', endpoint='todo3'))  # TODO

admin.add_view(InventoryNetworkDevicesView(Inventory, db.session, endpoint='inv', category='Inventar',name='Netzwerkfähige Geräte'))
admin.add_view(InventoryNetworkDevicesView(Inventory, db.session, endpoint='todo', category='Inventar',name='Andere inventarisierte Geräte')) #TODO

admin.add_view(MyModelView(Inventory, db.session, category='Erweitert', name='Alle Inventarnummern (ohne zugeordnete Geräte)'))
admin.add_view(MyModelView(Networkdevice, db.session, category='Erweitert', name='Netzwerkfähige Geräte (ohne Inventarnummer)'))
admin.add_view(MyModelView(Otherdevice, db.session, category='Erweitert', name='Andere Geräte (ohne Inventarnummer)'))
admin.add_view(MyModelView(Networkdevicetype, db.session, category='Erweitert', name='Typen netzwerkfähiger Geräte'))
admin.add_view(MyModelView(Otherdevicetype, db.session, category='Erweitert', name='Typen anderer Geräte'))
admin.add_view(MyModelView(Location, db.session, category='Erweitert', name='Verfügbare Standorte'))
admin.add_view(MyModelView(Ip, db.session, category='Erweitert', name='Verfügbare IPs'))

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
