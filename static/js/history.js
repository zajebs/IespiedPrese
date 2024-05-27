document.addEventListener('click', function(event) {
    if (event.target.classList.contains('pagination-link')) {
        event.preventDefault();
        var page = event.target.getAttribute('data-page');
        loadPage(page);
    }
});

function loadPage(page) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/account?page=' + page, true);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            document.getElementById('downloads-table-container').innerHTML = xhr.responseText;
        }
    };
    xhr.send();
}
