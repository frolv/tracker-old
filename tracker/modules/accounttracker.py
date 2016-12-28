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


def track(username):
    """
    Look up player username on the OSRS hiscores and add a new datapoint
    with their current levels and ranks.
    """

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

        periods = get_period_firsts(acc)

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
            update_current(acc, dp, s, periods)

    print('Account %s has been updated.' % username)
    return dp


def update_current(acc, datapoint, sklvl, earliest):
    """
    Update the current experience gains (and records, if necessary)
    for player acc for a single skill.

    Arguments:
        acc (RSAccount) - the player to update
        datapoint (DataPoint) - the most recent datapoint for the player
        sklvl (SkillLevel) - the skilllevel entry at the above datapoint
        for the skill to update
        earliest (list of DataPoint) - earliest datapoints for acc within
        all four periods (see `get_period_firsts`)
    """

    curr = Current.objects.filter(rsaccount=acc, skill_id=sklvl.skill_id)

    # Account is being tracked for the first time, create current and
    # record objects.
    if len(curr) == 0:
        curr = []
        curr.append(Current(rsaccount=acc, skill_id=sklvl.skill_id,
                            period=Current.DAY))
        curr.append(Current(rsaccount=acc, skill_id=sklvl.skill_id,
                            period=Current.WEEK))
        curr.append(Current(rsaccount=acc, skill_id=sklvl.skill_id,
                            period=Current.MONTH))
        curr.append(Current(rsaccount=acc, skill_id=sklvl.skill_id,
                            period=Current.YEAR))

        # Create dummy initial record entries.
        Record.objects.create(rsaccount=acc, skill_id=sklvl.skill_id,
                              start=datapoint, end=datapoint,
                              experience=0, period=Record.DAY)
        Record.objects.create(rsaccount=acc, skill_id=sklvl.skill_id,
                              start=datapoint, end=datapoint,
                              experience=0, period=Record.WEEK)
        Record.objects.create(rsaccount=acc, skill_id=sklvl.skill_id,
                              start=datapoint, end=datapoint,
                              experience=0, period=Record.MONTH)
        Record.objects.create(rsaccount=acc, skill_id=sklvl.skill_id,
                              start=datapoint, end=datapoint,
                              experience=0, period=Record.YEAR)

    for c in curr:
        # For each Current entry, find the entry for the same skill
        # corresponding to the first datapoint in that time period and check if
        # the player has gained xp since then.
        if c.period == Current.DAY:
            first = earliest[0]
        elif c.period == Current.WEEK:
            first = earliest[1]
        elif c.period == Current.MONTH:
            first = earliest[2]
        elif c.period == Current.YEAR:
            first = earliest[3]

        if first != None:
            s = SkillLevel.objects.get(datapoint=first, skill_id=sklvl.skill_id)
            c.start = first
            c.end = datapoint
            c.experience = sklvl.experience - s.experience
        else:
            c.start = datapoint
            c.end = datapoint
            c.experience = 0

        # Now, check if their current xp beats their record for the given skill
        # and time period. Update record if so.
        rec = Record.objects.get(rsaccount=acc, skill_id=sklvl.skill_id,
                                 period=c.period)
        if c.experience > rec.experience:
            rec.start = c.start
            rec.end = c.end
            rec.experience = c.experience
            rec.save()

        c.save()


def get_period_firsts(acc):
    """
    Return an array of the earliest datapoints for account acc within each
    of the four periods: day, month, week and year.
    """
    acc_dp = DataPoint.objects.filter(rsaccount=acc).order_by('time')
    points = []
    now = timezone.now()

    for d in [1, 7, 31, 365]:
        start = now - timedelta(days=d)
        # first can be None
        first = acc_dp.filter(time__gte=start).first()
        points.append(first)

    return points


def get_data_range(acc, period):
    """
    Fetch all datapoints for player acc within the given time period.
    """

    if period == 'day':
        p = timedelta(days=1)
    elif period == 'week':
        p = timedelta(days=7)
    elif period == 'month':
        p = timedelta(days=31)
    elif period == 'year':
        p = timedelta(days=365)
    else:
        raise InvalidPeriodError

    start = timezone.now() - p
    lst = DataPoint.objects.filter(rsaccount=acc, time__gte=start) \
                           .order_by('-time')

    skillpoints = []
    for point in lst:
        sp = SkillLevel.objects.filter(datapoint=point).order_by('skill_id')
        skillpoints.append((point, sp))

    return skillpoints


def latest_datapoint(acc):
    """
    Return the most recent datapoint for account acc.
    """
    return DataPoint.objects.filter(rsaccount=acc).order_by('-time').first()


def first_datapoint(acc):
    """
    Return the first datapoint on record for account acc.
    """
    return DataPoint.objects.filter(rsaccount=acc).order_by('time').first()


def skills():
    return Skill.objects.order_by('skill_id')


def skill_name(skill_id):
    try:
        name = Skill.objects.get(skill_id=skill_id).skillname
    except Skill.DoesNotExist:
        return ''

    return name


class RecentUpdateError(Exception):
    pass

class InvalidUsernameError(Exception):
    pass

class InvalidPeriodError(Exception):
    pass
