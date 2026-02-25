/**
 * HeroGeometric — Staggered entrance animations
 * Triggers CSS animations by adding the `.animate` class to hero elements.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Small delay so the page paint finishes first
    requestAnimationFrame(() => {
        // Animate each floating shape with staggered timing
        const shapes = document.querySelectorAll('.elegant-shape');
        shapes.forEach((shape, index) => {
            setTimeout(() => {
                shape.classList.add('animate');
            }, index * 150);  // 150 ms stagger between shapes
        });

        // Animate hero content elements (badge, title, subtitle)
        const heroElements = document.querySelectorAll(
            '.hero-badge, .hero-title, .hero-subtitle'
        );
        heroElements.forEach((el, index) => {
            setTimeout(() => {
                el.classList.add('animate');
            }, 400 + index * 200);  // start after shapes, 200 ms stagger
        });
    });
});
