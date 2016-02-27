import json
from datetime import date
from flask import Blueprint, current_app, request, jsonify, Response
from flask_login import login_required

from database import db

from api.models import Event, User, Team, Schedule
from util import _update_object_model, _str_to_date, \
                 _get_events_for_dates, _api_error, \
                 _can_add_event, _other_role, _is_role_valid

api_app = Blueprint('api', __name__, url_prefix='/api/v1')

@api_app.route('/')
def api_help():
    return "Help about the API will go here"


@api_app.route('/teams', methods=['GET', 'POST'])
@login_required
def teams():
    if request.method == 'GET':
        return jsonify({'teams': [t.to_json() for t in Team.query.all()]})

    if request.method == 'POST':
        if not request.json or not 'team' in request.json:
            # flash('Malformed request, "team" not found in JSON', 'danger')
            # abort(400)
            return _api_error('Malformed request, "team" not found in JSON', 'danger')
        db.session.add(Team(request.json.get('team')))

    db.session.commit()
    return Response(status=200)


@api_app.route('/teams/<team_slug>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def teams_team(team_slug):
    team = Team.query.filter_by(slug=team_slug).first_or_404()
    if request.method == 'GET':
        return jsonify(team.to_json())

    if request.method == 'PUT':
        if not request.json:
            # flash('Malformed request, no JSON', 'danger')
            # abort(400)
            return _api_error('Malformed request, no JSON', 'danger')
        if not _update_object_model(Team, team):
            return _api_error('Key not in model', 'danger')

    if request.method == 'DELETE':
        db.session.delete(team)

    db.session.commit()
    return Response(status=200)


@api_app.route('/teams/<team_slug>/members', methods=['GET', 'PUT', 'DELETE'])
@login_required
def teams_members(team_slug):
    team = Team.query.filter_by(slug=team_slug).first_or_404()
    if request.method == 'GET':
        members = []
        for u in team.users:
            members.append(u.to_json())

        return jsonify({'members': sorted(members, key=lambda item: item['name'])})

    if request.method == 'PUT':
        if not request.json or not 'members' in request.json:
            # flash('Malformd request, "members" not found in JSON', 'danger')
            # abort(400)
            return _api_error('Malformed request, members not found in JSON', 'danger')
        team.users = [User.query.filter_by(username=u).first_or_404() for u in request.json.get('members')]

    if request.method == 'DELETE':
        team.users = []

    db.session.commit()
    return Response(status=200)


@api_app.route('/teams/<team_slug>/schedule', methods=['GET', 'PUT', 'DELETE'])
@login_required
def teams_schedule(team_slug):
    """

        PUT structure:

        {"shedule":{"primary":[[0,"jkincl"],[1,"user1"]], "secondary":[[0,"user1"],[1,"jkincl"]]}}

    """
    if request.method == 'GET':
        return jsonify({'schedule':
                       {'Primary': [s.to_json() for s in Schedule.query. \
                                    filter_by(role='Primary', team_slug=team_slug). \
                                    order_by(Schedule.order).all()],
                        'Secondary': [s.to_json() for s in Schedule.query. \
                                      filter_by(role='Secondary', team_slug=team_slug). \
                                      order_by(Schedule.order).all()]}})

    if request.method == 'PUT':
        if not request.json or not 'schedule' in request.json:
            # flash('Malformd request, "schedule" not found in JSON', 'danger')
            # abort(400)
            return _api_error('Malformed request, schedule not found in JSON', 'danger')
        sched = request.json.get('schedule')

        # Maybe a better way to do this but delete all since we are doing an add all
        for item in Schedule.query.filter_by(team_slug=team_slug).all():
            db.session.delete(item)

        max_len = -1

        for role in [role for role in current_app.config['ROLES']]:
            if role not in sched:
                # flash('Malformd request, specified role is not found', 'danger')
                # abort(400)
                return _api_error('Malformed request, specified role is not found', 'danger')
            if max_len == -1:
                max_len = len(sched.get(role))
            else:
                if len(sched.get(role)) != max_len:
                    # flash('Schedules for each role must match length', 'danger')
                    # abort(400)
                    return _api_error('Schedules for each role must match length', 'danger')

            for seq in sched.get(role):
                user = User.query.filter_by(username=seq[1]).first_or_404().username
                db.session.add(Schedule(team_slug, user, role, seq[0]))

    if request.method == 'DELETE':
        for item in Schedule.query.filter_by(team_slug=team_slug).all():
            db.session.delete(item)

    db.session.commit()
    return Response(status=200)


@api_app.route('/teams/<team_slug>/events', methods=['GET', 'POST'])
@login_required
def teams_on_call(team_slug):
    """
        POST:
            {"start":"2014-12-23", "username":"jkincl"}

        Default to the current day if nothing specified
    """
    if request.method == 'GET':
        req_start = request.args.get('start', None, type=float)
        req_end = request.args.get('end', None, type=float)
        date_start = (date.fromtimestamp(req_start) if req_start is not None else date.today())
        date_end = (date.fromtimestamp(req_end) if req_end is not None else date.today())

        events = _get_events_for_dates(team_slug,
                                       date_start,
                                       date_end,
                                       predict=True)

        event_array = [e.to_json() if isinstance(e, Event) else e for e in events]

        # For FullCalendar so it returns in the correct way
        if request.args.get('minimal'):
            return Response(json.dumps(event_array),
                            mimetype='application/json')
        return jsonify({'range':[str(date_start), str(date_end)],
                        'on_call': event_array})

    if request.method == 'POST':
        if _can_add_event(team_slug, request.json.get('start'), request.json.get('end')):
            events = _get_events_for_dates(team_slug,
                                           request.json.get('start'),
                                           request.json.get('end'))
            newe = Event(request.json.get('username'),
                         team_slug,
                         current_app.config['ROLES'][0] if events == [] else _other_role(events[0].role),
                         _str_to_date(request.json.get('start')))
            db.session.add(newe)
        else:
            # flash('Cannot add event, maximum for day has been reached', 'danger')
            return _api_error('Cannot add event, maximum for day has been reached', 'danger')

    # TODO: Return status and result of action
    db.session.commit()
    return Response(status=200)


@api_app.route('/teams/<team_slug>/events/<eventid>', methods=['GET', 'PUT', 'DELETE'])
@login_required
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
                e.start = _str_to_date(start)
                e.end = _str_to_date(end)

                # If role is already taken, switch event to other role
                if not _is_role_valid(eventid,
                                      e.role,
                                      start,
                                      end):
                    e.role = _other_role(e.role)
            else:
                # flash('Cannot add event, maximum for day has been reached', 'danger')
                return _api_error('Cannot add event, maximum for day has been reached', 'danger')

        if request.json.get('role'):
            if _is_role_valid(eventid, request.json.get('role')):
                e.role = request.json.get('role')
            else:
                return _api_error('Cannot add event, maximum for day has been reached', 'danger')

        if request.json.get('user_username'):
            User.query.filter_by(username=request.json.get('user_username')).first_or_404()
            e.user_username = request.json.get('user_username')

    if request.method == 'DELETE':
        e = Event.query.filter_by(id=eventid).first_or_404()
        db.session.delete(e)

    db.session.commit()
    return Response(status=200)


@api_app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if request.method == 'GET':
        return jsonify({'users': [u.to_json() for u in User.query.all()]})

    if request.method == 'POST':
        if not request.json or not 'username' in request.json or not 'name' in request.json: # TODO fixme
            # flash('problem')
            # abort(400)
            return _api_error('Malformed request, no username specified', 'danger')
        db.session.add(User(request.json.get('username'), request.json.get('name')))

    db.session.commit()
    return Response(status=200)


@api_app.route('/users/<username>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def users_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if request.method == 'GET':
        return jsonify(user.to_json())

    if request.method == 'PUT':
        if not request.json:
            # flash('problem')
            # abort(400)
            return _api_error('Malformed request, no JSON', 'danger')
        # TODO: hax?
        if 'teams' in request.json:
            request.json['teams'] = [Team.query.filter_by(slug=t).first_or_404() for t in request.json.get('teams')]
        if not _update_object_model(User, user):
            return _api_error('Key not in model', 'danger')

    if request.method == 'DELETE':
        db.session.delete(user)

    db.session.commit()
    return Response(status=200)


@api_app.route('/users/<user>/on_call', methods=['GET', 'PUT', 'DELETE'])
@login_required
def users_on_call(user):
    return Response(status=501)


@api_app.route('/roles', methods=['GET'])
# @login_required
def roles():
    if request.method == 'GET':
        return jsonify(roles=current_app.config['ROLES'])
