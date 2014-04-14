from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from flask import render_template, abort
from jinja2 import TemplateNotFound
from flask import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

db = SQLAlchemy(app)

from oncall.models import Event
from oncall.models import User
#from oncall.models import Team

@app.route('/', defaults={'page': 'index'})
@app.route('/<page>')
def show(page):
    try:
        return render_template('%s.html' % page)
    except TemplateNotFound:
        abort(404)

@app.route('/get_events')
def get_events():
    return json.dumps([e.to_json() for e in Event.query.all()])

@app.route('/get_team_members/<team>')
def get_team_members(team):
    return json.dumps([u.to_json() for u in User.query.all()])

@app.route('/update_event', methods=['POST'])
def update_event():
    throw Exception
    #e = Event(jason.username, team1.slug, "Role 1", "2014-04-12")