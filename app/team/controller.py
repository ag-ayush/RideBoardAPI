from app import db
from app.auth.controller import get_current_user
from app.models_db import Team, User
from app.models_schema import TeamSchema
from app.utils import model_list_to_dict_list, user_in_team, get_value_from_payload, user_is_team_owner, check_key
from flask import Blueprint, jsonify, Response, abort

teams = Blueprint('team', __name__, url_prefix='/teams')

team_schema = TeamSchema(exclude=("members",))
team_schema_nested = TeamSchema(exclude=("members.teams",))


@teams.route('/', methods=['GET'])
@check_key
@get_current_user()
def get_teams(current_user):
    team_objs = db.session.query(Team).filter(
        Team.members.any(User.id == current_user.id)).all()
    json_build = model_list_to_dict_list(team_objs, team_schema)
    return jsonify(json_build)


@teams.route('/<team_id>', methods=['GET'])
@check_key
@user_in_team
def get_team(team_id):
    team = Team.query.get(team_id)
    if team is None:
        abort(404, "Team not found")
    json_build = model_list_to_dict_list([team], team_schema_nested)
    return jsonify(json_build[0])


@teams.route('/', methods=['POST'])
@check_key
@get_current_user()
def create_team(current_user):
    title = get_value_from_payload("title")
    description = get_value_from_payload("description")
    sharing = get_value_from_payload("sharing")
    creator = current_user.id
    team = Team(title, description, creator, sharing)
    team.members.append(current_user)
    db.session.add(team)
    db.session.commit()
    return Response(status=201)


@teams.route('/<team_id>', methods=['PATCH'])
@check_key
@user_is_team_owner
def update_team(team_id):
    team = Team.query.get(team_id)

    if team is None:
        abort(404, "Team not found")

    title = get_value_from_payload("title", optional=True)
    description = get_value_from_payload("description", optional=True)
    sharing = get_value_from_payload("sharing", optional=True)
    user_id = get_value_from_payload("user_id", optional=True)

    if title is not None:
        team.title = title
    if description is not None:
        team.description = description
    if sharing is not None:
        team.sharing = sharing
    if user_id is not None:
        valid = team.members.filter(User.id == user_id).all()
        if not valid:
            abort(400, "Provdided user_id is not a member of the team.")
        team.owner = user_id

    db.session.commit()
    return Response(status=200)


@teams.route('/<team_id>', methods=["DELETE"])
@check_key
@user_is_team_owner
def delete_team(team_id):
    team = Team.query.get(team_id)
    if team is None:
        abort(404, "Team not found")
    db.session.delete(team)
    db.session.commit()
    return Response(status=204)


@teams.route('/invite/<uuid:token>', methods=["POST"])
@check_key
@get_current_user()
def add_member(current_user, token):
    team = Team.query.filter_by(token=token).first()
    if not team:
        return abort(400, "Provided team does not exist.")
    if not team.sharing:
        return abort(400, "Provided team is not currently accepting invites.")

    ub = team.members.filter(User.id == current_user.id).all()
    if not ub:
        team.members.append(current_user)
        db.session.commit()
    return Response(status=201)


@teams.route('/<team_id>/user/<user_id>', methods=["DELETE"])
@check_key
@user_is_team_owner
def remove_member(team_id, user_id):
    team = Team.query.get(team_id)
    user = User.query.get(user_id)
    team.members.remove(user)
    db.session.commit()
    return Response(status=204)
