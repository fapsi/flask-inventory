from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin

db = SQLAlchemy()

# Define models
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email


class Ip(db.Model):
    __tablename__ = 'ip'
    id = db.Column(db.Integer(), primary_key=True)
    address = db.Column(db.String(15), default="0.0.0.0")
    internetaccess = db.Column(db.Boolean(), default=True)
    networkdevice_id = db.Column(db.Integer, db.ForeignKey("networkdevice.id"))
    used_by = db.relationship("Networkdevice", backref=db.backref(
        'ip', uselist=False, cascade="all, delete-orphan", single_parent=True))
    lastseen_at = db.Column(db.DateTime())

    def __str__(self):
        if self.internetaccess:
            return self.address
        return self.address + " (nur intern)"


class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer(), primary_key=True)
    building = db.Column(db.String(45), default="L1|01")
    room = db.Column(db.String(45), default="")
    description = db.Column(db.String, default="")

    def __str__(self):
        return self.building + " " + self.room + " " + self.description


class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer(), primary_key=True)
    inventorynumber = db.Column(db.String(45))

    responsible_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    responsible = db.relationship(User, backref=db.backref(
        'netzwerkfähige Geräte', uselist=False, cascade="all, delete-orphan", single_parent=True))
    bought_at = db.Column(db.Date())
    created_at = db.Column(db.DateTime())
    active = db.Column(db.Boolean(), default=True)
    location_id = db.Column(db.Integer(), db.ForeignKey("location.id"))
    location = db.relationship(Location, backref=db.backref('TODO'))

    def __str__(self):
        return self.inventorynumber


class Networkdevicetype(db.Model):
    __tablename__ = 'networkdevicetype'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(45))
    description = db.Column(db.String(45))

    def __str__(self):
        return self.name


class Networkdevice(db.Model):
    __tablename__ = 'networkdevice'
    id = db.Column(db.Integer, primary_key=True)
    networkname = db.Column(db.String(45))

    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"))
    inventory = db.relationship(Inventory, backref=db.backref('networkdevice',
                                                              cascade="all, delete-orphan", single_parent=True))  # ))

    networkdevicetype_id = db.Column(db.Integer, db.ForeignKey("networkdevicetype.id"))
    networkdevicetype = db.relationship(Networkdevicetype, backref=db.backref(
        'networkdevice', uselist=False, cascade="all, delete-orphan", single_parent=True))  # ))

    cpu = db.Column(db.String(45))
    ram = db.Column(db.String(45))
    ram_details = db.Column(db.String(45))
    mainboard = db.Column(db.String(45))
    description = db.Column(db.String(45))

    def __str__(self):
        return self.networkname


class Otherdevicetype(db.Model):
    __tablename__ = 'otherdevicetype'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(45))

    def __str__(self):
        return self.name


class Otherdevice(db.Model):
    __tablename__ = 'otherdevice'
    id = db.Column(db.Integer, primary_key=True)

    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"))
    inventory = db.relationship(Inventory, backref=db.backref('otherdevice',
                                                              cascade="all, delete-orphan", single_parent=True))  # ))

    otherdevicetype_id = db.Column(db.Integer, db.ForeignKey("otherdevicetype.id"))
    otherdevicetype = db.relationship(Otherdevicetype, backref=db.backref(
        'otherdevice', uselist=False, cascade="all, delete-orphan", single_parent=True))  # ))

    vendor = db.Column(db.String(45))
    model = db.Column(db.String(45))
    details = db.Column(db.String(45))
    description = db.Column(db.String(45))

    def __str__(self):
        return self.networkname
