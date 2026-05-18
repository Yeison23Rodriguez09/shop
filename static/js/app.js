/* ============================================================
   Nexo YR Secure — app.js
   Animación scroll fade-in, navbar móvil, qty steppers,
   validación de formularios, auto-cierre de alertas.
   ============================================================ */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {

    /* ---- 1. Fade-in on scroll (IntersectionObserver) ----
       Auto-etiqueta bloques comunes para que TODA página tenga
       animación sin tocar cada template. */
    var autoSelectors = [
      'section', '.ares-card', '.cat-card', '.stat-box', '.feature-box',
      '.order-card', '.panel', '.cart-summary', '.form-section',
      '.auth-box', '.summary-box', '.mini-cart'
    ];
    autoSelectors.forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (el) {
        if (!el.classList.contains('fade-in') && !el.closest('.ares-navbar')) {
          el.classList.add('fade-in');
        }
      });
    });

    var faded = document.querySelectorAll('.fade-in');
    if ('IntersectionObserver' in window && faded.length) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add('visible');
            io.unobserve(e.target);
          }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
      faded.forEach(function (el) { io.observe(el); });
    } else {
      faded.forEach(function (el) { el.classList.add('visible'); });
    }

    /* ---- 2. Navbar: sombra al hacer scroll ---- */
    var nav = document.querySelector('.ares-navbar');
    if (nav) {
      var onScroll = function () {
        nav.style.boxShadow = window.scrollY > 12
          ? '0 10px 30px rgba(0,0,0,.45)' : 'none';
      };
      onScroll();
      window.addEventListener('scroll', onScroll, { passive: true });
    }

    /* ---- 3. Navbar móvil: cerrar al hacer click en un link ---- */
    var collapse = document.getElementById('navMenu');
    if (collapse) {
      collapse.querySelectorAll('a.nav-link, .btn-ares, .btn-ares-outline').forEach(function (a) {
        a.addEventListener('click', function () {
          if (window.innerWidth < 992 && collapse.classList.contains('show')) {
            if (window.bootstrap && bootstrap.Collapse) {
              bootstrap.Collapse.getOrCreateInstance(collapse).hide();
            } else {
              collapse.classList.remove('show');
            }
          }
        });
      });
    }

    /* ---- 4. Steppers de cantidad [data-qty-stepper] ---- */
    document.querySelectorAll('[data-qty-minus],[data-qty-plus]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var wrap = btn.closest('[data-qty-stepper]') || btn.parentElement;
        var input = wrap.querySelector('input[type="number"]');
        if (!input) return;
        var v = parseInt(input.value, 10) || 1;
        var min = parseInt(input.min, 10) || 1;
        var max = parseInt(input.max, 10) || 999;
        v += btn.hasAttribute('data-qty-plus') ? 1 : -1;
        input.value = Math.max(min, Math.min(max, v));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      });
    });

    /* ---- 5. Validación ligera de formularios [data-validate] ---- */
    document.querySelectorAll('form[data-validate]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        var ok = true;
        form.querySelectorAll('[required]').forEach(function (f) {
          var bad = !f.value.trim() ||
            (f.type === 'email' && window.DeisiUtils &&
             !DeisiUtils.validateEmail(f.value));
          f.style.borderColor = bad ? 'var(--danger)' : '';
          if (bad) ok = false;
        });
        if (!ok) { e.preventDefault(); }
      });
    });

    /* ---- 6. Auto-cierre de alertas flash ---- */
    document.querySelectorAll('.alert-ok, .alert-err, .alert-success, .alert-danger')
      .forEach(function (al) {
        setTimeout(function () {
          al.style.transition = 'opacity .5s, transform .5s';
          al.style.opacity = '0';
          al.style.transform = 'translateY(-8px)';
          setTimeout(function () { al.remove(); }, 500);
        }, 6000);
      });

  });
})();
