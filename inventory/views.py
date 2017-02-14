"""
TODO:
- Annotations, Comments etc..
- Optimize imports
- Add view for otherdevices (may be generalized with networkdevice)
- Add view for Licenses
"""
from flask import Flask, url_for, redirect, render_template, request, abort, flash
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla.validators import Unique
from flask_admin.model.form import InlineFormAdmin
from flask_admin.actions import action

from flask_security import current_user
from sqlalchemy.sql import func
from wtforms import ValidationError
import gettext
try:
    from wtforms.validators import InputRequired
except ImportError:
    from wtforms.validators import Required as InputRequired
from inventory.models import db, User, Ip, Inventory, Location, Networkdevice, Networkdevicetype, Otherdevice, Otherdevicetype, Role, roles_users
# TODO: may be used for logging "from flask import current_app"
from flask import current_app

# Create customized model view class
class MyModelView(sqla.ModelView):
    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
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


class NetworkdeviceInlineModelForm(InlineFormAdmin):
    form_columns = ('id', 'networkname', 'networkdevicetype', 'mainboard', 'cpu',
                    'ram', "ram_details", 'description', 'ip', "description")

    column_labels = dict(networkname='Netzwerkname', mainboard="Modellbezeichnung/ Mainboard",
                         networkdevicetype='Geräte-Typ',
                         ram="Arbeitsspeicher", ram_details='Arbeitsspeicher Details')
    column_descriptions = dict(
        networkname="Name des Geräts im Netzwerk (gemäß VKM-Policy; Bsp.: Tanja2).",
        networkdevicetype="Art des netwerk-fähigen Gerätes.",
        mainboard="Je nach Typ Herstellerbezeichung/ Baureihe der Hardware (Bsp.: ASUS Z170-A | HP Aruba 2720 | KYOCERA FS1020D | Raspberry v3)",
        ram='Anzahl des zur Verfügung stehenden Arbeitsspeichers in Gigabytes (Bsp.: 8 )',
        ram_details='Format: [S0 bei Notebook-RAM],Chip,Modul,Weiteres (Bsp.: DDR3-2133,PC3-17000,ECC | S0,DDR4-3200,PC4L-25600,nur schnellster Riegel )'
    )


# #column_list = ( Systems.name)
# column_auto_select_related = True

# TODO: can be included from general helpers file; also make sure array index is accessible
class ItemsRequiredExactly(InputRequired):
    """
    A version of the ``InputRequired`` validator that works with relations,
    to require a minimum number of related items.
    """

    def __init__(self, min=1, message=None):
        """

        :param min:
        :param message:
        """
        super(ItemsRequiredExactly, self).__init__(message=message)
        self.min = min

    def __call__(self, form, field):
        """

        :param form:
        :param field:
        """
        if len(field.data) < self.min or len(field.data) > self.min:
            if self.message is None:
                message = field.ngettext(
                    u"Only %d item is allowed!",
                    u"Only least %d items are allowed!",
                    self.min
                ) % self.min
            else:
                message = self.message

            raise ValidationError(message)
        if field.data[0]["networkname"] == None:
            raise ValidationError(str(field.data[0]["networkname"]))


class InventoryNetworkDevicesView(MyModelView):
    inline_models = (NetworkdeviceInlineModelForm(Networkdevice),)
    can_delete = False
    can_export = True
    column_list = (
        "ip",
        "networkname",
        "mac",
        "networkdevicetype_",
        "inventorynumber",
        "responsible_",
        "location_",
        #"active",
        "bought_at",
        "created_at"
    )
    column_labels = dict(
        ip="IP-Adresse", networkname='Netzwerkname',mac="MAC-Adresse" , networkdevicetype_="Geräte-Typ", inventorynumber="Inventarnummer",
        responsible_='Verantwortlicher', location_="Standort", networkdevice='Netzwerfähiges Gerät',
        active='Aktiv', bought_at="Gekauft am", created_at='Erstellt am'
    )
    column_descriptions = dict(
        ip="Die zugeordnete IP-Adresse des Systems.", networkname='Der Computeranmeldename des Gerätes.',
        mac="Die Hardware-Adresse des Haupt-Netzwerkadapters.",
        networkdevicetype_="Typ des netzwerkfähigen Gerätes.",
        inventorynumber="Eindeutige Inventarnummer des Gerätes.",
        responsible_="Der für das Gerät Verantwortliche (Nutzer kann hier nur zugefügt werden, wenn er Berechtigung <verantwortlicher> besitzt).",
        active='Im Inventar vorhanden?', location_="Wo steht die Hardware?", bought_at="Wann wurde das Gerät gekauft?",
        created_at='In System aufgenommen am?'
    )
    form_args = {

        "networkdevice": {  # "default": [{"id":None}],
            "validators": [ItemsRequiredExactly()],
            "min_entries": 1,
            "max_entries": 1
        },
        # "name": {"validators": [InputRequired()]},
        "inventorynumber": {"validators": [InputRequired(), Unique(db.session, Inventory, Inventory.inventorynumber)]}
    }
    #form_widget_args = {
    #    "active": {
    #        'disabled': True
    #    }
    #}

    form_columns = (
        'networkdevice', 'inventorynumber', 'responsible', 'bought_at',
        'location'
    )

    form_excluded_columns = (
        "created_at","active"
    )

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(InventoryNetworkDevicesView, self).__init__(*args, **kwargs)
        if self.endpoint == "inv_network_inactive":
            # Disable creating and deinventorizing for already deinventorized devices
            self.action_disallowed_list = ["deinventorize"]
            self.can_create = False
    # TODO: needed? default sortable is problemativ becauese overriding column_list
    #  column_editable_list = ("id")
    # column_default_sort = (Systems.name)
    # TODO: Allow Ip-Selection from current used ip
    # Override possible drop down values in create form for ip and responsible
    def create_form(self):
        return self._use_filtered_create(
            super(InventoryNetworkDevicesView, self).create_form()
        )

    def _use_filtered_create(self, form):
        form.networkdevice[0].ip.query_factory = self._get_parent_list_ip_create
        form.responsible.query_factory = self._get_parent_list_responsible_create
        return form

    def _get_parent_list_ip_create(self):
        return Ip.query.filter(Ip.networkdevice_id == None).all()

    def _get_parent_list_responsible_create(self):
        return self.session.query(User).join(roles_users).join(Role).filter(Role.name == "responsible").all()

    # Override possible drop down values in edit form for ip and responsible
    def edit_form(self, obj):
        return self._use_filtered_edit(
            super(InventoryNetworkDevicesView, self).edit_form(obj)
        )

    def _use_filtered_edit(self, form):
        self.temp_ip_edit_id = 0
        if len(form.networkdevice) > 0 and form.networkdevice[0].ip.data != None:
            self.temp_ip_edit_id = form.networkdevice[0].ip.data.id # Pretty ugly and fucked up, but there seems to be no other easy way
        #current_app.logger.error(str(form.networkdevice[0].ip.data.id))
        form.networkdevice[0].ip.query_factory = self._get_parent_list_ip_edit
        form.responsible.query_factory = self._get_parent_list_responsible_edit
        return form

    def _get_parent_list_ip_edit(self):
        return Ip.query.filter((Ip.networkdevice_id == None) | (Ip.id == self.temp_ip_edit_id)).all()

    def _get_parent_list_responsible_edit(self):
        return self.session.query(User).join(roles_users).join(Role).filter(Role.name == "responsible").all()


    # TODO: Do an Ip-change History:
    '''def after_model_change(self, form, nd, is_created):
        current_app.logger.info("Form: "+str(form.networkdevice[0].ip.data.id))
        current_app.logger.info("Model: " + str(nd.networkdevice[0].ip.id))'''

    # TODO unicode or to str??
    def __unicode__(self):
        return self.name

    @action('deinventorize', 'Deinventarisieren', 'Sollen die Geräte wirklich deinventarisiert werden?')
    def action_deinventorize(self, ids):
        try:
            ipinfo = ""
            if len(ids) != 1:
                flash("Geräte bitte nur einzeln deinventarisiern, um Fehler zu vermeiden.")
                return
            rows = self.session.query(Inventory).filter(Inventory.id == ids[0]).all() # TODO: replace with self.model.filter ??
            if len(rows) != 1:
                flash("Inventarisiertes Gerät mit id " + str(ids[0]) + " wurde nicht gefunden.")
                return
            inv = rows[0]
            if len(inv.networkdevice) != 1:
                flash("Inventarnummer keinem netwerkfähigen Gerät zugeordnet. Inventory-id: " + str(ids[0]))
                return
            ndev= inv.networkdevice[0]
            if ndev.ip != None:
                # set IP None
                ipinfo = "Die IP-Addresse <" + ndev.ip.address + "> wurde freigegeben."
                ndev.ip.networkdevice_id = None
            # remove from inventory
            inv.active = False
            flash("Gerät mit Inventarnummer <" + str(inv.inventorynumber)+ "> wurde deinventarisiert. " + str(ipinfo))
            self.session.commit()
        except:
            # on rollback, the same closure of state
            # as that of commit proceeds.
            self.session.rollback()
            raise

    def get_query_helper(self, active=1):
        return (
            self.session.query(
                Inventory.id.label("id"),
                (func.IF(Ip.internetaccess > 0, Ip.address, Ip.address + " (nur intern)")).label("ip"),
                Networkdevice.networkname.label("networkname"),
                Networkdevice.mac.label("mac"),
                Networkdevicetype.name.label("networkdevicetype_"),
                Inventory.inventorynumber.label("inventorynumber"),
                (User.email + " " + User.first_name).label("responsible_"),
                # User.email.label("email"),
                (Location.building + " " + Location.room + " " + Location.description).label("location_"),
                Inventory.bought_at.label("bought_at"),
                Inventory.created_at.label("created_at")
            )
                .join(Networkdevice).outerjoin(Networkdevicetype).outerjoin(Ip).outerjoin(User).outerjoin(Location).filter(Inventory.active == active)
        )


    def get_query(self):
        if self.endpoint == "inv_network_active":
            return self.get_query_helper(1)
        elif self.endpoint == "inv_network_inactive":
            return self.get_query_helper(0)



    def get_count_query(self):
        if self.endpoint == "inv_network_active":
            return (
                self.session.query(func.count('*')).select_from(self.model).join(Networkdevice).filter(
                    Inventory.active == 1)
            )
        elif self.endpoint == "inv_network_inactive":
            return (
                self.session.query(func.count('*')).select_from(self.model).join(Networkdevice).filter(
                    Inventory.active == 0)
            )


    # TODO: Add needed sortable colums (Bug current stable with ids!! --> upgrade flask_admin over ???)
    def scaffold_sortable_columns(self):
        return {'networkname': 'networkname',
                'inventorynumber': 'inventorynumber',
                'typ': 'typ'}

    # TODO: see one above
    def scaffold_list_columns(self):
        """

        :return:
        """
        return ['id',
                'inventorynumber',
                'typ',
                'networkname']


class OtherdeviceInlineModelForm(InlineFormAdmin):
    form_columns = ('id', 'otherdevicetype', 'vendor', 'model',
                    'details',"description")
    column_labels = dict(otherdevicetype='Geräte-Typ', vendor="Hersteller",
                         model="Modell", details='Details', description='Anmerkung')
    column_descriptions = dict(
        otherdevicetype="Art des netwerk-fähigen Gerätes.",
        vendor="Je nach Typ Herstellerbezeichung/ Baureihe der Hardware (Bsp.: ASUS Z170-A | HP Aruba 2720 | KYOCERA FS1020D | Raspberry v3)",
        model='Anzahl des zur Verfügung stehenden Arbeitsspeichers in Gigabytes (Bsp.: 8 )',
        details='Format: [S0 bei Notebook-RAM],Chip,Modul,Weiteres (Bsp.: DDR3-2133,PC3-17000,ECC | S0,DDR4-3200,PC4L-25600,nur schnellster Riegel )',
        description='Format: [S0 bei Notebook-RAM],Chip,Modul,Weiteres (Bsp.: DDR3-2133,PC3-17000,ECC | S0,DDR4-3200,PC4L-25600,nur schnellster Riegel )'
    )


class InventoryOtherDevicesView(MyModelView):
    inline_models = (OtherdeviceInlineModelForm(Otherdevice),)
    can_delete = False
    can_export = True
    column_list = (
        "otherdevicetype_",
        "inventorynumber",
        "responsible_",
        "location_",
        #"active",
        "bought_at",
        "created_at"
    )
    column_labels = dict(
        otherdevicetype_="Geräte-Typ",
        responsible_='Verantwortlicher', location_="Standort", otherdevice='Netzwerfähiges Gerät',
        active='Aktiv', bought_at="Gekauft am", created_at='Erstellt am'
    )
    column_descriptions = dict(
        otherdevicetype_="Typ des Gerätes.",
        inventorynumber="Eindeutige Inventarnummer des Gerätes.",
        responsible_="Der für das Gerät Verantwortliche (Nutzer kann hier nur zugefügt werden, wenn er Berechtigung <verantwortlicher> besitzt).",
        active='Im Inventar vorhanden?', location_="Wo steht die Hardware?", bought_at="Wann wurde das Gerät gekauft?",
        created_at='In System aufgenommen am?'
    )
    form_args = {
        "otherdevice": {
            "validators": [ItemsRequiredExactly()],
            "min_entries": 1,
            "max_entries": 1
        },
        # "name": {"validators": [InputRequired()]},
        "inventorynumber": {"validators": [InputRequired(), Unique(db.session, Inventory, Inventory.inventorynumber)]}
    }
    #form_widget_args = {
    #    "active": {
    #        'disabled': True
    #    }
    #}

    form_columns = (
        'otherdevice', 'inventorynumber', 'responsible', 'bought_at',
        'location'
    )

    form_excluded_columns = (
        "created_at","active"
    )

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(InventoryOtherDevicesView, self).__init__(*args, **kwargs)
        if self.endpoint == "inv_other_inactive":
            # Disable creating and deinventorizing for already deinventorized devices
            self.action_disallowed_list = ["deinventorize"]
            self.can_create = False

    # TODO unicode or to str??
    def __unicode__(self):
        return self.name

    @action('deinventorize', 'Deinventarisieren', 'Sollen die Geräte wirklich deinventarisiert werden?')
    def action_deinventorize(self, ids):
        try:
            if len(ids) != 1:
                flash("Geräte bitte nur einzeln deinventarisiern, um Fehler zu vermeiden.")
                return
            rows = self.session.query(Inventory).filter(Inventory.id == ids[0]).all()
            if len(rows) != 1:
                flash("Inventarisiertes Gerät mit id " + str(ids[0]) + " wurde nicht gefunden.")
                return
            inv = rows[0]
            if len(inv.otherdevice) != 1:
                flash("Inventarnummer keinem Gerät zugeordnet. Inventory-id: " + str(ids[0]))
                return
            # remove from inventory
            inv.active = False
            flash("Gerät mit Inventarnummer <" + str(inv.inventorynumber)+ "> wurde deinventarisiert. ")
            self.session.commit()
        except:
            # on rollback, the same closure of state
            # as that of commit proceeds.
            self.session.rollback()
            raise

    def get_query_helper(self, active=1):
        return (
            self.session.query(
                Inventory.id.label("id"),
                Otherdevicetype.name.label("otherdevicetype_"),
                Inventory.inventorynumber.label("inventorynumber"),
                (User.email + " " + User.first_name).label("responsible_"),
                (Location.building + " " + Location.room + " " + Location.description).label("location_"),
                Inventory.bought_at.label("bought_at"),
                Inventory.created_at.label("created_at")
            ).join(Otherdevice).outerjoin(Otherdevicetype).outerjoin(User).outerjoin(Location).filter(Inventory.active == active)
        )


    def get_query(self):
        if self.endpoint == "inv_other_active":
            return self.get_query_helper(1)
        elif self.endpoint == "inv_other_inactive":
            return self.get_query_helper(0)


    def get_count_query(self):
        if self.endpoint == "inv_other_active":
            return (
                self.session.query(func.count('*')).select_from(self.model).join(Otherdevice).filter(Inventory.active == 1)
            )
        elif self.endpoint == "inv_other_inactive":
            return (
                self.session.query(func.count('*')).select_from(self.model).join(Otherdevice).filter(Inventory.active == 0)
            )


    # TODO: Add needed sortable colums (Bug current stable with ids!! --> upgrade flask_admin over ???)
    def scaffold_sortable_columns(self):
        return {'networkname': 'networkname',
                'inventorynumber': 'inventorynumber',
                'typ': 'typ'}

    # TODO: see one above
    def scaffold_list_columns(self):
        """

        :return:
        """
        return ['id',
                'inventorynumber',
                'typ',
                'networkname']


class IpAddressesView(MyModelView):
    # Variables for view
    can_export = True
    # Set flags for readonly views
    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(IpAddressesView, self).__init__(*args, **kwargs)
        if self.endpoint != "ip":
            self.can_create = False
            self.can_delete = False
            self.can_edit = False

    def get_query(self):
        """

        :return:
        """
        if self.endpoint == "ip_free":
            return super(MyModelView, self).get_query().filter(self.model.networkdevice_id == None)
        elif self.endpoint == "ip_notfree":
            return super(MyModelView, self).get_query().filter(self.model.networkdevice_id != None)
        else:
            return super(MyModelView, self).get_query()


    def get_count_query(self):
        """

        :return:
        """
        if self.endpoint == "ip_free":
            return (
                self.session.query(func.count('*')).filter(self.model.networkdevice_id == None)
            )
        elif self.endpoint == "ip_notfree":
            return (
                self.session.query(func.count('*')).filter(self.model.networkdevice_id != None)
            )
        else:
            return super(MyModelView, self).get_count_query()