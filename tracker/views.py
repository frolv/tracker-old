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

# Create your views here.
def index(request):
    template = loader.get_template('tracker/index.html')
    return HttpResponse(template.render(request))

def account(request, user):
    try:
        username = RSAccount.objects.get(username__iexact=user).username
    except RSAccount.DoesNotExist:
        username = user

    template = loader.get_template('tracker/account.html')
    context = {
        'username': username,
    }

    return HttpResponse(template.render(context, request))
