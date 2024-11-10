document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.querySelector('.sidebar');
    const projectsToggle = document.querySelector('.projects-toggle');
    const submenu = document.querySelector('.submenu');

    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });

    projectsToggle.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent default anchor behavior
        projectsToggle.classList.toggle('active');
        submenu.classList.toggle('active');
    });

    // Close sidebar when clicking outside
    document.addEventListener('click', (e) => {
        if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
            sidebar.classList.remove('active');
            projectsToggle.classList.remove('active');
            submenu.classList.remove('active');
        }
    });
}); 