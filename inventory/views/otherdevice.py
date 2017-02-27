from inventory.views.protected import ProtectedModelView
from inventory.models import db, User, Inventory, Location, Otherdevice, Otherdevicetype
from inventory.helpers import ItemsRequiredExactly
from flask import flash
from flask_admin.model.form import InlineFormAdmin
from flask_admin.contrib.sqla.validators import Unique
from flask_admin.actions import action
from sqlalchemy.sql import func
from wtforms.validators import InputRequired

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


class InventoryOtherDevicesView(ProtectedModelView):
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
        super().__init__(*args, **kwargs)
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




