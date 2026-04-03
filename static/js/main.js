document.addEventListener('DOMContentLoaded', function () {

    const current = window.location.pathname;
    const links = document.querySelectorAll('.nav-link');

    links.forEach(link => {
        if (link.getAttribute('href') === current) {
            link.classList.add('active');
        }
    });

});