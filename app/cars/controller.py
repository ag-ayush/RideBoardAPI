import datetime
import pytz

from itertools import chain
from sqlalchemy.orm import subqueryload
from flask import Blueprint, jsonify, request, Response

from app import db
from app.auth.controller import get_current_user
from app.utils import model_list_to_dict_list, get_value_from_payload, user_in_team, user_is_event_creator, check_key
from app.models_db import Event, Passenger, Car, User, Team
from app.models_schema import EventSchema, PassengerSchema, CarSchema, UserSchema, TeamSchema

cars = Blueprint('cars', __name__, url_prefix='/teams/<team_id>/events/<event_id>/cars/')
car_schema = CarSchema(exclude=("passengers",))
car_schema_nested = CarSchema()
# TODO: constants
eastern = pytz.timezone('US/Eastern')
fmt = '%Y-%m-%d %H:%M'


@cars.route('/', methods=['GET'])
@check_key
@user_in_team
def get_all_cars(team_id, event_id):
    event_schema = EventSchema(only=("cars",))
    event_obj = Event.query.get(event_id)
    json_out = event_schema.dump(event_obj)
    return jsonify(json_out)


@cars.route('/', methods=['POST'])
@check_key
@user_in_team
@get_current_user()
def create_car(team_id, event_id, current_user):
    # TODO: get car by username, and check all passengers??? if none create, else abort
    username = current_user.id
    name = get_value_from_payload("name")
    current_capacity = 0
    max_capacity = get_value_from_payload("address")
    departure_time = get_value_from_payload("departure_time")
    return_time = get_value_from_payload("return_time")
    driver_comment = get_value_from_payload("driver_comment")
    car = Car(username, name, current_capacity, max_capacity, departure_time, return_time, driver_comment, event_id)
    db.session.add(car)
    db.session.commit()
    return Response(status=201)



@cars.route('/<car_id>', methods=['GET'])
@check_key
@user_in_team
def get_car(team_id, event_id, car_id):
    car = Car.query.get(car_id)
    json_build = model_list_to_dict_list([car], car_schema_nested)
    return jsonify(json_build[0])


# @cars.route('/<car_id>', methods=['PATCH'])
# @user_in_team
# @user_is_event_creator
# def update_event(team_id, event_id, car_id):
#     event = Event.query.get(event_id)

#     name = get_value_from_payload("name", optional=True)
#     address = get_value_from_payload("address", optional=True)
#     start_time = get_value_from_payload("start_time", optional=True)
#     end_time = get_value_from_payload("end_time", optional=True)

#     if name is not None:
#         event.name = name
#     if address is not None:
#         event.address = address
#     if start_time is not None:
#         event.start_time = start_time
#     if end_time is not None:
#         event.end_time = end_time

#     event.expired = False

#     car = event.cars.filter(Car.name == "Need a Ride").first()
#     car.departure_time = start_time
#     car.return_time = end_time

#     db.session.commit()
#     return Response(status=200)


# @cars.route('/<car_id>', methods=["DELETE"])
# @user_in_team
# @user_is_event_creator
# def delete_event(team_id, event_id, car_id):
#     event = Event.query.get(event_id)
#     db.session.delete(event)
#     db.session.commit()
#     return Response(status=204)
