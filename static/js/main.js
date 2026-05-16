console.log('UCPC Poetry Archive Loaded');

document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || 
            (currentPath === '/' && href === '/') ||
            (currentPath.startsWith('/poet') && href === '/poets') ||
            (currentPath.startsWith('/view') && href === '/poets')) {
            link.classList.add('active');
        }
    });
});
