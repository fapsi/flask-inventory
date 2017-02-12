"""
TODO:
- Annotations, Comments etc..
- Optimize imports
- Add view for otherdevices (may be generalized with networkdevice)
- Add view for Licenses
"""
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla.validators import Unique
from flask_admin.model.form import InlineFormAdmin
from flask_security import current_user
from sqlalchemy.sql import func
from wtforms import ValidationError

try:
    from wtforms.validators import InputRequired
except ImportError:
    from wtforms.validators import Required as InputRequired
from inventory.models import db, User, Ip, Inventory, Location, Networkdevice, Networkdevicetype
# TODO: may be used for logging "from flask import current_app"


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

    form_args = {
        "networkdevice": {  # "default": [{"id":None}],
            "validators": [ItemsRequiredExactly()],
            "min_entries": 1,
            "max_entries": 1
        },
        # "name": {"validators": [InputRequired()]},
        "inventorynumber": {"validators": [InputRequired(), Unique(db.session, Inventory, Inventory.inventorynumber)]}
    }
    form_columns = (
        'networkdevice', 'inventorynumber', 'responsible', 'bought_at',
        'location', "active", "created_at"
    )
    column_labels = dict(
        inventorynumber="Inventarnummer", networkdevice='Netzwerfähiges Gerät', responsible='Verantwortlicher',
        bought_at="Gekauft am",
        location="Standort", active='Aktiv', created_at='Erstellt am'
    )
    column_descriptions = dict(
        inventorynumber="TODO", networkname='TODO', responsible='TODO',
        bought_at="TODO", location="TODO", active='TODO', created_at='TODO'
    )
    column_list = (
        #        "id",
        "ip",
        "networkname",
        "inventorynumber",
        "verantwortlicher",
        "typ",
        "Standort",
        "bought_at"
    )
    form_excluded_columns = (
        "created_at"
    )
    # TODO: needed? default sortable is problemativ becauese overriding column_list
    #  column_editable_list = ("id")
    # column_default_sort = (Systems.name)
    # TODO filter for ajax ip-requests
    '''     def create_form(self):
        return self._use_filtered_parent2(
            super(InventoryNetworkDevicesView, self).create_form()
        )

    def edit_form(self, obj):
        return self._use_filtered_parent(
            super(InventoryNetworkDevicesView, self).edit_form(obj)
        )

    def _use_filtered_parent(self, form):
        form.networkdevice[0].ip.query_factory = self._get_parent_list
        return form

    def _get_parent_list(self):
        return Ip.query.filter((Ip.networkdevice_id == None) | (Ip.networkdevice_id == Networkdevice.id)).all()

    def _use_filtered_parent2(self, form):
        form.networkdevice[0].ip.query_factory = self._get_parent_list2
        return form

    def _get_parent_list2(self):
        return Ip.query.filter(Ip.networkdevice_id == None).all()'''
    # TODO: Do an Ip-change History:
    '''def after_model_change(self, form, nd, is_created):
        current_app.logger.info("Form: "+str(form.networkdevice[0].ip.data.id))
        current_app.logger.info("Model: " + str(nd.networkdevice[0].ip.id))'''

    # TODO unicode or to str??
    def __unicode__(self):
        return self.name

    def get_query(self):
        return (
            self.session.query(
                Inventory.id.label("id"),
                (func.IF(Ip.internetaccess > 0, Ip.address, Ip.address + " (nur intern)")).label("ip"),
                Networkdevice.networkname.label("networkname"),
                Networkdevicetype.name.label("typ"),
                Inventory.inventorynumber.label("inventorynumber"),
                (User.email + " " + User.first_name).label("verantwortlicher"),
                # User.email.label("email"),
                (Location.building + " " + Location.room + " " + Location.description).label("Standort"),
                Inventory.bought_at.label("bought_at")
            )
                .outerjoin(Networkdevice).outerjoin(Networkdevicetype).outerjoin(Ip).outerjoin(User).outerjoin(Location)
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
            return super(MyModelView, self).get_query().filter(Ip.networkdevice_id.is_(None))
        elif self.endpoint == "ip_notfree":
            return super(MyModelView, self).get_query().filter(Ip.networkdevice_id.isnot(None))
        else:
            return super(MyModelView, self).get_query()
