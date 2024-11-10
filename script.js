document.addEventListener('DOMContentLoaded', () => {
    // Load sidebar content
    fetch('sidebar.html')
        .then(response => response.text())
        .then(data => {
            document.getElementById('sidebar').innerHTML = data;
            initializeSidebar();
        });
});

function initializeSidebar() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.querySelector('.sidebar');
    const projectsToggle = document.querySelector('.projects-toggle');
    const submenu = document.querySelector('.submenu');

    // Ensure sidebar starts closed on mobile
    if (window.innerWidth <= 768) {
        sidebar.classList.remove('active');
        projectsToggle.classList.remove('active');
        submenu.classList.remove('active');
    }

    menuToggle.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent event from bubbling up
        sidebar.classList.toggle('active');
    });

    projectsToggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation(); // Prevent event from bubbling up
        projectsToggle.classList.toggle('active');
        submenu.classList.toggle('active');
    });

    // Close sidebar when clicking on a link (mobile only)
    const menuLinks = sidebar.querySelectorAll('a:not(.projects-toggle)');
    menuLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('active');
                projectsToggle.classList.remove('active');
                submenu.classList.remove('active');
            }
        });
    });

    // Close sidebar when clicking outside
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                sidebar.classList.remove('active');
                projectsToggle.classList.remove('active');
                submenu.classList.remove('active');
            }
        }
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('active');
            projectsToggle.classList.remove('active');
            submenu.classList.remove('active');
        }
    });
} 