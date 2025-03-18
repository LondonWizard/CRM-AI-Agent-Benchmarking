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