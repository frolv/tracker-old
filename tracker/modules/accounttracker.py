#
# tracker/modules/accounttracker.py
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

import re
from django.db import connection, transaction
from django.db.models import Sum
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
        first = False
    except RSAccount.DoesNotExist:
        print('Tracking %s for the first time.' % username)
        acc = RSAccount(username=username)
        first = True

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
        acc.save()

        dp = DataPoint(rsaccount=acc)
        dp.save()

        # Create current and record entries first time account is tracked.
        if first:
            create_records(acc, dp)

        periods = get_period_firsts(acc, timezone.now())
        skills = hiscore_lookup(username)
        total_hours = 0

        i = len(skills) - 1
        while i >= 0:
            fields = skills[i].split(',')
            if len(fields) != 3:
                raise TrackError

            if (fields[2] == '-1'):
                exp = 0
            else:
                exp = int(fields[2])

            if i == 0:
                hours = total_hours
            else:
                hours = calculate_hours(i, exp)
                total_hours += hours

            s = SkillLevel(skill_id=i, datapoint=dp,
                           experience=exp, rank=int(fields[0]),
                           current_hours=hours, original_hours=hours)
            s.save()
            update_current(acc, dp, s, periods)
            if (periods[0] != None):
                update_five_min(acc, dp, s, periods[0])

            i -= 1

        update_time_played(acc, dp, total_hours, periods)
        tp = TimePlayed.objects.get(rsaccount=acc)
        tp.hours = total_hours
        tp.save()

        # compute and save time played rank
        rank = TimePlayed.objects.filter(hours__gte=total_hours).count()
        TimePlayedRank.objects.create(datapoint=dp, rank=rank)

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

    for c in curr:
        # For each Current entry, find the entry for the same skill
        # corresponding to the first datapoint in that time period and check if
        # the player has gained xp since then.
        if c.period == Current.DAY:
            first = earliest[1]
        elif c.period == Current.WEEK:
            first = earliest[2]
        elif c.period == Current.MONTH:
            first = earliest[3]
        elif c.period == Current.YEAR:
            first = earliest[4]

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


def update_five_min(acc, datapoint, sklvl, first):
    """
    Check and update the five minute record for a player and skill.

    Arguments:
        acc (RSAccount) - player to update.
        datapoint (DataPoint) - most recent data point for the player.
        sklvl (SkillLevel) - SkillLevel entry at the above datapoint for the
        skill to update.
        first (DataPoint) - earliest data point for player within
        five minutes of `datapoint`. Cannot be None.
    """

    s = SkillLevel.objects.get(datapoint=first, skill_id=sklvl.skill_id)
    dx = sklvl.experience - s.experience
    rec = Record.objects.get(rsaccount=acc, skill_id=sklvl.skill_id,
                             period=Record.FIVE_MIN)

    if dx > rec.experience:
        rec.start = first
        rec.end = datapoint
        rec.experience = dx
        rec.save()


def update_time_played(acc, datapoint, hours, earliest):
    """
    Update the Current and Record entires for player acc in QHA and
    Original QHA.
    """

    curr = Current.objects.filter(rsaccount=acc, skill_id=Skill.QHA_ID)

    for c in curr:
        if c.period == Current.DAY:
            first = earliest[1]
        elif c.period == Current.WEEK:
            first = earliest[2]
        elif c.period == Current.MONTH:
            first = earliest[3]
        elif c.period == Current.YEAR:
            first = earliest[4]

        if first != None:
            s = SkillLevel.objects.get(datapoint=first, skill_id=0)
            c.start = first
            c.end = datapoint
            c.hours = hours - s.current_hours
        else:
            c.start = datapoint
            c.end = datapoint
            c.hours = 0

        rec = Record.objects.filter(rsaccount=acc, skill_id__gte=Skill.QHA_ID,
                                    period=c.period)
        for r in rec:
            if c.hours > r.hours:
                r.start = c.start
                r.end = c.end
                r.hours = c.hours
                r.save()

        c.save()

    s = SkillLevel.objects.get(datapoint=earliest[0], skill_id=0)
    dh = hours - s.current_hours

    # Prevent floating point arithmetic errors
    if dh < 0.01:
        dh = 0

    rec = Record.objects.filter(rsaccount=acc, skill_id__gte=Skill.QHA_ID,
                                period=Record.FIVE_MIN)

    for r in rec:
        if dh > r.hours:
            r.start = first
            r.end = datapoint
            r.hours = dh
            r.save()


def get_period_firsts(acc, time):
    """
    Return an array of the earliest datapoints for account acc within each
    of the four periods: day, month, week and year.
    An entry in the array can be None, indicating that a data point does not
    exist within that period.
    """

    acc_dp = DataPoint.objects.filter(rsaccount=acc).order_by('time')
    points = []

    # For five minute records
    start = time - timedelta(seconds=300)
    first = acc_dp.filter(time__gte=start).first()
    points.append(first)

    for d in [1, 7, 31, 365]:
        start = time - timedelta(days=d)
        first = acc_dp.filter(time__gte=start).first()
        points.append(first)

    return points


def create_records(acc, datapoint):
    """
    Create Current and Record database entries for a newly tracked account.
    """

    skills = Skill.objects.order_by('skill_id')
    for s in skills:
        if s.skill_id != Skill.ORIG_QHA_ID:
            Current.objects.create(rsaccount=acc, skill=s,
                                   start=datapoint, end=datapoint,
                                   experience=0, period=Current.DAY)
            Current.objects.create(rsaccount=acc, skill=s,
                                   start=datapoint, end=datapoint,
                                   experience=0, period=Current.WEEK)
            Current.objects.create(rsaccount=acc, skill=s,
                                   start=datapoint, end=datapoint,
                                   experience=0, period=Current.MONTH)
            Current.objects.create(rsaccount=acc, skill=s,
                                   start=datapoint, end=datapoint,
                                   experience=0, period=Current.YEAR)

        Record.objects.create(rsaccount=acc, skill=s,
                              start=datapoint, end=datapoint,
                              experience=0, period=Record.FIVE_MIN)
        Record.objects.create(rsaccount=acc, skill=s,
                              start=datapoint, end=datapoint,
                              experience=0, period=Record.DAY)
        Record.objects.create(rsaccount=acc, skill=s,
                              start=datapoint, end=datapoint,
                              experience=0, period=Record.WEEK)
        Record.objects.create(rsaccount=acc, skill=s,
                              start=datapoint, end=datapoint,
                              experience=0, period=Record.MONTH)
        Record.objects.create(rsaccount=acc, skill=s,
                              start=datapoint, end=datapoint,
                              experience=0, period=Record.YEAR)


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


def specific_data_range(acc, start, end):
    """
    Fetch all datapoints for player acc between the points with IDs start and
    end, inclusive.
    """

    lst = DataPoint.objects.filter(rsaccount=acc, id__gte=start, id__lte=end) \
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


def skills(**kwargs):
    """
    Return set of Skill objects for all in-game skills.
    """

    try:
        include_hours = kwargs['include_qha']
    except KeyError:
        include_hours = False

    if include_hours:
        s = Skill.objects.all()
    else:
        s = Skill.objects.filter(skill_id__lt=Skill.QHA_ID)

    return s.order_by('skill_id')


def skill_name(skill_id):
    try:
        name = Skill.objects.get(skill_id=skill_id).skillname
    except Skill.DoesNotExist:
        return ''

    return name


def calculate_hours(skill_id, experience):
    """
    Calculate the number of hours played in a skill given an amount of
    experience.
    """

    rates = SkillRate.objects.filter(skill_id=skill_id).order_by('-start_exp')
    return __calculate_hours(rates, experience)


def __calculate_hours(rates, experience):
    """
    Calculate hours played using given experience rates and experience.
    """

    hours = 0

    for r in rates:
        if experience <= r.start_exp:
            continue

        diff = experience - r.start_exp
        if r.rate != 0:
            hours += diff / r.rate
        experience = r.start_exp

    return hours


def recalculate_hours(modified_skills, **kwargs):
    """
    Recalculate hours played for each skill ID in `modified_skills`
    for every datapoint in the database.

    This function takes a very long time to complete and should only be used
    after all desired changes to experience rates are made.
    """

    try:
        orig = kwargs['recalc_orig']
    except KeyError:
        orig = False

    if 0 in modified_skills:
        modified_skills.remove(0)

    Current.objects.filter(skill_id=Skill.QHA_ID).update(hours=0)
    Record.objects.filter(skill_id=Skill.QHA_ID).update(hours=0)

    if orig:
        Record.objects.filter(skill_id=Skill.ORIG_QHA_ID).update(hours=0)

    rates = []
    all_skills = skills()
    for s in all_skills:
        rates.append(SkillRate.objects.filter(skill=s).order_by('-start_exp'))

    for acc in RSAccount.objects.all():
        recalculate_single(acc, modified_skills, rates, orig)


def recalculate_single(acc, modified_skills, rates, orig):
    """
    Recalculate hours played for all datapoints belonging to player `acc`
    for each skill ID in `modified_skills`, and update player's QHA records.
    """

    points = DataPoint.objects.filter(rsaccount=acc)
    rec = Record.objects.filter(rsaccount=acc, skill_id=Skill.QHA_ID)

    records = [
        [rec.get(period=Record.FIVE_MIN), None],
        [rec.get(period=Record.DAY), None],
        [rec.get(period=Record.WEEK), None],
        [rec.get(period=Record.MONTH), None],
        [rec.get(period=Record.YEAR), None],
    ]

    if orig:
        orec = Record.objects.filter(rsaccount=acc, skill_id=Skill.ORIG_QHA_ID)
        records[0][1] = orec.get(period=Record.FIVE_MIN)
        records[1][1] = orec.get(period=Record.DAY)
        records[2][1] = orec.get(period=Record.WEEK)
        records[3][1] = orec.get(period=Record.MONTH)
        records[4][1] = orec.get(period=Record.YEAR)

    for dp in points:
        # Optimize for time through raw SQL queries.
        with connection.cursor() as cursor:
            # Recalculate hours for each modified skill.
            for s in modified_skills:
                cursor.execute('SELECT experience FROM tracker_skilllevel WHERE \
                                datapoint_id = %s AND skill_id = %s', [dp.id, s])
                h = __calculate_hours(rates[s], cursor.fetchone()[0])
                if not orig:
                    cursor.execute('UPDATE tracker_skilllevel \
                                    SET current_hours = %s \
                                    WHERE datapoint_id = %s AND skill_id = %s',
                                    [h, dp.id, s])
                else:
                    cursor.execute('UPDATE tracker_skilllevel \
                                    SET current_hours = %s, original_hours = %s \
                                    WHERE datapoint_id = %s AND skill_id = %s',
                                    [h, h, dp.id, s])

            # Recalculate total hours for this datapoint.
            cursor.execute('SELECT sum(current_hours) FROM tracker_skilllevel \
                            WHERE datapoint_id = %s AND skill_id != 0', [dp.id])
            hours = cursor.fetchone()[0]

            cursor.execute('UPDATE tracker_skilllevel SET current_hours = %s \
                            WHERE datapoint_id = %s AND skill_id = 0',
                            [hours, dp.id])

        ### TODO: Record checking and updating should be optimized to avoid
        ### redundantly checking the same datapoints multiple times.
        ### Amount of database queries can be reduced.

        # Check the five minute QHA from this datapoint
        # and update record if necessary.
        start = dp.time - timedelta(seconds=300)
        first = points.filter(time__gte=start).first()
        if first:
            h = SkillLevel.objects.get(datapoint=first, skill_id=0).current_hours
            dh = hours - h
            if dh < 0.01:
                dh = 0

            day = records[0][0]
            if dh > day.hours:
                day.hours = dh
                day.start = first
                day.end = dp
                if orig:
                    records[0][1].hours = dh
                    records[0][1].start = first
                    records[0][1].end = dp


        # Check and update day, week, month and year records.
        for i, d in enumerate([1, 7, 31, 365]):
            ind = i + 1
            start = dp.time - timedelta(days=d)
            first = points.filter(time__gte=start).first()

            if not first:
                continue

            h = SkillLevel.objects.get(datapoint=first, skill_id=0).current_hours
            dh = hours - h
            if dh < 0.01:
                dh = 0

            r = records[ind][0]
            if dh > r.hours:
                r.hours = dh
                r.start = first
                r.end = dp
                if orig:
                    records[ind][1].hours = dh
                    records[ind][1].start = first
                    records[ind][1].end = dp

    # Store all record values back into the database.
    for r in records:
        r[0].save()
        if orig:
            r[1].save()



class RecentUpdateError(Exception):
    pass

class InvalidUsernameError(Exception):
    pass

class TrackError(Exception):
    pass

class InvalidPeriodError(Exception):
    pass
