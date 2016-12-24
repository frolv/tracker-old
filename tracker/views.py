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

from tracker.models import RSAccount, Skill
from tracker.modules import accounttracker
from tracker.modules import osrsapi

# Tracker main page.
def index(request):
    return render(request, 'tracker/index.html')

# Tracker for a single account.
def player(request, user, period='week'):
    try:
        acc = RSAccount.objects.get(username__iexact=user)
    except RSAccount.DoesNotExist:
        return render(request, 'tracker/nottracked.html', {'username': user})

    datapoints = accounttracker.get_data_range(acc, period)
    skills = Skill.objects.order_by('skill_id')
    table_data = []

    # Set up an array of tuples to populate the player's skill table.
    # The first entry in each tuple is the difference in experience, the second
    # is difference in rank.
    for i in range(24):
        exp = datapoints[0][1][i].experience
        rank = datapoints[0][1][i].rank
        sn = skills[i].skillname

        de = exp - datapoints[-1][1][i].experience
        # Reversed as higher ranks are better.
        dr = datapoints[-1][1][i].rank - rank

        if de > 0:
            s0 = '+{:,}'.format(de)
        else:
            s0 = '{:,}'.format(de)

        if dr < 0:
            s1 = '{:,}'.format(dr)
        elif dr > 0:
            s1 = '+{:,}'.format(dr)
        else:
            s1 = '0'
        table_data.append((s0, s1, '{:,}'.format(exp), '{:,}'.format(rank), sn))

    context = {
        'username': acc.username,
        'period': period,
        'table_data': table_data,
        'lastupdate': datapoints[0][0].time,
    }

    return render(request, 'tracker/player.html', context)


def updateplayer(request):
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
