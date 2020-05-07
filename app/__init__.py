import os

# Import flask and template operators
from flask import Flask, render_template, session, blueprints, jsonify, request
# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Get app config from absolute file path
if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

db = SQLAlchemy(app)

# HTTP error handling route
@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400


@app.errorhandler(401)
def unauthorized(e):
    return jsonify(error=str(e)), 401


@app.errorhandler(403)
def forbidden(e):
    return jsonify(error=str(e)), 403


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify(error=str(e)), 405


# pylint: disable=wrong-import-position
from app.events.controller import events
from app.team.controller import teams
from app.home.controller import home

# Register blueprints
app.register_blueprint(home)
app.register_blueprint(teams)
app.register_blueprint(events)
