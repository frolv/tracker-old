#
# tracker/modules/template.py
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

from tracker.models import Skill, DataPoint, Record

# Set up an array of tuples to populate the rows in a player's skill table.
# The first entry in each tuple is the difference in experience, the second
# is difference in rank, third and fourth are total experience and rank,
# respectively and the fifth is the name of the skill.
def player_skill_table(datapoints):
    skills = Skill.objects.order_by('skill_id')
    table_data = []

    if len(datapoints) == 0:
        return table_data

    for i in range(24):
        sn = skills[i].skillname

        exp = datapoints[0][1][i].experience
        rank = datapoints[0][1][i].rank

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

    return table_data


def player_records(acc, skill_id):
    rec = []

    for p in 'DWMY':
        try:
            r = Record.objects.get(rsaccount=acc, skill_id=skill_id, period=p)
        except Record.DoesNotExist:
            return []
        rec.append('{:,}'.format(r.experience))

    return rec
