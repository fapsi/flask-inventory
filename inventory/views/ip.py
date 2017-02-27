from inventory.views.protected import ProtectedModelView
from sqlalchemy.sql import func

class IpAddressesView(ProtectedModelView):
    # Variables for view
    can_export = True
    # Set flags for readonly views
    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        if self.endpoint != "ip":
            self.can_create = False
            self.can_delete = False
            self.can_edit = False

    def get_query(self):
        """

        :return:
        """
        if self.endpoint == "ip_free":
            return super().get_query().filter(self.model.networkdevice_id == None)
        elif self.endpoint == "ip_notfree":
            return super().get_query().filter(self.model.networkdevice_id != None)
        else:
            return super().get_query()


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
            return super().get_count_query()