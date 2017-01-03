/*
 * static/js/nottracked.js
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

$('#track-player').click(function(evt) {
    var player = document.location.pathname.substring(8);

    var i = player.indexOf('/');
    if (i != -1)
        player = player.substring(0, i);

    $.ajax ({
        type: 'GET',
        url: '/tracker/updateplayer',
        data: {
            player: player
        },
        success: function(data) {
            if (data == '-1') {
                $('#track-player-result').html('This player was updated less'
                    + ' than 30s ago. Please wait.');
            } else if (data == '-2') {
                $('#track-player-result').html('Player ' + player
                    + ' not found on Hiscores.');
            } else if (data == '-3') {
                $('#track-player-result').html('Could not reach the OSRS'
                    + ' Hiscores API. Please try again.');
            } else if (data == '-4') {
                $('#track-player-result').html('Invalid username.');
            } else {
                document.location.reload(true);
            }
        },
        failure: function(data) {
            $('#track-player-result').html('Update failed.');
        }
    });
});
