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

    // Add initial state class to sidebar
    sidebar.classList.add('sidebar-closed');

    menuToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        sidebar.classList.toggle('active');
        // Toggle aria-expanded for accessibility
        menuToggle.setAttribute('aria-expanded', 
            sidebar.classList.contains('active').toString());
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

    // Update resize handler for smoother transitions
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('active');
                projectsToggle.classList.remove('active');
                submenu.classList.remove('active');
            }
        }, 250); // Debounce resize events
    });
} 