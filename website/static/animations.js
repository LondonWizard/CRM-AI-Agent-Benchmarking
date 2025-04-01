// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // GSAP animations
    
    // Stagger animation for navigation links
    gsap.from('nav a', {
        opacity: 0,
        y: -20,
        stagger: 0.1,
        duration: 0.5,
        ease: 'power1.out',
        delay: 0.5
    });
    
    // Content animation
    gsap.from('.content', {
        opacity: 0,
        y: 30,
        duration: 0.7,
        ease: 'back.out(1.2)'
    });
    
    // Button hover animations
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', () => {
            gsap.to(button, {
                scale: 1.05,
                duration: 0.2
            });
        });
        
        button.addEventListener('mouseleave', () => {
            gsap.to(button, {
                scale: 1,
                duration: 0.2
            });
        });
    });
    
    // Form field animations
    const formFields = document.querySelectorAll('input[type="text"], input[type="password"]');
    formFields.forEach(field => {
        // Initial state animation
        gsap.from(field, {
            opacity: 0,
            x: -20,
            duration: 0.5,
            delay: 0.3,
            stagger: 0.1
        });
        
        // Focus animations
        field.addEventListener('focus', () => {
            gsap.to(field, {
                boxShadow: '0 0 0 3px rgba(114, 137, 218, 0.3)',
                duration: 0.3
            });
        });
        
        field.addEventListener('blur', () => {
            gsap.to(field, {
                boxShadow: 'none',
                duration: 0.3
            });
        });
    });
    
    // Table row animations for leaderboard
    const tableRows = document.querySelectorAll('tbody tr');
    gsap.from(tableRows, {
        opacity: 0,
        y: 20,
        stagger: 0.1,
        duration: 0.4,
        ease: 'power1.out',
        delay: 0.3
    });
    
    // Flash message animations
    const messages = document.querySelectorAll('.message');
    if (messages.length > 0) {
        gsap.from(messages, {
            opacity: 0,
            y: -10,
            duration: 0.5,
            stagger: 0.1
        });
        
        // Auto-dismiss messages after 5 seconds
        setTimeout(() => {
            gsap.to(messages, {
                opacity: 0,
                y: -20,
                stagger: 0.1,
                duration: 0.5,
                onComplete: () => {
                    messages.forEach(msg => {
                        msg.style.height = '0';
                        msg.style.marginBottom = '0';
                        msg.style.padding = '0';
                        msg.style.overflow = 'hidden';
                    });
                }
            });
        }, 5000);
    }
    
    // Add particle background effect (if on homepage)
    if (document.querySelector('h2') && document.querySelector('h2').textContent.includes('Welcome')) {
        createParticleBackground();
    }
});

// Create a subtle particle background effect
function createParticleBackground() {
    const content = document.querySelector('.content');
    const particleContainer = document.createElement('div');
    particleContainer.className = 'particle-background';
    particleContainer.style.position = 'absolute';
    particleContainer.style.top = '0';
    particleContainer.style.left = '0';
    particleContainer.style.width = '100%';
    particleContainer.style.height = '100%';
    particleContainer.style.overflow = 'hidden';
    particleContainer.style.zIndex = '-1';
    particleContainer.style.opacity = '0.4';
    
    content.style.position = 'relative';
    content.insertBefore(particleContainer, content.firstChild);
    
    // Create particles
    for (let i = 0; i < 30; i++) {
        createParticle(particleContainer);
    }
}

function createParticle(container) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.position = 'absolute';
    particle.style.width = Math.random() * 5 + 2 + 'px';
    particle.style.height = particle.style.width;
    particle.style.backgroundColor = 'var(--accent)';
    particle.style.borderRadius = '50%';
    particle.style.opacity = Math.random() * 0.5 + 0.1;
    
    // Random initial position
    const posX = Math.random() * 100;
    const posY = Math.random() * 100;
    particle.style.left = posX + '%';
    particle.style.top = posY + '%';
    
    container.appendChild(particle);
    
    // Animate particle with GSAP
    gsap.to(particle, {
        x: (Math.random() - 0.5) * 100,
        y: (Math.random() - 0.5) * 100,
        opacity: Math.random() * 0.5,
        duration: Math.random() * 20 + 10,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut'
    });
}

// Enhanced animations for AI Agents Challenge website
document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS (Animate On Scroll) effect equivalent
    initScrollAnimations();
    
    // Add hover effects to cards
    addCardHoverEffects();
    
    // Add nav hover effects
    enhanceNavigation();
    
    // Add smooth page transitions
    initPageTransitions();
    
    // Add parallax effects to hero section
    initParallaxEffect();
    
    // Initialize countup animations for numbers/stats
    initCountUpAnimations();
    
    // Add typing effect to headings where appropriate
    initTypingEffects();
});

// Animate elements as they scroll into view
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('appeared');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    animatedElements.forEach(element => {
        observer.observe(element);
        // Set initial state
        element.classList.add('will-animate');
    });
}

// Add smooth hover effects to cards
function addCardHoverEffects() {
    const cards = document.querySelectorAll('.glass-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
            this.style.boxShadow = '0 12px 30px rgba(0, 0, 0, 0.4)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.25)';
        });
    });
}

// Enhanced navigation interactions
function enhanceNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.letterSpacing = '0.5px';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.letterSpacing = 'normal';
        });
    });
}

// Smooth page transitions
function initPageTransitions() {
    const contentArea = document.querySelector('.content');
    if (!contentArea) return;
    
    // Add exit class when navigating away
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (link && link.href.includes(window.location.hostname)) {
            e.preventDefault();
            
            // Add exit animation
            contentArea.classList.add('exit-animation');
            
            // Navigate after animation completes
            setTimeout(function() {
                window.location.href = link.href;
            }, 300);
        }
    });
    
    // Add entrance animation when page loads
    contentArea.classList.add('enter-animation');
}

// Parallax effect for hero section
function initParallaxEffect() {
    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;
    
    window.addEventListener('scroll', function() {
        const scrollPosition = window.scrollY;
        heroSection.style.backgroundPositionY = -scrollPosition * 0.2 + 'px';
        
        // Subtle scale effect on title
        const heroTitle = document.querySelector('.hero-title');
        if (heroTitle) {
            const scale = 1 + Math.min(scrollPosition * 0.0005, 0.1);
            heroTitle.style.transform = `scale(${scale})`;
        }
    });
}

// CountUp animation for numbers
function initCountUpAnimations() {
    const countElements = document.querySelectorAll('.count-up');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const targetNumber = parseInt(target.getAttribute('data-target'), 10);
                animateCount(target, targetNumber);
                observer.unobserve(target);
            }
        });
    }, {
        threshold: 0.5
    });
    
    countElements.forEach(element => {
        observer.observe(element);
    });
}

function animateCount(element, target) {
    let current = 0;
    const duration = 2000; // ms
    const step = target / (duration / 16);
    
    const timer = setInterval(() => {
        current += step;
        if (current > target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// Typing effect for headings
function initTypingEffects() {
    const typedElements = document.querySelectorAll('.typed-text');
    
    typedElements.forEach(element => {
        const text = element.textContent;
        element.textContent = '';
        element.style.borderRight = '2px solid #7289da';
        
        let i = 0;
        const interval = setInterval(() => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(interval);
                element.style.borderRight = 'none';
            }
        }, 100);
    });
} 