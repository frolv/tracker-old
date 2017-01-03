/*
 * static/js/records-full.js
 * Copyright (C) 2016-2017 Alexei Frolov
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

$('#navbar-records').addClass('navbar-active');

const USERS_PER_PAGE = 25;
var start = 0;

var buttonListeners = function() {
    $('#record-prev-button').click(function() {
        start -= USERS_PER_PAGE;
        fetchTable();
    });
    $('#record-next-button').click(function() {
        start += USERS_PER_PAGE;
        fetchTable();
    });
}

var fetchTable = function() {
    var match = document.location.pathname.match(/records\/(\d+)\/(\w+)/);

    $('#record-prev-button').prop('disabled', true);
    $('#record-next-button').prop('disabled', true);

    $.ajax({
        type: 'GET',
        url: '/tracker/fullrecords',
        data: {
            skill: match[1],
            period: match[2],
            after: start
        },
        success: function(data) {
            if (data == '-1') {
                $('#record-next-button').prop('disabled', true);
                $('#record-prev-button').prop('disabled', false);
            } else {
                $('#record-fulltable-wrapper').html(data);
                buttonListeners();
            }
        },
        failure: function() {
            enableButtons();
        }
    });
}

var enableButtons = function() {
    $('#record-next-button').prop('disabled', false);
    if (start == 0)
        $('#record-prev-button').prop('disabled', true);
    else
        $('#record-prev-button').prop('disabled', false);
}

buttonListeners();
