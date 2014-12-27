from flask import Blueprint, current_app, abort, request, jsonify, Response

import json

from oncall.models import Event, User, Team, OncallOrder, Cron

from sqlalchemy.orm.attributes import InstrumentedAttribute

from datetime import date, timedelta
import time

from copy import deepcopy

api = Blueprint('api', __name__)

ROLES = ['Primary',
         'Secondary']
ONCALL_START = 1
ONE_DAY = timedelta(1)


def _update_object_model(model, instance):
    """ Updates the instance of a model from provided request.json values """
    # Make sure we have a key that is an attribute of the model
    for key, value in request.json.items():
        if not isinstance(model.__dict__.get(key), InstrumentedAttribute):
            return Response('Key: {0} not in model'.format(key), status=500)
        setattr(instance, key, value)


# TODO: not needed?
def _str_to_date(date_str):
    """ converts string of 2014-04-13 to Python date """
    return date(*[int(n) for n in str(date_str).split('-')])


def _get_monday(date):
    if date.isoweekday() == ONCALL_START:
        return date
    else:
        return _get_monday(date - ONE_DAY)


def _filter_events_by_date(events, filter_date):
    return_events = []
    for event in events:
        if filter_date >= event.start and filter_date <= event.end:
            return_events.append(event)
    return return_events


def _serialize_and_delete_role(future_events, long_events, role):
    """Helper func to stringify dates and delete a long running event role from
       the dict and add it to the list of returned future events. Only really
       useful in get_future_events()"""
    if long_events.get(role):
        long_events[role]['start'] = str(long_events[role]['start'])
        long_events[role]['end'] = str(long_events[role]['end'])
        future_events += [long_events[role]]
        del long_events[role]


def _get_events_for_dates(team, start_date, end_date, exclude_event=None, predict=False):
    start = start_date
    end = end_date if end_date else start_date
    events_start = Event.query.filter(start >= Event.start,
                                      start <= Event.end,
                                      Event.id != exclude_event,
                                      Event.team_slug == team)
    events_end = Event.query.filter(end >= Event.start,
                                    end <= Event.end,
                                    Event.id != exclude_event,
                                    Event.team_slug == team)
    events_inside = Event.query.filter(start <= Event.start,
                                       end >= Event.end,
                                       Event.id != exclude_event,
                                       Event.team_slug == team)

    events = events_start.union(events_end, events_inside).all()

    if not predict:
        return events

    sched_query = OncallOrder.query.filter_by(team_slug=team) \
                                   .order_by(OncallOrder.order,
                                             OncallOrder.role)
    sched_all = sched_query.all()
    sched_len = len(sched_all)/len(ROLES)

    if sched_len == 0:
        return events

    # If we are looking ahead, figure out where to start in the order based on the current date
    if start_date > date.today():
        delta = _get_monday(start_date) - _get_monday(date.today())
        current_order = delta.days / 7 % sched_len
        current_date = _get_monday(start_date)
    elif start_date < date.today() and end_date < date.today():
        # Both request dates are in the past, so we are not predicting events
        return events
    else:
        current_order = 0
        current_date = _get_monday(date.today())

    prediction_id = 1
    event_buffer = {}
    future_events = []
    while current_date <= end_date:
        current_date_roles = []
        for e in _filter_events_by_date(events, current_date):
            current_date_roles.append(e.role)

        for role in ROLES:
            if role in current_date_roles:
                # stop the long running event because a real event exists
                # but if the predicted event ends before the start date, just delete it
                if event_buffer.get(role) and event_buffer[role]['end'] < start_date:
                    del event_buffer[role]
                _serialize_and_delete_role(future_events, event_buffer, role)
            else:
                try:
                    # just increment they day, we are already building an event
                    event_buffer[role]['end'] = deepcopy(current_date)
                except KeyError:
                    # Build the long event
                    oncall_now = sched_query.filter_by(order=current_order,
                                                       role=role).first()
                    if oncall_now:
                        event_buffer[role] = dict(editable=False,
                                                 projection=True,
                                                 id='prediction_%s' % prediction_id,
                                                 start=deepcopy(current_date),
                                                 end=deepcopy(current_date),
                                                 role=role,
                                                 title=oncall_now.get_title(),
                                                 user_username=oncall_now.user_username)
                        prediction_id += 1

        # stop all long running event builds because we are at the end of the week
        # TODO: am I sure that this mod 7 works right?
        if current_date.isoweekday() == ONCALL_START + 6 % 7 or current_date == end_date:
            for role in ROLES:
                _serialize_and_delete_role(future_events, event_buffer, role)
            if sched_len > 0:
                current_order = (current_order + 1) % sched_len
        current_date += ONE_DAY

    return events + future_events


def _get_week_dates(date):
    """ Returns a tuple of dates for the Monday and Sunday of
        the week for the specified date. """
    monday = date.today() - timedelta((date.isoweekday() - 1) % 7)
    sunday = monday + timedelta(6)
    return monday, sunday


@api.route('/')
def help():
    return "Help about the API will go here"


@api.route('/teams', methods = ['GET', 'POST'])
def teams():
    if request.method == 'GET':
        return jsonify({'teams': [t.to_json() for t in Team.query.all()]})

    if request.method == 'POST':
        if not request.json or not 'team' in request.json:
            abort(400)
        current_app.db.session.add(Team(request.json.get('team')))

    current_app.db.session.commit()
    return Response(status=200)


@api.route('/teams/<team_slug>', methods = ['GET', 'PUT', 'DELETE'])
def teams_team(team_slug):
    team = Team.query.filter_by(slug=team_slug).first_or_404()
    if request.method == 'GET':
        return jsonify(team.to_json())

    if request.method == 'PUT':
        if not request.json:
            abort(400)
        _update_object_model(Team, team)

    if request.method == 'DELETE':
        current_app.db.session.delete(team)

    current_app.db.session.commit()
    return Response(status=200)


@api.route('/teams/<team_slug>/members', methods = ['GET', 'PUT', 'DELETE'])
def teams_members(team_slug):
    team = Team.query.filter_by(slug=team_slug).first_or_404()
    if request.method == 'GET':
        members = []
        for u in team.users:
            members.append(u.to_json())

        return jsonify({'members': members})

    if request.method == 'PUT':
        if not request.json or not 'members' in request.json:
            abort(400)
        team.users = [User.query.filter_by(username=u).first_or_404() for u in request.json.get('members')]

    if request.method == 'DELETE':
        team.users = []

    current_app.db.session.commit()
    return Response(status=200)


@api.route('/teams/<team_slug>/schedule', methods = ['GET', 'PUT', 'DELETE'])
def teams_schedule(team_slug):
    """

        PUT structure:

        {"shedule":{"primary":[[0,"jkincl"],[1,"user1"]], "secondary":[[0,"user1"],[1,"jkincl"]]}}

    """
    if request.method == 'GET':
        return jsonify({'schedule':
                       {'primary': [s.to_json() for s in OncallOrder.query. \
                                    filter_by(role='Primary', team_slug=team_slug). \
                                    order_by(OncallOrder.order).all()],
                        'secondary': [s.to_json() for s in OncallOrder.query. \
                                      filter_by(role='Secondary', team_slug=team_slug). \
                                      order_by(OncallOrder.order).all()]}})

    if request.method == 'PUT':
        if not request.json or not 'schedule' in request.json:
            abort(400)
        sched = request.json.get('schedule')

        # Maybe a better way to do this but delete all since we are doing an add all
        for item in OncallOrder.query.filter_by(team_slug=team_slug).all():
            current_app.db.session.delete(item)

        max_len = -1

        for role in [role.lower() for role in ROLES]:
            if role not in sched:
                abort(400)
            if max_len == -1:
                max_len = len(sched.get(role))
            else:
                if len(sched.get(role)) != max_len:
                    abort(400)

            for seq in sched.get(role):
                user = User.query.filter_by(username=seq[1]).first_or_404().username
                current_app.db.session.add(OncallOrder(team_slug, user, role, seq[0]))

    if request.method == 'DELETE':
        for item in OncallOrder.query.filter_by(team_slug=team_slug).all():
            current_app.db.session.delete(item)

    current_app.db.session.commit()
    return Response(status=200)


def _can_add_event(team, start_date, end_date, exclude_event=None):
    """ Given a start and end date, make sure that there are not more
        than two events. """

    events_all = _get_events_for_dates(team,
                                       start_date,
                                       end_date,
                                       exclude_event)

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


def _other_role(start_role):
    """ Select the !this role """
    # TODO: make it work for more than two roles
    for role in ROLES:
        if role != start_role:
            return role


@api.route('/teams/<team_slug>/events', methods = ['GET', 'POST'])
def teams_on_call(team_slug):
    """
        POST:
            {"start":"2014-12-23", "username":"jkincl"}
    """
    if request.method == 'GET':
        """ Default to the current day if nothing specified """
        #monday, sunday = _get_week_dates(date.today())
        req_start = request.args.get('start', None, type=float)
        req_end = request.args.get('end', None, type=float)
        date_start = (date.fromtimestamp(req_start) if req_start is not None else date.today())
        date_end = (date.fromtimestamp(req_end) if req_end is not None else date.today())

        events = _get_events_for_dates(team_slug,
                                       date_start,
                                       date_end,
                                       predict=True)

        return jsonify({'range':[str(date_start), str(date_end)],
                        'on_call': [e.to_json() if isinstance(e, Event) else e for e in events]})

    if request.method == 'POST':
        if _can_add_event(team_slug, request.json.get('start'), request.json.get('end')):
            events = _get_events_for_dates(team_slug,
                                           request.json.get('start'),
                                           request.json.get('end'))
            newe = Event(request.json.get('username'),
                         team_slug,
                         ROLES[0] if events == [] else _other_role(events[0].role),
                         _str_to_date(request.json.get('start')))
            current_app.db.session.add(newe)

    # TODO: Return status and result of action
    current_app.db.session.commit()
    return Response(status=200)


def _is_role_valid(eventid, new_role, start_date=None, end_date=None):
    """ Can we change the of the given event to new_role, look up
        the event and see if there are any events that have that
        role already """
    e = Event.query.filter_by(id=eventid).first()
    events = _get_events_for_dates(e.team_slug,
                                   start_date if start_date else e.start,
                                   end_date if end_date else e.end,
                                   exclude_event=eventid)
    flag = True
    for event in events:
        if event.role == new_role:
            flag = False
    return flag


@api.route('/teams/<team_slug>/events/<eventid>', methods = ['GET', 'PUT', 'DELETE'])
def teams_on_call_events_event(team_slug, eventid):
    if request.method == 'GET':
        return jsonify(Event.query.filter_by(id=eventid).first_or_404().to_json())

    if request.method == 'PUT':
        start = request.json.get('start')
        end = request.json.get('end') if request.json.get('end') \
                                      else request.json.get('start')

        e = Event.query.filter_by(id=eventid).first_or_404()
        if start:
            if _can_add_event(e.team_slug,
                              start,
                              end,
                              exclude_event=eventid):
                if _is_role_valid(eventid,
                                  e.role,
                                  start,
                                  end):
                    e.start = _str_to_date(start)
                    e.end = _str_to_date(end)
                elif _is_role_valid(eventid,
                                    _other_role(e.role),
                                    start,
                                    end):
                    e.start = _str_to_date(start)
                    e.end = _str_to_date(end)
                    e.role = _other_role(e.role)

        # TODO: need much better error checking here, any role is valid!
        if request.json.get('role'):
            print request.json.get('role')
            if _is_role_valid(eventid, request.json.get('role')):
                e.role = request.json.get('role')

        # TODO: Need error checking here!
        if request.json.get('user_username'):
            e.user_username = request.json.get('user_username')

    if request.method == 'DELETE':
        e = Event.query.filter_by(id=eventid).first_or_404()
        current_app.db.session.delete(e)

    current_app.db.session.commit()
    return Response(status=200)


@api.route('/users', methods = ['GET', 'POST'])
def users():
    if request.method == 'GET':
        return jsonify({'users': [u.to_json() for u in User.query.all()]})

    if request.method == 'POST':
        if not request.json or not 'username' in request.json or not 'name' in request.json: # TODO fixme
            abort(400)
        current_app.db.session.add(User(request.json.get('username'), request.json.get('name')))

    current_app.db.session.commit()
    return Response(status=200)


@api.route('/users/<username>', methods = ['GET', 'PUT', 'DELETE'])
def users_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if request.method == 'GET':
        return jsonify(user.to_json())

    if request.method == 'PUT':
        if not request.json:
            abort(400)
        # TODO: hax?
        if 'teams' in request.json:
            request.json['teams'] = [Team.query.filter_by(slug=t).first_or_404() for t in request.json.get('teams')]
        _update_object_model(User, user)

    if request.method == 'DELETE':
        current_app.db.session.delete(user)

    current_app.db.session.commit()
    return Response(status=200)


@api.route('/users/<user>/on_call', methods = ['GET', 'PUT', 'DELETE'])
def users_on_call(user):
    abort(501)


@api.route('/roles', methods = ['GET'])
def roles():
    abort(501)
