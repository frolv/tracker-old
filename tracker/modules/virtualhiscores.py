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

vs_type_names = {
    'exp': 'Total Experience',
    '99s': '99 Skills',
    '200': '200m Skills',
    'low': 'Lowest Skill',
}

def type_name(vs_type):
    """
    """

    try:
        global vs_type_names
        return vs_type_names[vs_type]
    except KeyError:
        return ''

def vs_types():
    global vs_type_names
    return vs_type_names.items()
