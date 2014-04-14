from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from flask import Blueprint, render_template, abort, current_app
from jinja2 import TemplateNotFound
from flask import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

db = SQLAlchemy(app)

from oncall.models.user import User
from oncall.models.team import Team

@app.route('/', defaults={'page': 'index'})
@app.route('/<page>')
def show(page):
    try:
        return render_template('%s.html' % page)
    except TemplateNotFound:
        abort(404)

@app.route('/get_events')
def get_events():
    return json.dumps([
        {'id': 1, 
         'title': 'event1', 
         'start': "2014-04-10"},
        {'id': 2,
         'title': 'event2',
         'start': '2014-04-12',
         'end': '2014-04-14'}
        ])

@app.route('/get_team_members/<team>')
def get_team_members(team):
    users = []
    for u in User.query.all():
        users.append(u.to_json())
    return json.dumps(users)
