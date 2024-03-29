#
# tracker/modules/osrsapi.py
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

import requests

OSRS_HS_API = 'http://services.runescape.com/m=hiscore_oldschool'
OSRS_HS_REQ = '/index_lite.ws?player='

def hiscore_lookup(username, **kwargs):
    url = OSRS_HS_API + OSRS_HS_REQ + username

    r = requests.get(url)
    if r.status_code == 200:
        return r.text.split('\n')[:24]
    elif r.status_code == 404:
        raise PlayerNotFoundError
    else:
        raise OsrsRequestError


class PlayerNotFoundError(Exception):
    pass

class OsrsRequestError(Exception):
    pass
