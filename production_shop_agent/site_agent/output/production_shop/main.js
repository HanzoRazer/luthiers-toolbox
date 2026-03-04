/**
 * The Production Shop — main.js
 * Handles: mobile nav toggle, smooth scroll, sticky header,
 *          feature tab switcher, contact form validation
 */

(function () {
  "use strict";

  /* =========================================================
     CONSTANTS & CACHED ELEMENTS
  ========================================================= */
  const STICKY_CLASS = "header--sticky";
  const NAV_OPEN_CLASS = "nav--open";
  const TAB_ACTIVE_CLASS = "tab--active";
  const PANEL_ACTIVE_CLASS = "tab-panel--active";
  const SCROLL_THRESHOLD = 60; // px before header becomes sticky

  const header = document.querySelector(".site-header");
  const navToggle = document.querySelector(".nav-toggle");
  const navMenu = document.querySelector(".site-nav");
  const body = document.body;

  /* =========================================================
     UTILITY: throttle
     Limits how often a function fires during rapid events
  ========================================================= */
  function throttle(fn, wait) {
    let lastTime = 0;
    return function (...args) {
      const now = Date.now();
      if (now - lastTime >= wait) {
        lastTime = now;
        fn.apply(this, args);
      }
    };
  }

  /* =========================================================
     UTILITY: debounce
     Delays function execution until after a burst of events
  ========================================================= */
  function debounce(fn, wait) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), wait);
    };
  }

  /* =========================================================
     MOBILE NAV TOGGLE
     Toggles aria-expanded, nav open class, and body scroll lock
  ========================================================= */
  function initMobileNav() {
    if (!navToggle || !navMenu) return;

    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-controls", "site-nav");
    navMenu.setAttribute("id", "site-nav");

    navToggle.addEventListener("click", function () {
      const isOpen = body.classList.toggle(NAV_OPEN_CLASS);
      navToggle.setAttribute("aria-expanded", String(isOpen));
      navToggle.setAttribute("aria-label", isOpen ? "Close menu" : "Open menu");
      // Prevent background scroll while menu is open
      body.style.overflow = isOpen ? "hidden" : "";
    });

    // Close nav when a nav link is clicked (single-page style)
    navMenu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeNav);
    });

    // Close nav when clicking outside of it
    document.addEventListener("click", function (e) {
      if (
        body.classList.contains(NAV_OPEN_CLASS) &&
        !navMenu.contains(e.target) &&
        !navToggle.contains(e.target)
      ) {
        closeNav();
      }
    });

    // Close nav on Escape key
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && body.classList.contains(NAV_OPEN_CLASS)) {
        closeNav();
        navToggle.focus();
      }
    });

    // Close nav on resize to desktop width
    window.addEventListener(
      "resize",
      debounce(function () {
        if (window.innerWidth >= 768) {
          closeNav();
        }
      }, 200)
    );
  }

  function closeNav() {
    body.classList.remove(NAV_OPEN_CLASS);
    if (navToggle) {
      navToggle.setAttribute("aria-expanded", "false");
      navToggle.setAttribute("aria-label", "Open menu");
    }
    body.style.overflow = "";
  }

  /* =========================================================
     STICKY HEADER
     Adds a class to the header after scrolling past threshold
  ========================================================= */
  function initStickyHeader() {
    if (!header) return;

    function handleScroll() {
      if (window.scrollY > SCROLL_THRESHOLD) {
        header.classList.add(STICKY_CLASS);
      } else {
        header.classList.remove(STICKY_CLASS);
      }
    }

    window.addEventListener("scroll", throttle(handleScroll, 100), {
      passive: true,
    });

    // Run once on load in case page is already scrolled
    handleScroll();
  }

  /* =========================================================
     SMOOTH SCROLL
     Intercepts clicks on anchor links and scrolls smoothly,
     accounting for sticky header height
  ========================================================= */
  function initSmoothScroll() {
    document.addEventListener("click", function (e) {
      // Walk up the DOM to find an <a> tag if a child element was clicked
      const anchor = e.target.closest("a[href^='#']");
      if (!anchor) return;

      const targetId = anchor.getAttribute("href");
      if (!targetId || targetId === "#") return;

      const target = document.querySelector(targetId);
      if (!target) return;

      e.preventDefault();

      const headerHeight = header ? header.offsetHeight : 0;
      const targetTop =
        target.getBoundingClientRect().top + window.scrollY - headerHeight;

      window.scrollTo({
        top: targetTop,
        behavior: "smooth",
      });

      // Update URL hash without jumping
      history.pushState(null, "", targetId);

      // Move focus to the target section for accessibility
      target.setAttribute("tabindex", "-1");
      target.focus({ preventScroll: true });
    });
  }

  /* =========================================================
     FEATURE TAB SWITCHER
     Used on the features page; looks for [data-tab] triggers
     and [data-panel] content blocks

     Markup expected:
       <button class="tab" data-tab="tab-id" aria-selected="true">…</button>
       <div class="tab-panel" data-panel="tab-id">…</div>
  ========================================================= */
  function initFeatureTabs() {
    const tabContainers = document.querySelectorAll("[data-tab-group]");
    if (!tabContainers.length) return;

    tabContainers.forEach(function (container) {
      const tabs = container.querySelectorAll("[data-tab]");
      const panels = container.querySelectorAll("[data-panel]");

      if (!tabs.length || !panels.length) return;

      // Build a map for quick lookup: tabId -> { tab, panel }
      const tabMap = {};
      tabs.forEach(function (tab) {
        const id = tab.dataset.tab;
        tabMap[id] = tabMap[id] || {};
        tabMap[id].tab = tab;
        tab.setAttribute("role", "tab");
        tab.setAttribute("aria-controls", "panel-" + id);
        tab.setAttribute("id", "tab-" + id);
      });

      panels.forEach(function (panel) {
        const id = panel.dataset.panel;
        if (tabMap[id]) {
          tabMap[id].panel = panel;
        }
        panel.setAttribute("role", "tabpanel");
        panel.setAttribute("aria-labelledby", "tab-" + id);
        panel.setAttribute("id", "panel-" + id);
      });

      // Activate a specific tab by id
      function activateTab(id) {
        Object.keys(tabMap).forEach(function (key) {
          const entry = tabMap[key];
          const isActive = key === id;

          if (entry.tab) {
            entry.tab.classList.toggle(TAB_ACTIVE_CLASS, isActive);
            entry.tab.setAttribute("aria-selected", String(isActive));
            entry.tab.setAttribute("tabindex", isActive ? "0" : "-1");
          }

          if (entry.panel) {
            entry.panel.classList.toggle(PANEL_ACTIVE_CLASS, isActive);
            entry.panel.hidden = !isActive;
          }
        });
      }

      // Initialise: activate the first tab (or whichever has aria-selected="true")
      let initialTab = null;
      tabs.forEach(function (tab) {
        if (tab.getAttribute("aria-selected") === "true") {
          initialTab = tab.dataset.tab;
        }
      });
      if (!initialTab && tabs[0]) {
        initialTab = tabs[0].dataset.tab;
      }
      if (initialTab) activateTab(initialTab);

      // Click handler
      tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
          activateTab(tab.dataset.tab);
        });
      });

      // Keyboard navigation (arrow keys within a tab group)
      tabs.forEach(function (tab, index) {
        tab.addEventListener("keydown", function (e) {
          let newIndex = null;

          if (e.key === "ArrowRight" || e.key === "ArrowDown") {
            e.preventDefault();
            newIndex = (index + 1) % tabs.length;
          } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
            e.preventDefault();
            newIndex = (index - 1 + tabs.length) % tabs.length;
          } else if (e.key === "Home") {
            e.preventDefault();
            newIndex = 0;
          } else if (e.key === "End") {
            e.preventDefault();
            newIndex = tabs.length - 1;
          }

          if (newIndex !== null) {
            activateTab(tabs[newIndex].dataset.tab);
            tabs[newIndex].focus();
          }
        });
      });
    });
  }

  /* =========================================================
     CONTACT FORM VALIDATION
     Validates required fields, email format, and optional
     fields marked with data-min-length

     Markup expected:
       <form class="contact-form" novalidate>
         <input type="text"  name="name"    required>
         <input type="email" name="email"   required>
         <textarea           name="message" required data-min-length="20"></textarea>
         <button type="submit">Send</button>
       </form>
  ========================================================= */
  function initContactForm() {
    const forms = document.querySelectorAll(".contact-form");
    if (!forms.length) return;

    forms.forEach(function (form) {
      // Create or fetch the status announcement region
      let statusRegion = form.querySelector(".form-status");
      if (!statusRegion) {
        statusRegion = document.createElement("div");
        statusRegion.className = "form-status";
        statusRegion.setAttribute("aria-live", "polite");
        statusRegion.setAttribute("role", "status");
        form.prepend(statusRegion);
      }

      form.addEventListener("submit", function (e) {
        e.preventDefault();
        clearAllErrors(form);
        statusRegion.textContent = "";

        const fields = form.querySelectorAll("input, textarea, select");
        let firstInvalidField = null;
        let isFormValid = true;

        fields.forEach(function (field) {
          const error = validateField(field);
          if (error) {
            showFieldError(field, error);
            isFormValid = false;
            if (!firstInvalidField) firstInvalidField = field;
          }
        });

        if (!isFormValid) {
          statusRegion.textContent =
            "Please fix the errors below and try again.";
          statusRegion.className = "form-status form-status--error";
          if (firstInvalidField) firstInvalidField.focus();
          return;
        }

        // ── SUCCESS PATH ──────────────────────────────────────
        // Replace this block with your real fetch/AJAX submit
        handleFormSuccess(form, statusRegion);
      });

      // Validate individual fields on blur for inline feedback
      form.querySelectorAll("input, textarea, select").forEach(function (field) {
        field.addEventListener("blur", function () {
          clearFieldError(field);
          const error = validateField(field);
          if (error) showFieldError(field, error);
        });

        // Clear error on input once user starts correcting
        field.addEventListener("input", function () {
          if (field.getAttribute("aria-invalid") === "true") {
            clearFieldError(field);
          }
        });
      });
    });
  }

  /**
   * Validate a single field; returns an error string or null
   */
  function validateField(field) {
    const value = field.value.trim();
    const name = field.name || field.id || "This field";
    const label = getFieldLabel(field) || name;

    // Skip disabled or hidden fields
    if (field.disabled || field.type === "hidden") return null;

    // Required check
    if (field.required && value === "") {
      return label + " is required.";
    }

    // Email format check
    if (field.type === "email" && value !== "") {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) {
        return "Please enter a valid email address.";
      }
    }

    // Minimum length check (data-min-length attribute)
    const minLength = parseInt(field.dataset.minLength, 10);
    if (!isNaN(minLength) && value.length > 0 && value.length < minLength) {
      return (
        label +
        " must be at least " +
        minLength +
        " characters (currently " +
        value.length +
        ")."
      );
    }

    // Pattern check (uses native pattern attribute if present)
    if (field.pattern && value !== "") {
      const pattern = new RegExp("^(?:" + field.pattern + ")$");
      if (!pattern.test(value)) {
        return field.title
          ? field.title
          : label + " format is invalid.";
      }
    }

    return null; // field is valid
  }

  /**
   * Attempt to find the associated <label> text for a field
   */
  function getFieldLabel(field) {
    // Check for aria-label
    if (field.getAttribute("aria-label")) {
      return field.getAttribute("aria-label");
    }
    // Check for associated <label>
    if (field.id) {
      const label = document.querySelector('label[for="' + field.id + '"]');
      if (label) return label.textContent.trim().replace(/:$/, "");
    }
    // Check wrapping label
    const parentLabel = field.closest("label");
    if (parentLabel) {
      // Get text without the input's own text
      return parentLabel.childNodes[0].textContent.trim().replace(/:$/, "");
    }
    return null;
  }

  /**
   * Inject an error message next to a field and mark it invalid
   */
  function showFieldError(field, message) {
    field.setAttribute("aria-invalid", "true");
    field.classList.add("field--error");

    const errorId = "error-" + (field.id || field.name || Math.random().toString(36).slice(2));
    field.setAttribute("aria-describedby", errorId);

    const errorEl = document.createElement("span");
    errorEl.className = "field-error";
    errorEl.id = errorId;
    errorEl.setAttribute("role", "alert");
    errorEl.textContent = message;

    // Insert directly after the field (or after its wrapper)
    const wrapper = field.closest(".field-wrapper") || field;
    wrapper.insertAdjacentElement("afterend", errorEl);
  }

  /**
   * Remove the error state from a single field
   */
  function clearFieldError(field) {
    field.removeAttribute("aria-invalid");
    field.removeAttribute("aria-describedby");
    field.classList.remove("field--error");

    const wrapper = field.closest(".field-wrapper") || field;
    const errorEl = wrapper.nextElementSibling;
    if (errorEl && errorEl.classList.contains("field-error")) {
      errorEl.remove();
    }
  }

  /**
   * Remove all error states within a form
   */
  function clearAllErrors(form) {
    form.querySelectorAll(".field-error").forEach((el) => el.remove());
    form.querySelectorAll("[aria-invalid]").forEach(function (field) {
      field.removeAttribute("aria-invalid");
      field.removeAttribute("aria-describedby");
      field.classList.remove("field--error");
    });
  }

  /**
   * Handle successful form submission
   * Replace or augment with a real fetch call as needed
   */
  function handleFormSuccess(form, statusRegion) {
    // Example: swap form contents for a success message
    statusRegion.textContent =
      "Thank you! Your message has been sent. We'll be in touch shortly.";
    statusRegion.className = "form-status form-status--success";

    // Optionally reset the form
    form.reset();

    // Scroll the status into view
    statusRegion.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  /* =========================================================
     ACTIVE NAV LINK HIGHLIGHTING (scroll-spy)
     Marks the nav link whose section is currently in view
  ========================================================= */
  function initScrollSpy() {
    const sections = document.querySelectorAll("section[id]");
    const navLinks = document.querySelectorAll('.site-nav a[href^="#"]');

    if (!sections.length || !navLinks.length) return;

    const ACTIVE_LINK_CLASS = "nav-link--active";

    function onScroll() {
      const scrollMid = window.scrollY + window.innerHeight / 2;

      let currentId = null;
      sections.forEach(function (section) {
        const top = section.offsetTop;
        const bottom = top + section.offsetHeight;
        if (scrollMid >= top && scrollMid < bottom) {
          currentId = section.id;
        }
      });

      navLinks.forEach(function (link) {
        const href = link.getAttribute("href").slice(1); // strip #
        link.classList.toggle(ACTIVE_LINK_CLASS, href === currentId);
        link.setAttribute(
          "aria-current",
          href === currentId ? "true" : "false"
        );
      });
    }

    window.addEventListener("scroll", throttle(onScroll, 150), {
      passive: true,
    });

    // Run once on load
    onScroll();
  }

  /* =========================================================
     INIT — run everything when DOM is ready
  ========================================================= */
  function init() {
    initMobileNav();
    initStickyHeader();
    initSmoothScroll();
    initFeatureTabs();
    initContactForm();
    initScrollSpy();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    // DOM already parsed (script loaded with defer/async)
    init();
  }
})();