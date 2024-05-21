document.addEventListener('DOMContentLoaded', function() {
    const isLoggedIn = document.querySelector('.fas.fa-user-circle');

    if (isLoggedIn) {
        const url = "updatable";
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.updatable_count > 0) {
                    const historyLink = document.getElementById('history-link');
                    const badge = document.createElement('span');
                    badge.className = 'absolute -top-1 -right-5 w-5 h-5 flex items-center justify-center text-xs font-bold text-red-100 bg-red-600 rounded-full hidden md:flex';
                    badge.textContent = data.updatable_count;
                    historyLink.appendChild(badge);

                    const historyLinkMobile = document.getElementById('history-link-mobile');
                    if (historyLinkMobile) {
                        const count = data.updatable_count;
                        const suffix = (count % 10 === 1 && count % 100 !== 11) ? 'atjauninājums' : 'atjauninājumi';
                        historyLinkMobile.innerHTML += ` <b>(${count} ${suffix})</b>`;
                    }
                }
            });
    }
});
