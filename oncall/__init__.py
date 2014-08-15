from flask import Flask, request, render_template, abort, json, Response, session, url_for, redirect, flash, get_flashed_messages
from flask.ext.sqlalchemy import SQLAlchemy
from jinja2 import TemplateNotFound
from datetime import date, timedelta, datetime
from copy import deepcopy
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
from urlparse import urlparse, urljoin
from flask_wtf import Form 
from wtforms import TextField, PasswordField, HiddenField

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.secret_key = 'test123'

login_manager = LoginManager()
login_manager.login_view = '/login'
login_manager.init_app(app)

db = SQLAlchemy(app)

from oncall.models import Event
from oncall.models import User
from oncall.models import Team
from oncall.models import OncallOrder
from oncall.models import Cron

ROLES = ['Primary',
         'Secondary']
ONCALL_START = 1

ONE_DAY = timedelta(1)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


class RedirectForm(Form):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))


class LoginForm(RedirectForm):
    username = TextField('Username')
    password = PasswordField('Password')


@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(username=userid).first()


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # login and validate the user...
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user:
            login_user(user)
            flash('Logged in successfully.')
            return redirect(request.args.get('next') or '/')
        else:
            flash('Invalid login.')
    return render_template('login.html', form=form, flashes=get_flashed_messages())


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


def _str_to_date(date_str):
    """ converts string of 2014-04-13 to Python date """
    return date(*[int(n) for n in str(date_str).split('-')])


def _get_events_for_dates(team, start_date, end_date, exclude_event=None):
    start = _str_to_date(start_date)
    end = _str_to_date(end_date if end_date else start_date)
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

    return events_start.union(events_end, events_inside).all()


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


def _other_role(start_role):
    """ Select the !this role """
    # TODO: make it work for more than two roles
    for role in ROLES:
        if role != start_role:
            return role


# TODO: FIX
@app.route('/', defaults={'team': 'team-1'})
@app.route('/<team>')
@login_required
def calendar(team):
    try:
        return render_template('index.html', logged_in=current_user, flashes=get_flashed_messages())
    except TemplateNotFound:
        abort(404)


@app.route('/list')
def current_oncall():
    current_oncall = {}
    for team in Team.query.all():
        current_team = {}
        current_oncall[team.name] = current_team
        for order in OncallOrder.query.filter_by(team_slug=team.slug, order=0):
            current_team[order.role] = order.user
        for event in _get_events_for_dates(team.slug, date.today(), date.today()):
            current_team[event.role] = event.user
    return render_template('list.html', oncall=current_oncall, roles=ROLES)


@app.route('/roles')
@login_required
def get_roles():
    return Response(json.dumps(ROLES),
                    mimetype='application/json')


@app.route('/teams')
@login_required
def get_teams():
    return Response(json.dumps([t.to_json() for t in Team.query.all()]),
                    mimetype='application/json')


@app.route('/<team>/events')
@login_required
def get_events(team):
    #team = request.args.get('team')
    events = _get_events_for_dates(team,
                                   date.fromtimestamp(float(request.args.get('start'))),
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


def _filter_events_by_date(events, filter_date):
    return_events = []
    for event in events:
        if filter_date >= event.start and filter_date <= event.end:
            return_events.append(event)
    return return_events


@app.route('/<team>/predict_events')
@login_required
def get_future_events(team):
    """Build list of events that will occur based on current Oncall Order"""
    #team = request.args.get('team')
    request_start = date.fromtimestamp(float(request.args.get('start')))
    request_end = date.fromtimestamp(float(request.args.get('end')))

    oncall_order = OncallOrder.query.filter_by(team_slug=team) \
                                    .order_by(OncallOrder.order,
                                              OncallOrder.role)
    oncall_order_all = oncall_order.all()
    max_oncall_order = len(oncall_order_all)/len(ROLES)

    if len(oncall_order_all) == 0:
        return Response(json.dumps(list()),
                        mimetype='application/json')

    # If we are looking ahead, figure out where to start in the order based on the current date
    if request_start > date.today():
        delta = _get_monday(request_start) - _get_monday(date.today())
        current_order = delta.days / 7 % max_oncall_order
        current_date = _get_monday(request_start)
    elif request_start < date.today() and request_end < date.today():
        # Both request dates are in the past, so we are not predicting events
        return Response([], mimetype='aplication/json')
    else:
        current_order = 0
        current_date = _get_monday(date.today())

    current_id = 1
    long_events = {}
    future_events = []
    real_events = _get_events_for_dates(team, current_date, request_end)
    while current_date != request_end:
        current_date_roles = []
        for e in _filter_events_by_date(real_events, current_date):
            current_date_roles.append(e.role)

        for role in ROLES:
            if role in current_date_roles:
                # stop the long running event because a real event exists
                _serialize_and_delete_role(future_events, long_events, role)
            else:
                try:
                    # just increment they day, we are already building an event
                    long_events[role]['end'] = deepcopy(current_date)
                except KeyError:
                    # Build the long event
                    oncall_now = oncall_order.filter_by(order=current_order,
                                                        role=role).first()
                    if oncall_now:
                        long_events[role] = dict(editable=False,
                                                 projection=True,
                                                 id='prediction_%s' % current_id,
                                                 start=deepcopy(current_date),
                                                 end=deepcopy(current_date),
                                                 role=role,
                                                 title=oncall_now.get_title(),
                                                 user_username=oncall_now.user_username)
                        current_id += 1

        # stop all long running event builds because we are at the end of the week
        # TODO: am I sure that this mod 7 works right?
        if current_date.isoweekday() == ONCALL_START + 6 % 7:
            for role in ROLES:
                _serialize_and_delete_role(future_events, long_events, role)
            if max_oncall_order > 0:
                current_order = (current_order + 1) % max_oncall_order
        current_date += ONE_DAY

    return Response(json.dumps(future_events),
                    mimetype='application/json')


@app.before_request
@app.route('/oncallOrder/rotate')
def rotate_oncall():
    if session['rotated'] < datetime.now() - timedelta(0, 60):
        print 'checking rotation'

        session['rotated'] = datetime.now()
        c = Cron.query.filter_by(name='oncall_rotate').first()
        if c is None:
            c = Cron('oncall_rotate')
            db.session.add(c)
            db.session.commit()

        if c.date_updated <= _get_monday(date.today()):
            c.date_updated = date.today()
            db.session.commit()

            for team in Team.query.all():
                currently_oncall = {}
                for role in ROLES:
                    oncall = OncallOrder.query.filter_by(team_slug=team.slug, role=role).all()
                    for oo in oncall:
                        oo.order = (oo.order - 1) % len(oncall)
                        if oo.order == 0:
                            currently_oncall[role] = oo

                db.session.commit()

                start_date = _get_monday(date.today())
                end_date = start_date + timedelta(7)
                real_events = _get_events_for_dates(team.slug, start_date, end_date)
                current_date = start_date
                build_events = {}
                while current_date != end_date:
                    current_date_roles = []
                    for e in _filter_events_by_date(real_events, current_date):
                        current_date_roles.append(e.role)
                    for role in ROLES:
                        if role in current_date_roles:
                            if build_events.get(role, None):
                                db.session.add(build_events.get(role))
                                del build_events[role]
                        else:
                            if build_events.get(role, None):
                                build_events.get(role).end = deepcopy(current_date)
                            else:
                                try:
                                    build_events[role] = Event(currently_oncall[role].user_username,
                                                               currently_oncall[role].team_slug,
                                                               role,
                                                               current_date)
                                except KeyError:
                                    # we dont have a current oncall role
                                    pass
                    current_date += ONE_DAY

                for role, event in build_events.items():
                    db.session.add(event)
                db.session.commit()


@app.route('/<team>/oncallOrder/<role>')
@login_required
def get_oncall_order(team, role):
    # TODO: find who is not in the rotation and pass that list to client as well
    oncall_order = OncallOrder.query.filter_by(team_slug=team,
                                               role=role) \
                                    .order_by(OncallOrder.order).all()


    team_members = Team.query.filter_by(slug=team).first() \
                             .users.order_by(User.username).all()
    for o in oncall_order:
        if o.user in team_members:
            team_members.remove(o.user)

    response = json.dumps({'oncall': [o.to_json() for o in oncall_order],
                           'not_oncall': [o.to_json() for o in team_members]})

    return Response(response,
                    mimetype='application/json')


@app.route('/<team>/oncallOrder', methods=['POST'])
@login_required
def update_oncall(team):
    for role in ROLES:
        order_list = OncallOrder.query.filter_by(team_slug=team,
                                                 role=role) \
                                      .order_by(OncallOrder.order).all()
        for order in order_list:
            db.session.delete(order)

        order_num = 0
        for user in request.form.getlist(role+'[]'):
            db.session.add(OncallOrder(team, user, role, order_num))
            order_num += 1

    db.session.commit()
    return Response(json.dumps({'result': 'success'}),
                    mimetype='application/json')


@app.route('/<team>/members')
@login_required
def get_team_members(team):
    members = []
    for u in Team.query.filter_by(slug=team).first() \
                 .users.order_by(User.username).all():
        members.append(u.to_json())

    return Response(json.dumps(members),
                    mimetype='application/json')


@app.route('/<team>/event', methods=['POST'])
@login_required
def create_event(team):
    #team = request.form.get('team')
    if _can_add_event(team, request.form.get('start'), request.form.get('end')):
        events = _get_events_for_dates(team,
                                       request.form.get('start'),
                                       request.form.get('end'))
        newe = Event(request.form.get('username'),
                     team,
                     ROLES[0] if events == [] else _other_role(events[0].role),
                     _str_to_date(request.form.get('start')))

        db.session.add(newe)
        db.session.commit()
        return Response(json.dumps({'result': 'success'}),
                        mimetype='application/json')
    else:
        return Response(json.dumps({'result': 'failure'}),
                        mimetype='application/json')


@app.route('/<team>/event/<eventid>', methods=['POST'])
@login_required
def update_event(team, eventid):
    start = request.form.get('start')
    end = request.form.get('end') if request.form.get('end') \
                                  else request.form.get('start')

    e = Event.query.filter_by(id=eventid).first()
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


@app.route('/<team>/event/delete/<eventid>', methods=['POST'])
@login_required
def delete_event(team, eventid):
    e = Event.query.filter_by(id=eventid).first()
    db.session.delete(e)
    db.session.commit()
    return Response(json.dumps({'result': 'success'}),
                    mimetype='application/json')
