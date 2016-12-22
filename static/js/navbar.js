$('#searchform').submit(function(evt) {
    evt.preventDefault();

    var user = $('#search-username').val();
    document.location.href = '/account/' + user;
});
