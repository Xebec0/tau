// Landing page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Smooth Scrolling for Navigation Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#' || !targetId.startsWith('#')) return;
            
            e.preventDefault();
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Testimonial Slider
    const testimonialCards = document.querySelectorAll('.testimonial-card');
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');
    let currentIndex = 0;

    // Function to update the visible testimonials based on screen size
    function updateTestimonials() {
        const isMobile = window.innerWidth < 768;
        const isTablet = window.innerWidth >= 768 && window.innerWidth < 992;
        
        testimonialCards.forEach((card, index) => {
            card.style.display = 'none';
        });
        
        if (isMobile) {
            // Show only one testimonial on mobile
            testimonialCards[currentIndex].style.display = 'block';
        } else if (isTablet) {
            // Show two testimonials on tablet
            testimonialCards[currentIndex].style.display = 'block';
            if (testimonialCards[currentIndex + 1]) {
                testimonialCards[currentIndex + 1].style.display = 'block';
            } else {
                testimonialCards[0].style.display = 'block';
            }
        } else {
            // Show all testimonials on desktop
            testimonialCards.forEach(card => {
                card.style.display = 'block';
            });
        }
    }

    // Initialize testimonials
    if (testimonialCards.length > 0 && prevBtn && nextBtn) {
        updateTestimonials();

        // Update testimonials when window is resized
        window.addEventListener('resize', updateTestimonials);

        // Previous button click handler
        prevBtn.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex--;
            } else {
                currentIndex = testimonialCards.length - 1;
            }
            updateTestimonials();
        });

        // Next button click handler
        nextBtn.addEventListener('click', () => {
            if (currentIndex < testimonialCards.length - 1) {
                currentIndex++;
            } else {
                currentIndex = 0;
            }
            updateTestimonials();
        });
    }

    // Animation on scroll
    function animateOnScroll() {
        const elements = document.querySelectorAll('.feature-card, .benefit-item, .testimonial-card, .dashboard-card');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.2;
            
            if (elementPosition < screenPosition) {
                element.classList.add('animate');
            }
        });
    }
    
    // Run animation on page load
    animateOnScroll();
    
    // Run animation on scroll
    window.addEventListener('scroll', animateOnScroll);
    
    // Testimonial slider functionality
    const testimonialSlider = document.querySelector('.testimonials-slider');
    const prevButton = document.querySelector('.prev-button');
    const nextButton = document.querySelector('.next-button');
    
    if (testimonialSlider && prevButton && nextButton) {
        let currentSlide = 0;
        const testimonials = document.querySelectorAll('.testimonial-card');
        const totalSlides = testimonials.length;
        
        // Hide all testimonials except the first one on mobile
        function updateSlider() {
            if (window.innerWidth < 768) {
                testimonials.forEach((testimonial, index) => {
                    testimonial.style.display = index === currentSlide ? 'block' : 'none';
                });
            } else {
                testimonials.forEach(testimonial => {
                    testimonial.style.display = 'block';
                });
            }
        }
        
        // Initialize slider
        updateSlider();
        
        // Previous slide
        prevButton.addEventListener('click', function() {
            if (window.innerWidth < 768) {
                currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
                updateSlider();
            }
        });
        
        // Next slide
        nextButton.addEventListener('click', function() {
            if (window.innerWidth < 768) {
                currentSlide = (currentSlide + 1) % totalSlides;
                updateSlider();
            }
        });
        
        // Update slider on window resize
        window.addEventListener('resize', updateSlider);
    }
}); 