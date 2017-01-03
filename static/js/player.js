/*
 * static/js/player.js
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

/* ID of the skill currently displayed in records table. */
var recordSkillId = 0;

$('#player-update').click(function(evt) {
    var player = document.location.pathname.substring(8);

    var i = player.indexOf('/');
    if (i != -1)
        player = player.substring(0, i);

    $.ajax({
        type: 'GET',
        url: '/tracker/updateplayer',
        data: {
            player: player
        },
        success: function(data) {
            if (data == '-1') {
                $('#player-update-result').html('This player was updated less'
                    + ' than 30s ago.<br>Please wait.');
            } else if (data == '-2') {
                $('#player-update-result').html('Player ' + player
                    + ' not found on Hiscores.');
            } else if (data == '-3') {
                $('#player-update-result').html('Could not reach the OSRS'
                    + ' Hiscores API. Please try again.');
            } else {
                $('#player-update-result').html('Player ' + player
                    + ' has been updated.');
                updateRecords(recordSkillId);
                updateSkillTable();
                fetchUpdateTime();
                setTimeout(function() {
                    $('#player-update-result').html('');
                }, 5000);
            }
        },
        failure: function(data) {
            $('#player-update-result').html('Update failed.');
        }
    });
});

$(document).ready(function(evt) {
    $('[data-toggle="tooltip"]').tooltip();
});

var updateRecords = function(skillid) {
    var match = document.location.pathname.match(/\/player\/(.*?)\//);

    $.ajax ({
        type: 'GET',
        url: '/tracker/recordstable',
        data: {
            player: match[1],
            skill_id: skillid
        },
        success: function(data) {
            if (data == '-2') {
            } else {
                $('#player-records').html(data);
            }
        },
        failure: function(data) {
        }
    });
}

/* Fetch HTML for player skill table from server and display it. */
var updateSkillTable = function() {
    var match = document.location.pathname.match(/\/player\/(.*)\/(.*)/);

    $.ajax ({
        type: 'GET',
        url: '/tracker/skillstable',
        data: {
            player: match[1],
            period: match[2] ? match[2] : 'week'
        },
        success: function(data) {
            if (data == '-2') {
            } else {
                $('#player-skills-table-wrapper').html(data);
                $('[data-toggle="tooltip"]').tooltip();
                $('#player-table-row-' + recordSkillId).addClass('active-row');
                setupRowListeners();
            }
        },
        failure: function(data) {
        }
    });
}

var fetchUpdateTime = function() {
    var match = document.location.pathname.match(/\/player\/(.*)\/(.*)/);

    $.ajax ({
        type: 'GET',
        url: '/tracker/lastupdate',
        data: {
            player: match[1],
        },
        success: function(data) {
            if (data == '-2') {
            } else {
                $('#player-last-update').html(data);
            }
        },
        failure: function(data) {
        }
    });
}

/* Show records for a skill when its icon is clicked. */
var setupRowListeners = function() {
    $('.player-table-skill').click(function(evt) {
        var skillid = parseInt(this.id.substring(19));

        $('.player-table-row').removeClass('active-row');
        $('#player-table-row-' + skillid).addClass('active-row');
        recordSkillId = skillid;
        updateRecords(skillid);
    });
}

/* Skill 0 (overall) is active by default. */
$('#player-table-row-0').addClass('active-row');

setupRowListeners();
