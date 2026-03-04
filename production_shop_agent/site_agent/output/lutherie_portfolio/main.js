/* ============================================================
   Hartwell Guitars — main.js
   Handles: mobile nav toggle, smooth scroll,
            image lightbox (gallery), contact form validation
   ============================================================ */

'use strict';

/* ----------------------------------------------------------
   Utility helpers
   ---------------------------------------------------------- */

/**
 * Shorthand querySelector
 * @param {string} selector
 * @param {Element} [scope=document]
 * @returns {Element|null}
 */
const qs = (selector, scope = document) => scope.querySelector(selector);

/**
 * Shorthand querySelectorAll (returns real Array)
 * @param {string} selector
 * @param {Element} [scope=document]
 * @returns {Element[]}
 */
const qsa = (selector, scope = document) =>
  Array.from(scope.querySelectorAll(selector));

/**
 * Add multiple event listeners to one element
 * @param {Element} el
 * @param {string[]} events
 * @param {Function} handler
 */
const onEvents = (el, events, handler) =>
  events.forEach((evt) => el.addEventListener(evt, handler));

/* ----------------------------------------------------------
   1. Mobile Nav Toggle
   ---------------------------------------------------------- */
function initMobileNav() {
  const toggle = qs('[data-nav-toggle]');
  const nav    = qs('[data-nav-menu]');

  if (!toggle || !nav) return;

  toggle.setAttribute('aria-expanded', 'false');

  toggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('nav-open');
    toggle.classList.toggle('nav-toggle--active', isOpen);
    toggle.setAttribute('aria-expanded', String(isOpen));
    // Prevent body scroll while menu is open
    document.body.classList.toggle('no-scroll', isOpen);
  });

  // Close nav when a nav link is clicked (single-page or anchor nav)
  qsa('a', nav).forEach((link) => {
    link.addEventListener('click', () => {
      nav.classList.remove('nav-open');
      toggle.classList.remove('nav-toggle--active');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('no-scroll');
    });
  });

  // Close nav on outside click
  document.addEventListener('click', (e) => {
    if (
      nav.classList.contains('nav-open') &&
      !nav.contains(e.target) &&
      !toggle.contains(e.target)
    ) {
      nav.classList.remove('nav-open');
      toggle.classList.remove('nav-toggle--active');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('no-scroll');
    }
  });

  // Close nav on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && nav.classList.contains('nav-open')) {
      nav.classList.remove('nav-open');
      toggle.classList.remove('nav-toggle--active');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('no-scroll');
      toggle.focus();
    }
  });
}

/* ----------------------------------------------------------
   2. Smooth Scroll
   ---------------------------------------------------------- */
function initSmoothScroll() {
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;

    const targetId = link.getAttribute('href');
    if (targetId === '#') return;

    const target = qs(targetId);
    if (!target) return;

    e.preventDefault();

    // Account for a fixed header if present
    const header      = qs('[data-site-header]');
    const headerHeight = header ? header.offsetHeight : 0;
    const targetTop   = target.getBoundingClientRect().top + window.scrollY - headerHeight;

    window.scrollTo({ top: targetTop, behavior: 'smooth' });

    // Move focus to target for accessibility
    target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
  });
}

/* ----------------------------------------------------------
   3. Image Lightbox (Gallery)
   ---------------------------------------------------------- */
function initLightbox() {
  // Expects gallery items marked with [data-lightbox]
  // Each item should have data-lightbox-src and optionally data-lightbox-caption
  const triggers = qsa('[data-lightbox]');
  if (!triggers.length) return;

  /* ---- Build lightbox DOM ---- */
  const overlay = document.createElement('div');
  overlay.id = 'hw-lightbox';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', 'Image lightbox');
  overlay.setAttribute('tabindex', '-1');
  overlay.innerHTML = `
    <div class="lb-backdrop"></div>
    <div class="lb-container">
      <button class="lb-btn lb-prev" aria-label="Previous image">&#8249;</button>
      <figure class="lb-figure">
        <img class="lb-img" src="" alt="" />
        <figcaption class="lb-caption"></figcaption>
      </figure>
      <button class="lb-btn lb-next" aria-label="Next image">&#8250;</button>
      <button class="lb-btn lb-close" aria-label="Close lightbox">&times;</button>
    </div>
  `;
  document.body.appendChild(overlay);

  const lbImg      = qs('.lb-img',     overlay);
  const lbCaption  = qs('.lb-caption', overlay);
  const lbPrev     = qs('.lb-prev',    overlay);
  const lbNext     = qs('.lb-next',    overlay);
  const lbClose    = qs('.lb-close',   overlay);
  const lbBackdrop = qs('.lb-backdrop',overlay);

  let currentIndex  = 0;
  let lastFocused   = null;

  /* ---- Helpers ---- */

  function showSlide(index) {
    const item    = triggers[index];
    const src     = item.dataset.lightboxSrc || item.src || item.href || '';
    const alt     = item.dataset.lightboxAlt || item.alt || `Gallery image ${index + 1}`;
    const caption = item.dataset.lightboxCaption || '';

    lbImg.classList.add('lb-img--loading');
    lbImg.src = src;
    lbImg.alt = alt;
    lbCaption.textContent = caption;

    lbImg.onload = () => lbImg.classList.remove('lb-img--loading');

    // Show/hide prev-next based on count
    lbPrev.hidden = triggers.length <= 1;
    lbNext.hidden = triggers.length <= 1;
  }

  function openLightbox(index) {
    lastFocused  = document.activeElement;
    currentIndex = index;
    showSlide(currentIndex);
    overlay.classList.add('lb-open');
    document.body.classList.add('no-scroll');
    overlay.focus();
  }

  function closeLightbox() {
    overlay.classList.remove('lb-open');
    document.body.classList.remove('no-scroll');
    if (lastFocused) lastFocused.focus();
  }

  function goPrev() {
    currentIndex = (currentIndex - 1 + triggers.length) % triggers.length;
    showSlide(currentIndex);
  }

  function goNext() {
    currentIndex = (currentIndex + 1) % triggers.length;
    showSlide(currentIndex);
  }

  /* ---- Event listeners ---- */

  triggers.forEach((trigger, idx) => {
    // Make non-interactive elements keyboard accessible
    if (!['A', 'BUTTON'].includes(trigger.tagName)) {
      trigger.setAttribute('role', 'button');
      trigger.setAttribute('tabindex', '0');
    }

    onEvents(trigger, ['click', 'keydown'], (e) => {
      if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') return;
      e.preventDefault();
      openLightbox(idx);
    });
  });

  lbClose.addEventListener('click', closeLightbox);
  lbBackdrop.addEventListener('click', closeLightbox);
  lbPrev.addEventListener('click', goPrev);
  lbNext.addEventListener('click', goNext);

  overlay.addEventListener('keydown', (e) => {
    switch (e.key) {
      case 'Escape':    closeLightbox(); break;
      case 'ArrowLeft': goPrev();        break;
      case 'ArrowRight':goNext();        break;
    }
  });

  /* Touch / swipe support */
  let touchStartX = 0;

  overlay.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
  }, { passive: true });

  overlay.addEventListener('touchend', (e) => {
    const deltaX = e.changedTouches[0].screenX - touchStartX;
    if (Math.abs(deltaX) > 50) {
      deltaX < 0 ? goNext() : goPrev();
    }
  }, { passive: true });
}

/* ----------------------------------------------------------
   4. Contact Form Validation
   ---------------------------------------------------------- */
function initContactForm() {
  const form = qs('[data-contact-form]');
  if (!form) return;

  /* ---- Validation rules ---- */
  const rules = {
    name: {
      validate: (v) => v.trim().length >= 2,
      message:  'Please enter your full name (at least 2 characters).',
    },
    email: {
      validate: (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()),
      message:  'Please enter a valid email address.',
    },
    phone: {
      // Optional field — only validate format if a value is provided
      validate: (v) => v.trim() === '' || /^[\d\s\-\+\(\)]{7,}$/.test(v.trim()),
      message:  'Please enter a valid phone number.',
    },
    message: {
      validate: (v) => v.trim().length >= 10,
      message:  'Please enter a message (at least 10 characters).',
    },
  };

  /* ---- Helper: show / clear error for a field ---- */

  function getErrorEl(field) {
    // Look for a sibling [data-error] element, or create one
    let errEl = qs(`[data-error="${field.name}"]`, form);
    if (!errEl) {
      errEl = document.createElement('span');
      errEl.dataset.error = field.name;
      errEl.setAttribute('role', 'alert');
      errEl.className = 'form-error';
      field.parentNode.appendChild(errEl);
    }
    return errEl;
  }

  function showError(field, message) {
    field.classList.add('field--invalid');
    field.classList.remove('field--valid');
    field.setAttribute('aria-invalid', 'true');
    const errEl = getErrorEl(field);
    errEl.textContent = message;
    errEl.hidden = false;
  }

  function clearError(field) {
    field.classList.remove('field--invalid');
    field.classList.add('field--valid');
    field.setAttribute('aria-invalid', 'false');
    const errEl = getErrorEl(field);
    errEl.textContent = '';
    errEl.hidden = true;
  }

  function validateField(field) {
    const rule = rules[field.name];
    if (!rule) return true; // no rule = always valid

    if (rule.validate(field.value)) {
      clearError(field);
      return true;
    } else {
      showError(field, rule.message);
      return false;
    }
  }

  /* ---- Live validation on blur / input ---- */
  qsa('input, textarea, select', form).forEach((field) => {
    // Validate when user leaves a field
    field.addEventListener('blur', () => validateField(field));
    // Clear error as user types (after it has been shown)
    field.addEventListener('input', () => {
      if (field.classList.contains('field--invalid')) {
        validateField(field);
      }
    });
  });

  /* ---- Form submit ---- */
  form.addEventListener('submit', (e) => {
    e.preventDefault();

    let isValid = true;

    // Validate every field that has a rule
    qsa('input, textarea, select', form).forEach((field) => {
      if (!validateField(field)) isValid = false;
    });

    if (!isValid) {
      // Focus first invalid field
      const firstInvalid = qs('.field--invalid', form);
      if (firstInvalid) firstInvalid.focus();
      return;
    }

    /* ---- Simulate async form submission ---- */
    const submitBtn    = qs('[type="submit"]', form);
    const originalText = submitBtn.textContent;

    submitBtn.disabled    = true;
    submitBtn.textContent = 'Sending…';

    // Replace this block with your real fetch/XHR call
    setTimeout(() => {
      showFormSuccess(form, submitBtn, originalText);
    }, 1200);
  });

  /* ---- Success state ---- */
  function showFormSuccess(form, btn, originalBtnText) {
    // Look for an existing success message container
    let successMsg = qs('[data-form-success]', form);
    if (!successMsg) {
      successMsg = document.createElement('p');
      successMsg.dataset.formSuccess = '';
      successMsg.className = 'form-success';
      successMsg.setAttribute('role', 'status');
      form.appendChild(successMsg);
    }

    successMsg.textContent =
      "Thank you for reaching out! We'll be in touch within one business day.";
    successMsg.hidden = false;

    // Reset fields
    form.reset();
    qsa('input, textarea, select', form).forEach((f) => {
      f.classList.remove('field--valid', 'field--invalid');
      f.removeAttribute('aria-invalid');
    });

    btn.disabled    = false;
    btn.textContent = originalBtnText;

    // Hide success message after 8 s
    setTimeout(() => {
      successMsg.hidden = true;
    }, 8000);
  }
}

/* ----------------------------------------------------------
   5. Header scroll shadow
      Adds a class to the header when the page is scrolled
   ---------------------------------------------------------- */
function initHeaderScroll() {
  const header = qs('[data-site-header]');
  if (!header) return;

  const onScroll = () => {
    header.classList.toggle('header--scrolled', window.scrollY > 10);
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll(); // run once on load
}

/* ----------------------------------------------------------
   6. Animate elements on scroll (Intersection Observer)
      Add class="hw-reveal" to any element you want to
      fade-in when it enters the viewport.
   ---------------------------------------------------------- */
function initRevealOnScroll() {
  const items = qsa('.hw-reveal');
  if (!items.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('hw-reveal--visible');
          observer.unobserve(entry.target); // animate only once
        }
      });
    },
    { threshold: 0.15 }
  );

  items.forEach((el) => observer.observe(el));
}

/* ----------------------------------------------------------
   Init — run everything after the DOM is ready
   ---------------------------------------------------------- */
function init() {
  initMobileNav();
  initSmoothScroll();
  initLightbox();
  initContactForm();
  initHeaderScroll();
  initRevealOnScroll();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  // DOM already parsed (script is deferred or at bottom of body)
  init();
}