function loadPage(page) {
    fetch(`/history?page=${page}`)
        .then(response => response.text())
        .then(data => {
            document.getElementById('downloads-table-container').innerHTML = data;
        })
        .catch(error => console.error('Error:', error));
}

document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('pagination-link')) {
            event.preventDefault();
            var page = event.target.getAttribute('data-page');
            loadPage(page);
        }
    });
});
