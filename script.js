document.addEventListener('DOMContentLoaded', () => {
    // Load sidebar content
    fetch('sidebar.html')
        .then(response => response.text())
        .then(data => {
            document.getElementById('sidebar').innerHTML = data;
            initializeSidebar();
        })
        .catch(error => console.error('Error loading sidebar:', error));
});

function initializeSidebar() {
    const menuToggle = document.querySelector('#menuToggle');
    const sidebar = document.querySelector('.sidebar');
    
    // Ensure elements exist before adding listeners
    if (!menuToggle || !sidebar) {
        console.error('Required elements not found');
        return;
    }

    // Handle menu toggle click
    menuToggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        sidebar.classList.toggle('active');
        
        // Update aria-expanded state
        const isExpanded = sidebar.classList.contains('active');
        menuToggle.setAttribute('aria-expanded', isExpanded.toString());
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                sidebar.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        }
    });

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (window.innerWidth > 768) {
                sidebar.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        }, 250);
    });
} 