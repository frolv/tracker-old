#
# tracker/modules/template.py
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

from django.template import loader

from tracker.models import Skill, DataPoint, Record
from tracker.modules import accounttracker

def player_skill_table(datapoints):
    """
    Set up an array of tuples to populate the rows in a player's skill table.
    The first entry in each tuple is the difference in experience, the second
    is difference in rank, third and fourth are total experience and rank,
    respectively and the fifth is the name of the skill.
    """

    skills = accounttracker.skills()
    table_data = []

    if len(datapoints) == 0:
        return table_data

    for i in range(len(skills)):
        exp = datapoints[0][1][i].experience
        rank = datapoints[0][1][i].rank
        hours =  datapoints[0][1][i].current_hours

        de = exp - datapoints[-1][1][i].experience
        # Reversed as higher ranks are better.
        dr = datapoints[-1][1][i].rank - rank
        dh = hours - datapoints[-1][1][i].current_hours
        if dh < 0.01:
            dh = 0

        skilldata = {}

        if de > 0:
            skilldata['de'] = '+{:,}'.format(de)
        else:
            skilldata['de'] = '{:,}'.format(de)

        if dr < 0:
            skilldata['dr'] = '{:,}'.format(dr)
        elif dr > 0:
            skilldata['dr'] = '+{:,}'.format(dr)
        else:
            skilldata['dr'] = '0'

        if dh > 0:
            skilldata['dh'] = '+{:,.2f}'.format(dh)
        else:
            skilldata['dh'] = '{:,.2f}'.format(dh)

        skilldata['exp'] = '{:,}'.format(exp)
        skilldata['rank'] = '{:,}'.format(rank)
        skilldata['hours'] = '{:,.2f}'.format(hours)
        skilldata['skillname'] = skills[i].skillname

        table_data.append(skilldata)

    return table_data


def player_records(acc, skill_id):
    """
    Set up an array of tuples to populate the small records table on a player
    page for a specific skill.
    """

    rec = []

    for p in 'DWMY':
        try:
            r = Record.objects.get(rsaccount=acc, skill_id=skill_id, period=p)
        except Record.DoesNotExist:
            return []

        if r.experience == 0:
            url = "#"
        else:
            url = "/player/%s/period/%d-%d" % (acc.username, r.start_id, r.end_id)
        rec.append(('{:,}'.format(r.experience), url))

    return rec


def record_table(skill_id, period, start=0, limit=10):
    """
    Set up an array of tuples to populate a single table on a records page.

    Arguments:
    skill_id (int): the ID of the skill for which to look up records.
    period (str): period for which to look up records.
    start (int): the index at which to begin.
    limit (int): number of players to return.
    """

    rec = []
    end = start + limit

    if skill_id < Skill.QHA_ID:
        top = Record.objects.filter(skill_id=skill_id, period=period) \
                            .order_by('-experience')[start:end]
    else:
        top = Record.objects.filter(skill_id=skill_id, period=period) \
                            .order_by('-hours')[start:end]

    for r in top:
        if skill_id < Skill.QHA_ID:
            if r.experience == 0:
                break
            recval = '{:,}'.format(r.experience)

        else:
            if r.hours == 0:
                break
            recval = '{:,.2f}'.format(r.hours)

        name = r.rsaccount.username
        rec.append((name, name.replace('_', ' '), recval,
                    str(r.start_id), str(r.end_id)))

    return rec


def player_page(acc, datapoints, period, searchperiod):
    """
    Return the HTML of the player page for a specific player and period.
    """

    table_data = player_skill_table(datapoints)
    firstupdate = accounttracker.first_datapoint(acc).time

    if len(datapoints) == 0:
        lastupdate = accounttracker.latest_datapoint(acc).time
        skills = accounttracker.skills()
        cs = None
        ce = None
        dh = '0.00'
    else:
        lastupdate = datapoints[0][0].time
        skills = None
        cs = datapoints[-1][0].time
        ce = lastupdate
        dh = table_data[0]['dh']

    records = player_records(acc, 0)
    skillname = 'Overall'

    t = loader.get_template('tracker/player/player.html')
    context = {
        'username': acc.username.replace('_', ' '),
        'period': period,
        'periods': ['day', 'week', 'month', 'year'],
        'customstart': cs,
        'customend': ce,
        'table_data': table_data,
        'table_skills': skills,
        'delta_hours': dh,
        'firstupdate': firstupdate,
        'lastupdate': lastupdate,
        'records': records,
        'skillname': skillname,
        'searchperiod': searchperiod,
    }

    return t.render(context)
