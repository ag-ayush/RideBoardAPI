####################################
# File name: models_schema.py      #
# Author: Ayush Goel               #
####################################
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field, fields
from app.models_db import UserTeam, Team, User, Event, Car, Passenger, APIKey



class APIKeySchema(SQLAlchemySchema):
    class Meta:
        model = APIKey
        load_instance = True

    id = auto_field()
    hash = auto_field()
    owner = auto_field()
    reason = auto_field()


class UserSchema(SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = auto_field()
    firstname = auto_field()
    lastname = auto_field()
    picture = auto_field()
    teams = auto_field()


class TeamSchema(SQLAlchemySchema):
    class Meta:
        model = Team
        load_instance = True

    id = auto_field()
    title = auto_field()
    description = auto_field()
    token = auto_field()
    owner = auto_field()
    sharing = auto_field()
    members = fields.Nested(UserSchema, many=True)


class PassengerSchema(SQLAlchemySchema):
    class Meta:
        model = Passenger
        load_instance = True

    id = auto_field()
    username = auto_field()
    name = auto_field()
    car_id = auto_field()


class CarSchema(SQLAlchemySchema):
    class Meta:
        model = Car
        load_instance = True

    id = auto_field()
    username = auto_field()
    name = auto_field()
    current_capacity = auto_field()
    max_capacity = auto_field()
    departure_time = auto_field()
    return_time = auto_field()
    driver_comment = auto_field()
    event_id = auto_field()
    passengers = fields.Nested(PassengerSchema, many=True)


class EventSchema(SQLAlchemySchema):
    class Meta:
        model = Event
        load_instance = True

    id = auto_field()
    team_id = auto_field()
    name = auto_field()
    address = auto_field()
    start_time = auto_field()
    end_time = auto_field()
    creator = auto_field()
    expired = auto_field()
    cars = fields.Nested(CarSchema, many=True)
