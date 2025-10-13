/**
 * Unsaved Changes Guard for Django Admin Change Form
 * 
 * - Sets a dirty flag on any user change (input/change/keydown).
 * - Shows a confirm dialog on in-admin navigation.
 * - Shows a browser beforeunload warning on refresh/close.
 * - Disables the warning on form submit.
 * - IGNORES language selector dropdown changes and programmatic events.
 *
 * Also exposes a debugging API at window.__adminUnsavedChangesGuard.
 */

(function () {
  document.addEventListener('DOMContentLoaded', function () {
    // Try to grab the change form reliably
    var form =
      document.querySelector('#room_form') ||                 // common admin id
      document.querySelector('.change-form form') ||          // admin structure
      document.querySelector('form');                         // fallback

    if (!form) return;

    var hasUnsavedChanges = false;

    function markDirty() {
      hasUnsavedChanges = true;
    }

    // Check if an event should be ignored for unsaved changes
    function shouldIgnoreEvent(e) {
      // Ignore programmatic events (from language switcher)
      if (e.isProgrammatic) {
        return true;
      }
      
      var el = e.target;
      // Ignore language selector dropdown
      if (el.name === 'edit_language' || 
          (el.tagName === 'SELECT' && el.name && el.name.includes('language'))) {
        return true;
      }
      return false;
    }

    // Mark dirty on typical edit interactions, but ignore language dropdown and programmatic events
    form.addEventListener('input', function(e) {
      if (!shouldIgnoreEvent(e)) {
        markDirty();
      }
    }, { capture: true });

    form.addEventListener('change', function(e) {
      if (!shouldIgnoreEvent(e)) {
        markDirty();
      }
    }, { capture: true });

    // Also mark dirty on keydown in inputs/textarea/selects to be extra robust
    form.querySelectorAll('input, textarea, select').forEach(function (el) {
      el.addEventListener('keydown', function(e) {
        if (!shouldIgnoreEvent(e)) {
          markDirty();
        }
      }, { capture: true });
    });

    // Allow normal submit without warnings
    form.addEventListener('submit', function () {
      hasUnsavedChanges = false;
    });

    // Warn on page unload (refresh/close)
    window.addEventListener('beforeunload', function (e) {
      if (!hasUnsavedChanges) return;
      e.preventDefault();
      e.returnValue = ''; // required by Chrome
      return '';          // Safari compatibility
    });

    // Intercept in-admin link navigation (breadcrumbs, sidebar, etc.)
    document.addEventListener('click', function (e) {
      var anchor = e.target && e.target.closest ? e.target.closest('a') : null;
      if (!anchor) return;

      if (!hasUnsavedChanges) return;

      // Ignore links that open a new tab/download/hash
      var href = anchor.getAttribute('href') || '';
      if (anchor.target === '_blank') return;
      if (anchor.hasAttribute('download')) return;
      if (href === '' || href.charAt(0) === '#') return;

      // Allow clicks in the submit row (save/continue buttons etc.)
      if (anchor.closest('.submit-row')) return;

      var leave = window.confirm('You have unsaved changes. Leave this page? Your changes will be lost.');
      if (!leave) {
        e.preventDefault();
        e.stopImmediatePropagation();
      } else {
        // Allow this navigation without further warnings
        hasUnsavedChanges = false;
      }
    }, { capture: true });

    // Expose a small debugging API
    window.__adminUnsavedChangesGuard = {
      get dirty() { return hasUnsavedChanges; },
      markDirty: markDirty,
      reset: function() { hasUnsavedChanges = false; }
    };
  });
})();