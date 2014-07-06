from flask import Flask, request, render_template, abort, json, Response, g
from flask.ext.sqlalchemy import SQLAlchemy
from jinja2 import TemplateNotFound
from datetime import date, timedelta
from copy import deepcopy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

db = SQLAlchemy(app)

from oncall.models import Event
from oncall.models import User
from oncall.models import Team
from oncall.models import OncallOrder

ROLES = ['Primary',
         'Secondary']
ONCALL_START = 1

ONE_DAY = timedelta(1)

def _str_to_date(date_str):
    """ converts string of 2014-04-13 to Python date """
    return date(*[int(n) for n in str(date_str).split('-')])

def _get_events_for_dates(start_date, end_date, exclude_event = None):
    start  = _str_to_date(start_date)
    end = _str_to_date(end_date if end_date else start_date)
    events_start = Event.query.filter(start >= Event.start,
                                      start <= Event.end,
                                      Event.id != exclude_event,
                                      Event.team_slug == g.team)
    events_end = Event.query.filter(end >= Event.start,
                                    end <= Event.end,
                                    Event.id != exclude_event,
                                    Event.team_slug == g.team)
    events_inside = Event.query.filter(start <= Event.start,
                                       end >= Event.end,
                                       Event.id != exclude_event,
                                        Event.team_slug == g.team)

    return events_start.union(events_end, events_inside).all()


def _can_add_event(start_date, end_date, exclude_event = None):
    """ Given a start and end date, make sure that there are not more
        than two events. """

    events_all = _get_events_for_dates(start_date, end_date, exclude_event)

    i = _str_to_date(start_date)
    while i != _str_to_date(end_date if end_date else start_date) + ONE_DAY:
        count = 0
        for e in events_all:
            if i >= e.start and i <= e.end:
                count += 1
        if count >= len(ROLES):
            return False
        i += ONE_DAY
    return True

def _is_role_valid(eventid, new_role, start_date = None, end_date = None):
    """ Can we change the of the given event to new_role, look up
        the event and see if there are any events that have that 
        role already """
    e = Event.query.filter_by(id=eventid).first()
    events = _get_events_for_dates(start_date if start_date else e.start,
                                   end_date if end_date else e.end,
                                   exclude_event=eventid)
    flag = True
    for event in events:
        if event.role == new_role:
            flag = False
    return flag

def _other_role(start_role):
    """ Select the !this role """
    # TODO: make it work for more than two roles
    for role in ROLES:
        if role != start_role:
            return role

@app.route('/', defaults={'page': 'index'})
@app.route('/<page>')
def show(page):
    try:
        return render_template('%s.html' % page)
    except TemplateNotFound:
        abort(404)

@app.route('/get_events')
def get_events():
    g.team = request.args.get('team')
    events = _get_events_for_dates(date.fromtimestamp(float(request.args.get('start'))), 
                                   date.fromtimestamp(float(request.args.get('end'))))
    return Response(json.dumps([e.to_json() for e in events]),
           mimetype='application/json')

def _get_monday(date):
    if date.isoweekday() == ONCALL_START:
        return date
    else:
        return _get_monday(date - ONE_DAY)

def _serialize_and_delete_role(future_events, long_events, role):
    """Helper func to stringify dates and delete a long running event role from
       the dict and add it to the list of returned future events. Only really
       useful in get_future_events()"""
    if long_events.get(role):
        long_events[role]['start'] = str(long_events[role]['start'])
        long_events[role]['end'] = str(long_events[role]['end'])
        future_events += [long_events[role]]
        del long_events[role]

@app.route('/get_future_events')
def get_future_events():
    g.team = request.args.get('team')
    request_start = date.fromtimestamp(float(request.args.get('start')))
    request_end = date.fromtimestamp(float(request.args.get('end')))

    oncall_order = OncallOrder.query.filter_by(team_slug=g.team) \
                                    .order_by(OncallOrder.order,
                                              OncallOrder.role)
    oncall_order_all = oncall_order.all()
    max_oncall_order = len(oncall_order_all)/len(ROLES)

    if len(oncall_order_all) == 0:
        return Response(json.dumps(list()),
                        mimetype='application/json')

    current_date = _get_monday(request_start)
    # TODO: event ids will overlap with real events, do we care?
    current_id = 1
    current_order = 0
    long_events = {}
    future_events = []
    while current_date != request_end:
        events = _get_events_for_dates(current_date, current_date)
        event_roles = {}
        for e in events:
            event_roles[e.role] = e

        for role in ROLES:
            if role in event_roles.keys():
                # stop the long running event because an event already exists
                _serialize_and_delete_role(future_events, long_events, role)
            else:
                if long_events.get(role):
                    # just increment they day, we are already building an event
                    long_events.get(role)['end'] = deepcopy(current_date)
                else:
                    # Build the long event
                    oncall_now = oncall_order.filter_by(order=current_order, 
                                                        role=role).first()

                    long_events[role] = dict(editable=False,
                                             projection=True,
                                             id=current_id,
                                             start=deepcopy(current_date),
                                             end=deepcopy(current_date),
                                             role=role,
                                             title=oncall_now.get_title(),
                                             user_username=oncall_now.user_username)
                    current_id += 1

        # TODO: am I sure that this mod 7 works right?
        if current_date.isoweekday() == ONCALL_START + 6 % 7:
            for role in ROLES:
                _serialize_and_delete_role(future_events, long_events, role)
            current_order = (current_order + 1) % max_oncall_order
        current_date += ONE_DAY

    return Response(json.dumps(future_events),
                    mimetype='application/json')

@app.route('/get_oncall_order/<team>/<role>')
def get_oncall_order(team, role):
    # TODO: find who is not in the rotation and pass that list to client as well
    oncall_order = OncallOrder.query.filter_by(team_slug=team, role=role).order_by(OncallOrder.order).all()

    team_members = Team.query.filter_by(slug=team).first().users.order_by(User.username).all()
    for o in oncall_order:
        if o.user in team_members:
            team_members.remove(o.user)

    response = json.dumps({'oncall': [o.to_json() for o in oncall_order],
                           'not_oncall': [o.to_json() for o in team_members]})

    return Response(response,
                    mimetype='application/json')

@app.route('/update_oncall/<team>', methods=['POST'])
def update_oncall(team):
    for role in ROLES:
        order_list = OncallOrder.query.filter_by(team_slug=team, role=role).order_by(OncallOrder.order).all()
        for order in order_list:
            db.session.delete(order)

        order_num = 0
        for user in request.form.getlist(role+'[]'):
            db.session.add(OncallOrder(team, user, role, order_num))
            order_num += 1

    db.session.commit()
    return Response(json.dumps({'result': 'success'}),
                        mimetype='application/json')

@app.route('/get_teams')
def get_teams():
    return Response(json.dumps([t.to_json() for t in Team.query.all()]),
                    mimetype='application/json')

@app.route('/get_team_members/<team>')
def get_team_members(team):
    return Response(json.dumps([u.to_json() for u in Team.query.filter_by(slug=team).first().users.order_by(User.username).all()]),
                    mimetype='application/json')

@app.route('/get_roles')
def get_roles():
    return Response(json.dumps(ROLES),
                    mimetype='application/json')

@app.route('/create_event', methods=['POST'])
def create_event():
    g.team = request.form.get('team')
    if _can_add_event(request.form.get('start'), request.form.get('end')):
        events = _get_events_for_dates(request.form.get('start'), request.form.get('end'))
        newe = Event(request.form.get('username'),
                     request.form.get('team'),
                     ROLES[0] if events == [] else _other_role(events[0].role),
                     _str_to_date(request.form.get('start')))

        db.session.add(newe)
        db.session.commit()
        return Response(json.dumps({'result': 'success'}),
                        mimetype='application/json')
    else:
        return Response(json.dumps({'result': 'failure'}),
                        mimetype='application/json')

@app.route('/update_event/<eventid>', methods=['POST'])
def update_event(eventid):
    e = Event.query.filter_by(id=eventid).first()
    g.team = e.team_slug
    if request.form.get('start'):
        if _can_add_event(request.form.get('start'), request.form.get('end'), exclude_event=eventid):
            if _is_role_valid(eventid,
                              e.role,
                              request.form.get('start'),
                              request.form.get('end') if request.form.get('end') else request.form.get('start')):
                e.start = _str_to_date(request.form.get('start'))
                e.end = _str_to_date(request.form.get('end') if request.form.get('end') else request.form.get('start'))
            elif _is_role_valid(eventid,
                                _other_role(e.role),
                                request.form.get('start'),
                                request.form.get('end') if request.form.get('end') else request.form.get('start')):
                e.start = _str_to_date(request.form.get('start'))
                e.end = _str_to_date(request.form.get('end') if request.form.get('end') else request.form.get('start'))
                e.role = _other_role(e.role)

    if request.form.get('role'):
        if _is_role_valid(eventid, request.form.get('role')):
            e.role = request.form.get('role')

    if request.form.get('user_username'):
        e.user_username = request.form.get('user_username')

    if db.session.commit():
        return Response(json.dumps({'result': 'success'}),
                        mimetype='application/json')
    else:
        return Response(json.dumps({'result': 'failure'}),
                        mimetype='application/json')

@app.route('/delete_event/<eventid>', methods=['POST'])
def delete_event(eventid):
    e = Event.query.filter_by(id=eventid).first()
    db.session.delete(e)
    db.session.commit()
    return Response(json.dumps({'result': 'success'}),
                    mimetype='application/json')


