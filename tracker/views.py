#
# tracker/views.py
# Copyright (C) 2016-2017 Alexei Frolov
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest

from tracker.models import RSAccount, Skill, Record
from tracker.modules import accounttracker, osrsapi, template

def index(request):
    """
    Tracker main page view.
    """

    return render(request, 'tracker/index.html', {
        'searchperiod': get_searchperiod(request)
    })


def player(request, user, period='week'):
    """
    Tracker view for a single account for the given period.
    """

    try:
        acc = RSAccount.objects.get(username__iexact=user)
    except RSAccount.DoesNotExist:
        return render(request, 'tracker/nottracked.html', {
            'username': user,
            'searchperiod': get_searchperiod(request),
        })

    datapoints = accounttracker.get_data_range(acc, period)
    return HttpResponse(template.player_page(acc, datapoints, period,
                                             get_searchperiod(request)))


def playerperiod(request, user, start, end):
    """
    Player view for experience in between the datapoints with IDs start and end.
    """

    try:
        acc = RSAccount.objects.get(username__iexact=user)
    except RSAccount.DoesNotExist:
        return render(request, 'tracker/nottracked.html', {'username': user})

    start_id = int(start)
    end_id = int(end)

    if start_id >= end_id:
        return HttpResponseBadRequest()

    datapoints = accounttracker.specific_data_range(acc, start, end)
    return HttpResponse(template.player_page(acc, datapoints, '',
                                             get_searchperiod(request)))


def records(request, skill):
    """
    Records overview for a given skill.
    """

    skill_id = int(skill)
    context = {
        'skills': accounttracker.skills(),
        'skillname': accounttracker.skill_name(skill_id),
        'day_records': template.record_table(skill_id, Record.DAY),
        'week_records': template.record_table(skill_id, Record.WEEK),
        'month_records': template.record_table(skill_id, Record.MONTH),
        'year_records': template.record_table(skill_id, Record.YEAR),
        'fivemin_records': template.record_table(skill_id, Record.FIVE_MIN),
        'searchperiod': get_searchperiod(request),
        'use_hours': skill_id >= Skill.QHA_ID,
    }

    return render(request, 'tracker/records/records.html', context)


def recordsfull(request, skill, period, page=1):
    """
    Full table of records for a specific skill.
    """

    skill_id = int(skill)
    p = Record.str_to_period(period)
    start = (int(page) - 1) * 25

    if period == 'fivemin':
        period = ''

    context = {
        'skillname': accounttracker.skill_name(skill_id),
        'period': period,
        'start': start,
        'page': page,
        'records': template.record_table(skill_id, p, start, 25),
        'searchperiod': get_searchperiod(request),
        'use_hours': skill_id >= Skill.QHA_ID,
    }

    return render(request, 'tracker/records/full.html', context)


def current(request, skill):
    """
    Current top overview for a given skill.
    """

    skill_id = int(skill)

    # TODO: update current top for expired datapoints

    context = template.current_top(skill_id)
    context['searchperiod'] = get_searchperiod(request)

    return render(request, 'tracker/current/current.html', context)


def updateplayer(request):
    """
    Player update request.
    """

    if (request.method != 'GET'):
        return HttpResponseBadRequest()

    try:
        dp = accounttracker.track(request.GET['player'])
    except accounttracker.RecentUpdateError:
        return HttpResponse('-1')
    except osrsapi.PlayerNotFoundError:
        return HttpResponse('-2')
    except osrsapi.OsrsRequestError:
        return HttpResponse('-3')
    except accounttracker.InvalidUsernameError:
        return HttpResponse('-4')
    except accounttracker.TrackError:
        return HttpResponse('-5')

    return HttpResponse('OK')


def recordstable(request):
    """
    Record table HTML for a given player and skill.
    """

    if (request.method != 'GET'):
        return HttpResponseBadRequest()

    try:
        acc = RSAccount.objects.get(username__iexact=request.GET['player'])
        skill = int(request.GET['skill_id'])
    except RSAccount.DoesNotExist:
        return HttpResponse('-2')

    context = {
        'records': template.player_records(acc, skill),
        'skillname': accounttracker.skill_name(skill),
        'suffix': 'xp' if skill < Skill.QHA_ID else 'hours',
    }

    return render(request, 'tracker/player/record-table.html', context)


def skillstable(request):
    """
    Respond with skills table HTML for a given player.
    """

    if (request.method != 'GET' or not request.GET['player'] \
            or not request.GET['period']):
        return HttpResponseBadRequest()

    try:
        acc = RSAccount.objects.get(username__iexact=request.GET['player'])
    except RSAccount.DoesNotExist:
        return HttpResponse('-2')

    datapoints = accounttracker.get_data_range(acc, request.GET['period'])
    table_data = template.player_skill_table(acc, datapoints)

    if len(datapoints) == 0:
        skills = accounttracker.skills()
    else:
        skills = None

    context = {
        'table_data': table_data,
        'table_skills': skills,
    }

    return render(request, 'tracker/player/skill-table.html', context)


def lastupdate(request):
    if (request.method != 'GET' or not request.GET['player']):
        return HttpResponseBadRequest()

    try:
        acc = RSAccount.objects.get(username__iexact=request.GET['player'])
    except RSAccount.DoesNotExist:
        return HttpResponse('-2')

    context = {
        'lastupdate': accounttracker.latest_datapoint(acc).time,
    }

    return render(request, 'tracker/player/last-update.html', context)


def searchperiod(request):
    if (request.method == 'POST'):
        request.session['searchperiod'] = request.POST['searchperiod']

    return HttpResponse('OK')


def get_searchperiod(request):
    try:
        return request.session['searchperiod']
    except KeyError:
        request.session['searchperiod'] = 'week'
        return request.session['searchperiod']
