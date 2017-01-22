#
# tracker/urls.py
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

from django.conf.urls import url
import tracker.views as views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^player/(?P<user>[a-zA-Z0-9_]+)/$', views.player, name='player'),
    url(r'^player/(?P<user>[a-zA-Z0-9_]+)/(?P<period>day|week|month|year)$',
        views.player, name='player'),
    url(r'^player/(?P<user>[a-zA-Z0-9_]+)/period/(?P<start>\d+)-(?P<end>\d+)$',
        views.playerperiod),
    url(r'^current/(?P<skill>(1?[0-9]|2[0-3]|99))/$', views.current),
    url(r'^records/(?P<skill>(1?[0-9]|2[0-3]|99|100))/$', views.records),
    url(r'^records/(?P<skill>(1?[0-9]|2[0-3]|99|100))/'
        r'(?P<period>day|week|month|year|fivemin)/$', views.recordsfull),
    url(r'^records/(?P<skill>(1?[0-9]|2[0-3]|99|100))/'
        r'(?P<period>day|week|month|year|fivemin)/(?P<page>\d+)$',
        views.recordsfull),
    url(r'^tracker/updateplayer$', views.updateplayer),
    url(r'^tracker/recordstable$', views.recordstable),
    url(r'^tracker/skillstable$', views.skillstable),
    url(r'^tracker/lastupdate$', views.lastupdate),
    url(r'^tracker/searchperiod$', views.searchperiod),
]
