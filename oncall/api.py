from flask import Blueprint, current_app, abort, request, jsonify, Response

import json

from oncall.models import Event, User, Team, OncallOrder, Cron

from sqlalchemy.orm.attributes import InstrumentedAttribute

api = Blueprint('api', __name__)

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

@api.route('/teams/<team>', methods = ['GET', 'PUT', 'DELETE'])
def teams_team(team):
    if request.method == 'GET':
        team = Team.query.filter_by(slug=team).first_or_404()
        return jsonify(team.to_json())

    if request.method == 'PUT':
        if not request.json:
            abort(400)
        team = Team.query.filter_by(slug=team).first_or_404()
        # Make sure we have a key that is an attribute of the model
        for key, value in request.json.items():
            if not isinstance(Team.__dict__.get(key), InstrumentedAttribute):
                return Response('Key: {0} not in model'.format(key), status=500)
            setattr(team, key, value)

    if request.method == 'DELETE':
        current_app.db.session.delete(Team.query.filter_by(slug=team).first_or_404())

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

@api.route('/teams/<team>/schedule', methods = ['GET', 'PUT', 'DELETE'])
def teams_schedule(team):
    abort(501)

@api.route('/teams/<team>/on_call', methods = ['GET', 'PUT', 'DELETE'])
def teams_on_call(team):
    abort(501)

@api.route('/users')
def users():
    abort(501)

@api.route('/users/<user>')
def users_user(user):
    abort(501)

@api.route('/users/<user>/on_call')
def users_on_call(user):
    abort(501)

@api.route('/roles')
def roles():
    abort(501)
