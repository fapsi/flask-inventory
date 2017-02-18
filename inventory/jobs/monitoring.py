import datetime
from inventory.models import Ip
from inventory.app import app,db
from platform import system as system_name
from os import system as system_call


def ping_job():
    with app.app_context():
        try:
            # db.session.flush()
            datetime_now = datetime.datetime.now()
            for ip in db.session.query(Ip).with_for_update():
                if ping(ip.address):
                    ip.lastseen_at = datetime_now
            db.session.commit()
        except:
            # on rollback, the same closure of state
            # as that of commit proceeds.
            db.session.rollback()
            raise
        db.session.close()


def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that some hosts may not respond to a ping request even if the host name is valid.
    """

    # Ping parameters as function of OS
    ping_param = "-n 1" if system_name().lower()=="windows" else "-c 1"

    # Pinging
    return system_call("ping " + ping_param + " " + host) == 0