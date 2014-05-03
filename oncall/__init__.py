from flask import Flask, request, render_template, abort, json, Response
from flask.ext.sqlalchemy import SQLAlchemy
from jinja2 import TemplateNotFound
from datetime import date, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

db = SQLAlchemy(app)

from oncall.models import Event
from oncall.models import User
from oncall.models import Team

ROLES = ['Primary',
         'Secondary']

def _str_to_date(date_str):
    """ converts string of 2014-04-13 to Python date """
    return date(*[int(n) for n in str(date_str).split('-')])

def _can_add_event(start_date, end_date, exclude_event = None):
    """ Given a start and end date, make sure that there are not more
        than two events. """
    start  = _str_to_date(start_date)
    end = _str_to_date(end_date if end_date else start_date)
    events_start = Event.query.filter(start >= Event.start,
                                      start <= Event.end,
                                      Event.id != exclude_event)
    events_end = Event.query.filter(end >= Event.start,
                                    end <= Event.end,
                                    Event.id != exclude_event)
    events_inside = Event.query.filter(start <= Event.start,
                                       end >= Event.end,
                                       Event.id != exclude_event)

    events_all = events_start.union(events_end, events_inside).all()

    one_day = timedelta(1)

    i = start
    while i != end + one_day:
        count = 0
        for e in events_all:
            if i >= e.start and i <= e.end:
                count += 1
        if count >= 2:
            return False
        i += one_day
    return True

@app.route('/', defaults={'page': 'index'})
@app.route('/<page>')
def show(page):
    try:
        return render_template('%s.html' % page)
    except TemplateNotFound:
        abort(404)

@app.route('/get_events')
def get_events():
    return Response(json.dumps([e.to_json() for e in Event.query.all()]), mimetype='application/json')

@app.route('/get_team_members/<team>')
def get_team_members(team):
    return Response(json.dumps([u.to_json() for u in User.query.all()]), mimetype='application/json')

@app.route('/create_event', methods=['POST'])
def create_event():
    if _can_add_event(request.form.get('start'), request.form.get('end')):
        events = Event.query.filter_by(start=_str_to_date(request.form.get('start'))).all()
        newe = Event(request.form.get('username'), 
                     'team-1', 
                     ROLES[0] if events == [] else ROLES[1], 
                     _str_to_date(request.form.get('start')))

        db.session.add(newe)
        db.session.commit()
        return Response(json.dumps({'result': 'success'}), mimetype='application/json')
    else:
        return Response(json.dumps({'result': 'failure'}), mimetype='application/json')

@app.route('/update_event/<eventid>', methods=['POST'])
def update_event(eventid):
    if _can_add_event(request.form.get('start'), request.form.get('end'), exclude_event=eventid):
        # TODO fix error handling
        e = Event.query.filter_by(id=eventid).first()
        e.start = _str_to_date(request.form.get('start'))
        e.end = _str_to_date(request.form.get('end') if request.form.get('end') else request.form.get('start'))
        db.session.commit()
        return Response(json.dumps({'result': 'success'}), mimetype='application/json')
    else:
        return Response(json.dumps({'result': 'failure'}), mimetype='application/json')

@app.route('/delete_event/<eventid>', methods=['POST'])
def delete_event(eventid):
    e = Event.query.filter_by(id=eventid).first()
    db.session.delete(e)
    db.session.commit()
    return Response(json.dumps({'result': 'success'}), mimetype='application/json')


