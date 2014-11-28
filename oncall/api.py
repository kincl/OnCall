from flask import Blueprint, current_app, abort, request, jsonify, Response

import json

from oncall.models import Event, User, Team, OncallOrder, Cron

from sqlalchemy.orm.attributes import InstrumentedAttribute

api = Blueprint('api', __name__)


def _update_object_model(model, instance):
    """ Updates the instance of a model from provided request.json values """
    # Make sure we have a key that is an attribute of the model
    for key, value in request.json.items():
        if not isinstance(model.__dict__.get(key), InstrumentedAttribute):
            return Response('Key: {0} not in model'.format(key), status=500)
        setattr(instance, key, value)

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

@api.route('/teams/<team>/schedule', methods = ['GET', 'PUT', 'DELETE'])
def teams_schedule(team):
    abort(501)

@api.route('/teams/<team>/on_call', methods = ['GET', 'PUT', 'DELETE'])
def teams_on_call(team):
    abort(501)

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
