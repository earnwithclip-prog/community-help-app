/**
 * Community Help Request Management System
 * Frontend JavaScript — Form validation, UX enhancements & animations
 */

document.addEventListener("DOMContentLoaded", function () {

    // ── Smooth scroll behavior ──
    document.documentElement.style.scrollBehavior = "smooth";

    // ── Form Validation ──
    const helpForm = document.getElementById("helpForm");
    if (helpForm) {
        helpForm.addEventListener("submit", function (e) {
            const fields = helpForm.querySelectorAll("[required]");
            let isValid = true;

            fields.forEach(function (field) {
                if (!field.value.trim()) {
                    field.classList.add("is-invalid");
                    isValid = false;
                } else {
                    field.classList.remove("is-invalid");
                    field.classList.add("is-valid");
                }
            });

            // Phone validation: only digits, spaces, hyphens, plus
            const phoneField = document.getElementById("phone");
            if (phoneField && phoneField.value.trim()) {
                const phoneRegex = /^[\d\s\-\+\(\)]{7,15}$/;
                if (!phoneRegex.test(phoneField.value.trim())) {
                    phoneField.classList.add("is-invalid");
                    isValid = false;
                }
            }

            if (!isValid) {
                e.preventDefault();
                e.stopPropagation();

                // Scroll to first invalid field
                const firstInvalid = helpForm.querySelector(".is-invalid");
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
                    firstInvalid.focus();
                }
            } else {
                // Show loading state
                const submitBtn = document.getElementById("submitBtn");
                if (submitBtn) {
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = "0.8";
                }
            }
        });

        // Real-time validation feedback
        const formFields = helpForm.querySelectorAll(".form-control, .form-select");
        formFields.forEach(function (field) {
            field.addEventListener("input", function () {
                if (field.value.trim()) {
                    field.classList.remove("is-invalid");
                    field.classList.add("is-valid");
                }
            });

            field.addEventListener("blur", function () {
                if (field.hasAttribute("required") && !field.value.trim()) {
                    field.classList.add("is-invalid");
                }
            });
        });
    }

    // ── Character Counter for Description ──
    const descriptionField = document.getElementById("description");
    const charCounter = document.getElementById("charCounter");
    if (descriptionField && charCounter) {
        descriptionField.addEventListener("input", function () {
            const len = descriptionField.value.length;
            const max = descriptionField.maxLength || 500;
            charCounter.textContent = len + " / " + max;

            if (len > max * 0.85) {
                charCounter.classList.add("warning");
            } else {
                charCounter.classList.remove("warning");
            }
        });
    }

    // ── Auto-dismiss alerts after 5 seconds ──
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // ── Add confirm dialog for status toggle ──
    const actionForms = document.querySelectorAll(".action-btn");
    actionForms.forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            const action = btn.textContent.trim();
            const row = btn.closest("tr");
            const name = row ? row.querySelector("td:nth-child(2)").textContent.trim() : "this request";

            if (!confirm("Are you sure you want to " + action.toLowerCase() + " the request from " + name + "?")) {
                e.preventDefault();
            }
        });
    });

    // ── Tooltip initialization ──
    const tooltipTriggerList = document.querySelectorAll('[title]');
    tooltipTriggerList.forEach(function (el) {
        if (el.title) {
            new bootstrap.Tooltip(el, {
                placement: "top",
                trigger: "hover"
            });
        }
    });

    // ── Filter form auto-submit on change (Admin page) ──
    const filterForm = document.getElementById("filterForm");
    if (filterForm) {
        const selects = filterForm.querySelectorAll("select");
        selects.forEach(function (sel) {
            sel.addEventListener("change", function () {
                filterForm.submit();
            });
        });
    }

    // ── Intersection Observer for scroll-reveal ──
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -40px 0px"
    };

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe stat cards
    document.querySelectorAll(".stat-card").forEach(function (card, index) {
        card.style.opacity = "0";
        card.style.transform = "translateY(16px)";
        card.style.transition = "all 0.5s cubic-bezier(0.4, 0, 0.2, 1) " + (index * 0.08) + "s";
        observer.observe(card);
    });
});
