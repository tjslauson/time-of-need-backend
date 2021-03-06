from flask_security import RoleMixin, UserMixin

from flask_sqlalchemy import SQLAlchemy, event
from sqlalchemy.orm.session import Session as SessionBase
from sqlalchemy.sql import func as sql_func

db = SQLAlchemy()

# Authorization tables
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)


# Data tables
locations_services = db.Table(
    'locations_services',
    db.Column('location_id', db.Integer, db.ForeignKey('location.id')),
    db.Column('service_id', db.Integer, db.ForeignKey('service.id'))
)


locations_days_of_week = db.Table(
    'locations_days_of_week',
    db.Column('location_id', db.Integer, db.ForeignKey('location.id')),
    db.Column('day_of_week_id', db.Integer, db.ForeignKey('day_of_week.id'))
)


users_locations = db.Table(
    'users_locations',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('location_id', db.Integer, db.ForeignKey('location.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    locations = db.relationship('Location', secondary=users_locations,
                                backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email


class LastUpdate(db.Model):
    __tablename__ = 'last_update'
    id = db.Column(db.Integer, primary_key=True)
    last_update = db.Column(db.DateTime, nullable=False)

    def __str__(self):
        return self.day


class ChangeTrackingModel(db.Model):
    __abstract__ = True
    created = db.Column(db.DateTime, nullable=False,
        server_default=sql_func.current_timestamp())  # noqa
    updated = db.Column(db.DateTime, nullable=False,
        server_default=sql_func.current_timestamp())  # noqa


class DayOfWeek(ChangeTrackingModel):
    __tablename__ = 'day_of_week'
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10), nullable=False, unique=True)

    def __str__(self):
        return self.day


class Location(ChangeTrackingModel):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.String(255))
    address_line1 = db.Column(db.String(80))
    address_line2 = db.Column(db.String(80))
    address_line3 = db.Column(db.String(80))
    phone = db.Column(db.String(30))
    contact_email = db.Column(db.String(256))
    website = db.Column(db.String(256))
    opening_time = db.Column(db.Time)
    closing_time = db.Column(db.Time)
    city = db.Column(db.String(80))
    state = db.Column(db.String(80))
    days_of_week = db.relationship(
        'DayOfWeek', secondary=locations_days_of_week,
        backref=db.backref('locations', lazy='dynamic'))
    services = db.relationship(
        'Service', secondary=locations_services,
        backref=db.backref('locations', lazy='dynamic'))

    def __str__(self):
        return self.name


class Service(ChangeTrackingModel):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False, unique=True)

    def __str__(self):
        return self.name


@event.listens_for(SessionBase, 'before_flush')
def receive_before_flush(session, flush_context, instances):
    """Update the data version before every flush"""
    db.session.query(LastUpdate).delete()
    db.session.add(LastUpdate(last_update=sql_func.current_timestamp()))
