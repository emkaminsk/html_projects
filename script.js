document.addEventListener('DOMContentLoaded', () => {
    // Load sidebar content
    fetch('sidebar.html')
        .then(response => response.text())
        .then(data => {
            document.getElementById('sidebar').innerHTML = data;
            initializeSidebar();
            initializeActiveStates();
        })
        .catch(error => console.error('Error loading sidebar:', error));

    // Initialize interactive features
    initializeBackToTop();
    initializeStatCounters();
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

// Back to Top Button
function initializeBackToTop() {
    const backToTopButton = document.getElementById('backToTop');

    if (!backToTopButton) return;

    // Show/hide button based on scroll position
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopButton.classList.add('visible');
        } else {
            backToTopButton.classList.remove('visible');
        }
    });

    // Scroll to top on click
    backToTopButton.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Animated Statistics Counter
function initializeStatCounters() {
    const statNumbers = document.querySelectorAll('.stat-number');

    if (statNumbers.length === 0) return;

    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px'
    };

    const animateCounter = (element) => {
        const target = parseInt(element.getAttribute('data-target'));
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60fps
        let current = 0;

        const updateCounter = () => {
            current += increment;
            if (current < target) {
                element.textContent = Math.floor(current);
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = target;
            }
        };

        updateCounter();
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    statNumbers.forEach(stat => observer.observe(stat));
}

// Active State Indicators for Sidebar
function initializeActiveStates() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.sidebar a[href^="#"]');

    if (sections.length === 0 || navLinks.length === 0) return;

    const observerOptions = {
        threshold: 0.3,
        rootMargin: '-100px 0px -66%'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');

                // Remove active class from all links
                navLinks.forEach(link => {
                    link.classList.remove('active');
                });

                // Add active class to current link
                const activeLink = document.querySelector(`.sidebar a[href="#${id}"]`);
                if (activeLink) {
                    activeLink.classList.add('active');
                }
            }
        });
    }, observerOptions);

    sections.forEach(section => observer.observe(section));
} 