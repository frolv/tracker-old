#
# tracker/views.py
# Copyright (C) 2016 Alexei Frolov
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
from django.http import HttpResponse
from django.template import loader

from tracker.models import RSAccount
from tracker.modules import accounttracker, osrsapi, template

def index(request):
    """
    Tracker main page view.
    """

    return render(request, 'tracker/index.html')

def player(request, user, period='week'):
    """
    Tracker view for a single account for the given period.
    """

    try:
        acc = RSAccount.objects.get(username__iexact=user)
    except RSAccount.DoesNotExist:
        return render(request, 'tracker/nottracked.html', {'username': user})

    datapoints = accounttracker.get_data_range(acc, period)
    table_data = template.player_skill_table(datapoints)
    firstupdate = accounttracker.first_datapoint(acc).time

    if len(datapoints) == 0:
        lastupdate = accounttracker.latest_datapoint(acc).time
        skills = accounttracker.skills()
    else:
        lastupdate = datapoints[0][0].time
        skills = None

    records = template.player_records(acc, 0)
    skillname = 'Overall'

    context = {
        'username': acc.username.replace('_', ' '),
        'period': period,
        'periods': ['day', 'week', 'month', 'year'],
        'table_data': table_data,
        'table_skills': skills,
        'firstupdate': firstupdate,
        'lastupdate': lastupdate,
        'records': records,
        'skillname': skillname,
    }

    return render(request, 'tracker/player/player.html', context)


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
    table_data = template.player_skill_table(datapoints)

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
