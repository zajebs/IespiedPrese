function loadPage(page) {
    $.get('/history', { page: page }, function(data) {
        $('#downloads-table-container').html(data);
    });
}

$(document).ready(function() {
    $(document).on('click', '.pagination-link', function(event) {
        event.preventDefault();
        var page = $(this).data('page');
        loadPage(page);
    });
});