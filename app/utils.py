import uuid
from functools import wraps

from flask import request, abort

from app.auth.controller import get_current_user
from app.models_db import User, Team, Event, APIKey


def model_list_to_dict_list(models, schema):
    """ Returns a JSON representation of a list of SQLAlchemy-backed object.
    """
    json_build = []
    for model in models:
        json_build.append(schema.dump(model))

    return json_build


def check_key(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        keys = APIKey.query.filter_by(hash=api_key).all()
        if not keys:
            return abort(401, "Invalid API Key!")
        return fn(*args, **kwargs)
    return decorated_view


def user_in_team(fn):
    @wraps(fn)
    @get_current_user()
    def decorated_view(current_user, *args, **kwargs):
        team_id = kwargs['team_id']
        team = Team.query.get(team_id)
        if team is None:
            abort(404, "Provided team does not exist.")
        valid = team.members.filter(User.id == current_user.id).all()
        if not valid:
            abort(405, "You are not allowed to access this team.")
        return fn(*args, **kwargs)
    return decorated_view


def user_is_team_owner(fn):
    @wraps(fn)
    @get_current_user()
    def decorated_view(current_user, *args, **kwargs):
        team_id = kwargs['team_id']
        team = Team.query.get(team_id)
        if team is None:
            abort(404, "Provided team does not exist.")
        elif team.owner != current_user.id:
            abort(405, "You are not an admin of this team.")
        return fn(*args, **kwargs)
    return decorated_view


def user_is_event_creator(fn):
    @wraps(fn)
    @get_current_user()
    def decorated_view(current_user, *args, **kwargs):
        event_id = kwargs['event_id']
        event = Event.query.filter_by(id=event_id).first()
        if event is None:
            abort(404, "Provided event does not exist.")
        elif event.creator != current_user.id:
            abort(405, "You are not the creator of this event.")
        return fn(*args, **kwargs)
    return decorated_view


def get_value_from_payload(key, optional=False):
    value = request.get_json().get(key)
    if value is None and not optional:
        abort(400, description="Missing {} in request body.".format(key))
    return value
