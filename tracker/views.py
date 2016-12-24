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
    table_data = template.player_skill_table(datapoints)

    context = {
        'username': acc.username.replace('_', ' '),
        'period': period,
        'table_data': table_data,
        'lastupdate': datapoints[0][0].time,
    }

    return render(request, 'tracker/player.html', context)


# Process request to update a player.
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
