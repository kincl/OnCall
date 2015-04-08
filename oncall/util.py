import os
import json
from copy import deepcopy
from datetime import date, timedelta
from flask import current_app, request, Response

from sqlalchemy.orm.attributes import InstrumentedAttribute

from oncall.models import Event, User, Team, Schedule, Cron

ONE_DAY = timedelta(1)

def _update_object_model(model, instance):
    """ Updates the instance of a model from provided request.json values """
    # Make sure we have a key that is an attribute of the model
    for key, value in request.json.items():
        if not isinstance(model.__dict__.get(key), InstrumentedAttribute):
            return False
        setattr(instance, key, value)
    return True


def _str_to_date(date_str):
    """ converts string of 2014-04-13 to Python date """
    return date(*[int(n) for n in str(date_str).split('-')])


def _get_monday(date):
    if date.isoweekday() == current_app.config['ONCALL_START']:
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

    sched_query = Schedule.query.filter_by(team_slug=team) \
                                   .order_by(Schedule.order,
                                             Schedule.role)
    sched_all = sched_query.all()
    sched_len = len(sched_all)/len(current_app.config['ROLES'])

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

        for role in current_app.config['ROLES']:
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
        if current_date.isoweekday() == current_app.config['ONCALL_START'] + 6 % 7 or current_date == end_date:
            for role in current_app.config['ROLES']:
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


def _api_error(message, category = 'warning'):
    return Response(json.dumps({'message':message, 'category':category}), 400)


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
        if count >= len(current_app.config['ROLES']):
            return False
        i += ONE_DAY
    return True


def _other_role(start_role):
    """ Select the !this role """
    # TODO: make it work for more than two roles
    for role in current_app.config['ROLES']:
        if role != start_role:
            return role


def _is_role_valid(eventid, new_role, start_date=None, end_date=None):
    """ Can we change the of the given event to new_role, look up
        the event and see if there are any events that have that
        role already """
    if new_role not in current_app.config['ROLES']:
        return False
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

