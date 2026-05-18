/* ============================================================
   Nexo YR Secure — utils.js
   Funciones utilitarias reutilizables.
   ============================================================ */
(function (w) {
  'use strict';

  /** Formatea un número como precio COP: 1234567 -> "$1.234.567" */
  function formatCOP(value) {
    var n = Math.round(Number(value) || 0);
    return '$' + n.toLocaleString('es-CO').replace(/,/g, '.');
  }

  /** Valida un email de forma básica. */
  function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(email || '').trim());
  }

  /** Scroll suave a un elemento (selector o nodo). */
  function scrollToEl(target, offset) {
    var el = typeof target === 'string' ? document.querySelector(target) : target;
    if (!el) return;
    var y = el.getBoundingClientRect().top + w.pageYOffset - (offset || 80);
    w.scrollTo({ top: y, behavior: 'smooth' });
  }

  /** Debounce simple. */
  function debounce(fn, wait) {
    var t;
    return function () {
      var ctx = this, args = arguments;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, wait || 200);
    };
  }

  w.DeisiUtils = {
    formatCOP: formatCOP,
    validateEmail: validateEmail,
    scrollToEl: scrollToEl,
    debounce: debounce
  };
})(window);
