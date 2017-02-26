#
# tracker/modules/virtualhiscores.py
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

from tracker.models import RSAccount

vs_type_names = {
    'exp': 'Total Experience',
    '99s': '99 Skills',
    '200': '200m Skills',
    'low': 'Lowest Skill',
}


def type_name(vs_type):
    """
    Return the full name of a virtual hiscores type.
    """

    try:
        return vs_type_names[vs_type]
    except KeyError:
        return ''


def vs_types():
    return vs_type_names.items()


def vs_top_exp(start, limit):
    """
    """

    top = RSAccount.objects.order_by('-total_exp')
    if len(top) < start:
        return None

    result = {
        'vs_table': [],
        'vs_table_rows': 2,
    }

    for t in top[start:start + limit]:
        result['vs_table'].append({
            'username': t.username,
            'data': '{:,}'.format(t.total_exp)
        })

    return result


vs_type_fn = {
    'exp': vs_top_exp,
}

VS_PAGE_SIZE = 25


def vs_data(vs_type, page):
    """
    Return virtual hiscores data for given virtual hiscores type.

    Arguments:
        vs_type (str) - virtual hiscores type
        page - page number (pages consist of 25 entries)
    """

    start = (page - 1) * VS_PAGE_SIZE
    return vs_type_fn[vs_type](start, VS_PAGE_SIZE)
