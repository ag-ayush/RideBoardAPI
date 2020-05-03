import os 

# Import flask and template operators
from flask import Flask, render_template,session, blueprints,jsonify, request
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
# @app.errorhandler(404)
# def not_found(error):
# 	return jsonify(success=True,error=404,text=str(error))


# Import modules
from app.home.controller import home
from app.team.controller import teams

# Register blueprints
app.register_blueprint(home)
app.register_blueprint(teams)

