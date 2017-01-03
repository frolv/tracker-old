/*
 * static/js/navbar.js
 * Copyright (C) 2016 Alexei Frolov
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

$('#search-username').on('invalid', function(evt) {
    this.setCustomValidity('Please enter a valid username.');
});

$('#search-username').on('input', function(evt) {
    this.setCustomValidity('');
});

$('#navbar-searchform').submit(function(evt) {
    evt.preventDefault();

    var user = $('#search-username').val();
    if (user.match(/^[a-zA-Z0-9_ ]{1,12}$/)) {
        var match = $('#search-period').html().match(/(\w+)/);
        document.location.href = '/player/' + user.replace(/ /g, '_') + '/'
                + match[0].toLowerCase();
    }
});

$('.search-period-dropdown').click(function(evt) {
    var period = this.id.substring(14);

    $('#search-period').html(period.charAt(0).toUpperCase() + period.slice(1)
        + ' <span class="caret"></span>');

    $.ajax({
        type: 'POST',
        url: '/tracker/searchperiod',
        beforeSend: function(req) {
            req.setRequestHeader("X-CSRFToken", Cookies.get('csrftoken'));
        },
        data: {
            searchperiod: period
        }
    });
});
