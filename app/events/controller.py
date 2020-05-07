import datetime
import pytz

from itertools import chain
from sqlalchemy.orm import subqueryload
from flask import Blueprint, jsonify, request, Response

from app import db
from app.auth.controller import get_current_user
from app.utils import model_list_to_dict_list, get_value_from_payload, user_in_team, user_is_event_creator
from app.models_db import Event, Passenger, Car, User, Team
from app.models_schema import EventSchema, PassengerSchema, CarSchema, UserSchema, TeamSchema

events = Blueprint('events', __name__, url_prefix='/teams/<team_id>/events/')
event_schema = EventSchema(exclude=("cars",))
event_schema_nested = EventSchema()
# TODO: constants
eastern = pytz.timezone('US/Eastern')
fmt = '%Y-%m-%d %H:%M'


@events.route('/', methods=['GET'])
@user_in_team
def get_all_events(team_id):
    expired = request.args.get("expired") == 'true'
    expand = request.args.get("expand") == 'true'

    # Get all the events and current EST time.
    event_objs = Event.query.filter_by(team_id=team_id).all()
    loc_dt = datetime.datetime.now(tz=eastern)
    st = loc_dt.strftime(fmt)

    # If any event has expired by 1 hour then expire the event.
    for event in event_objs:
        t = datetime.datetime.strftime(
            (event.end_time + datetime.timedelta(hours=1)), '%Y-%m-%d %H:%M')
        if st > t:
            event.expired = True
    db.session.commit()

    event_objs = Event.query.filter_by(
        team_id=team_id, expired=expired).order_by(Event.start_time.asc()).all()

    json_out = model_list_to_dict_list(event_objs, event_schema_nested) if expand else model_list_to_dict_list(event_objs, event_schema)

    return jsonify(json_out)


@events.route('/<event_id>', methods=['GET'])
@user_in_team
def get_event(team_id, event_id):
    event = Event.query.get(event_id)
    json_build = model_list_to_dict_list([event], event_schema_nested)
    return jsonify(json_build[0])


@events.route('/', methods=['POST'])
@user_in_team
@get_current_user
def create_event(team_id, current_user):
    name = get_value_from_payload("name")
    address = get_value_from_payload("address")
    start_time = get_value_from_payload("start_time")
    end_time = get_value_from_payload("end_time")
    creator = current_user.id
    event = Event(name, address, start_time, end_time, creator, team_id)
    user = _get_default_ride_user()
    infty = Car(user.id, "Need a Ride", 0, 0,
                start_time, end_time, "", event.id)
    event.cars.append(infty)
    db.session.add(event)
    db.session.commit()
    return Response(status=201)


def _get_default_ride_user():
    val = User.query.get("∞")
    if val is None:
        user = User("∞", "Default", "User", "")
        db.session.add(user)
        return user
    return val


@events.route('/<event_id>', methods=['PATCH'])
@user_in_team
@user_is_event_creator
def update_event(team_id, event_id):
    event = Event.query.get(event_id)

    name = get_value_from_payload("name", optional=True)
    address = get_value_from_payload("address", optional=True)
    start_time = get_value_from_payload("start_time", optional=True)
    end_time = get_value_from_payload("end_time", optional=True)

    if name is not None:
        event.name = name
    if address is not None:
        event.address = address
    if start_time is not None:
        event.start_time = start_time
    if end_time is not None:
        event.end_time = end_time

    event.expired = False

    car = event.cars.filter(Car.name == "Need a Ride").first()
    car.departure_time = start_time
    car.return_time = end_time

    db.session.commit()
    return Response(status=200)


@events.route('/<event_id>', methods=["DELETE"])
@user_in_team
@user_is_event_creator
def delete_event(team_id, event_id):
    event = Event.query.get(event_id)
    db.session.delete(event)
    db.session.commit()
    return Response(status=204)
