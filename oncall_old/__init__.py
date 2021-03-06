import os
from copy import deepcopy
from datetime import date, timedelta, datetime

from flask import Flask, request, render_template, json, Response, session, \
                  redirect, flash, get_flashed_messages, jsonify, url_for

from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
from flask.ext.sqlalchemy import SQLAlchemy

from forms import LoginForm, UpdateProfileForm

app = Flask(__name__)

import logging
import logging.handlers

db = SQLAlchemy(app)
from oncall.models import Event, User, Team, Schedule, Cron
app.db = db

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

class MyModelView(ModelView):
    column_display_pk = True

    def is_accessible(self):
        return current_user.is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

class UserModelView(MyModelView):
    form_columns = ('username', 'name', 'teams')

class TeamModelView(MyModelView):
    form_columns = ('name', 'slug')

admin = Admin(app, name='Oncall', template_mode='bootstrap3')
admin.add_view(UserModelView(User, db.session))
admin.add_view(TeamModelView(Team, db.session))
admin.add_view(MyModelView(Cron, db.session))
# Add administrative views here

from oncall.api import api
app.register_blueprint(api, url_prefix='/api/v1')

from oncall.util import _get_monday, _filter_events_by_date, _str_to_date, _get_events_for_dates, ONE_DAY

app.config.from_object('oncall.settings.Defaults')
if 'ONCALLAPP_SETTINGS' in os.environ:
    app.config.from_envvar('ONCALLAPP_SETTINGS')
    app.logger.info("Config file at {0}".format(os.environ['ONCALLAPP_SETTINGS']))

if app.config['LOG_FILE']:
    file = logging.FileHandler(app.config['LOG_FILE'])
    file.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    app.logger.addHandler(file)

if app.config['SYSLOG']:
    syslog = logging.handlers.SysLogHandler("/dev/log")
    syslog.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    app.logger.addHandler(syslog)

login_manager = LoginManager()
login_manager.login_view = '/login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(username=userid).first()


@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.args.get('api_key')
    if api_key:
        if api_key == app.config['ADMIN_TOKEN']:
            return User('AdminToken', 'Admin Token')
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            return user


@app.route('/schedule/rotate')
def rotate_oncall():
    # TODO: Allow for changes to this time limit
    if session.get('rotated', None) != None and \
       session.get('rotated') > datetime.now() - timedelta(0, int(app.config.get('LIMIT', 3))):
       session['rotated'] = datetime.now()
       # TODO: this appears to only suceed if the last request was made more than X seconds ago?
       return Response('Too many responses', 200)

    # query the DB and check the last date the oncall rotation was done
    app.logger.debug('checking rotation')
    session['rotated'] = datetime.now()
    c = Cron.query.filter_by(name='oncall_rotate').first()
    if c is None:
        c = Cron('oncall_rotate')
        db.session.add(c)
        db.session.commit()
    else:
        if _get_monday(c.date_updated) == _get_monday(date.today()):
            # then we are in the same week, do nothing
            return Response('Already done', 200)

    app.logger.info('Rotating on call')
    c.date_updated = date.today()
    db.session.commit()

    for team in Team.query.all():
        currently_oncall = {}
        for role in app.config['ROLES']:
            oncall = Schedule.query.filter_by(team_slug=team.slug, role=role).all()
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
            for role in app.config['ROLES']:
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

    return Response('', 200)

@app.after_request
def add_header(response):
    """
    Do not cache json query responses
    """
    if response.mimetype == 'application/json':
        response.headers['Cache-Control'] = 'no-cache, no-store, max-age=0, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = 'Fri, 01 Jan 1990 00:00:00 GMT'
    return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # login and validate the user...
        from oncall.ldap_helper import bind

        password_bind = None
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user:
            if app.debug:
                password_bind = True
            else:
                password_bind = bind(request.form.get('username'), request.form.get('password'))
        if password_bind:
            login_user(user)
            return redirect(request.args.get('next') or '/')
        else:
            flash('Invalid login', 'danger')
    else:
        if app.debug:
            flash('Debug mode')
    return render_template('login.html', form=form, flashes=get_flashed_messages())


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route('/')
def current_oncall():
    current_oncall = {}
    for team in Team.query.all():
        current_team = {}
        current_oncall[team.name] = current_team
        for order in Schedule.query.filter_by(team_slug=team.slug, order=0):
            current_team[order.role] = order.user
        for event in _get_events_for_dates(team.slug, date.today(), date.today()):
            current_team[event.role] = event.user
    return render_template('list.html', oncall=current_oncall, roles=app.config['ROLES'])


@app.route('/calendar')
@login_required
def calendar():
    profile_form = UpdateProfileForm()

    profile_form.primary_team.choices = [(t.slug, t.name) for t in Team.query.all()]
    profile_form.teams.choices = [(t.slug, t.name) for t in Team.query.all()]
    profile_form.primary_team.data = current_user.primary_team
    profile_form.contact_card.data = current_user.contact_card
    profile_form.teams.data = [team.slug for team in current_user.teams]

    return render_template('calendar.html',
                           selected_team=team,
                           profile_form=profile_form,
                           logged_in=current_user)


@app.route('/user/current_state')
@login_required
def user_current_state():
    team = current_user.primary_team
    if team is None:
        team = Team.query.first().slug

    return jsonify({'primary_team': team})


@app.route('/user/updatePrefs', methods=['POST'])
@login_required
def user_update_prefs():
    form = UpdateProfileForm()
    form.primary_team.choices = [(t.slug, t.name) for t in Team.query.all()]
    form.teams.choices = [(t.slug, t.name) for t in Team.query.all()]

    if form.validate_on_submit():
        current_user.primary_team = request.form.get('primary_team')
        current_user.contact_card = request.form.get('contact_card')
        current_user.set_teams(request.form.getlist('teams'))
        db.session.commit()
        return Response(json.dumps({'result': 'success'}),
                        mimetype='application/json')
