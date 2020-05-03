import uuid

def model_to_dict(model):
    """ Returns a JSON representation of an SQLAlchemy-backed object.
    """
    json = {}
    json['fields'] = {}
    json['pk'] = getattr(model, 'id')

    for col in model._sa_class_manager.mapper.mapped_table.columns:
        json['fields'][col.name] = getattr(model, col.name)
        if isinstance(json['fields'][col.name], uuid.UUID):
            json['fields'][col.name] = str(json['fields'][col.name])

    return json


def list_model_to_json_list(models):
    """ Returns a JSON representation of a list of SQLAlchemy-backed object.
    """
    json_build = []
    for model in models:
        json_build.append(model_to_dict(model))

    return json_build


def user_in_team(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        teamid = 0    # TODO: fix
        current_user = kwargs['current_user']
        valid = UserTeam.query.filter_by(team_id=teamid, user_id=current_user.id).all()
        if not valid:
            abort(404)
        return fn(*args, **kwargs)
    return decorated_view