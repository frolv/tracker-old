#
# tracker/modules/accounttracker.py
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

import re
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from tracker.models import *
from tracker.modules.osrsapi import *

# Look up username on the hiscores and add a new datapoint to their account.
def track(username):
    print('Proccessing update request for account %s.' % username)

    if not re.fullmatch(r'^[a-zA-Z0-9_]{1,12}$', username):
        raise InvalidUsernameError

    try:
        acc = RSAccount.objects.get(username__iexact=username)
    except RSAccount.DoesNotExist:
        print('Tracking %s for the first time.' % username)
        acc = RSAccount(username=username)

    # Check if the user has been updated recently.
    try:
        last = DataPoint.objects.filter(rsaccount=acc).order_by('-time')[0]
        if timezone.now() < last.time + timedelta(seconds=30):
            print('Account %s was updated less than 30s ago.' % username)
            raise RecentUpdateError

    except IndexError:
        pass

    # Of course, we want the whole datapoint to be added atomically.
    with transaction.atomic():
        # Add the account if a new one was created.
        acc.save()

        dp = DataPoint(rsaccount=acc)
        dp.save()

        skills = hiscore_lookup(username)
        for i in range(len(skills)):
            fields = skills[i].split(',')

            if (fields[2] == '-1'):
                exp = 0
            else:
                exp = int(fields[2])

            s = SkillLevel(skill_id=i, datapoint=dp, \
                    experience=exp, rank=int(fields[0]))
            s.save()

    print('Account %s has been updated.' % username)
    return dp


def get_data_range(acc, period):
    if (period == 'day'):
        p = timedelta(days=1)
    elif (period == 'week'):
        p = timedelta(days=7)
    elif (period == 'month'):
        p = timedelta(days=31)
    elif (period == 'year'):
        p = timedelta(days=365)
    else:
        raise InvalidPeriodError

    start = timezone.now() - p
    lst = DataPoint.objects.filter(rsaccount=acc, time__gte=start).order_by('-time')
    skillpoints = []

    for point in lst:
        sp = SkillLevel.objects.filter(datapoint=point).order_by('skill_id')
        skillpoints.append((point, sp))

    return skillpoints


class RecentUpdateError(Exception):
    pass

class InvalidUsernameError(Exception):
    pass

class InvalidPeriodError(Exception):
    pass
