from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from flask import json

calendar = Blueprint('calendar', __name__,
                     template_folder='templates')

@calendar.route('/', defaults={'page': 'index'})
@calendar.route('/<page>')
def show(page):
    try:
        return render_template('%s.html' % page)
    except TemplateNotFound:
        abort(404)

@calendar.route('/get_events')
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

@calendar.route('/get_team_members/<team>')
def get_team_members(team):
    return json.dumps([
        {'id': 'kincljc',
         'name': 'Jason Kincl'},
        {'id': 'smkoch',
         'name': 'Scott Koch'}
        ])