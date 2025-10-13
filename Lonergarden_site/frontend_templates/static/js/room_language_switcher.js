/**
 * Admin language switcher for Room model
 * Real-time two-way synchronization between:
 *  - Visible description textarea (name="description")
 *  - Hidden per-language fields (name="description_{lang}")
 *  - Language selector (name="edit_language")
 *
 * Behavior:
 *  - Typing in the visible textarea updates the corresponding hidden field instantly.
 *  - Typing in a hidden field for the selected language updates the visible textarea instantly.
 *  - Switching the language saves the current visible text to its hidden field and loads the new language.
 *  - On submit, all cached values are flushed to their language fields for persistence.
 *  - Language switching does NOT trigger unsaved changes warnings.
 *
 * Requirements in the admin form:
 *  - <select name="edit_language"> with options: en, id, ja, fr, de, es
 *  - <textarea name="description"> as the visible input area
 *  - Hidden textareas present in DOM:
 *      description_en, description_id, description_ja,
 *      description_fr, description_de, description_es
 */

(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var select = document.querySelector('select[name="edit_language"]');
    var textarea = document.querySelector('textarea[name="description"]');

    if (!select || !textarea) return;

    var langLabels = {
      en: 'English',
      id: 'Indonesian',
      ja: 'Japanese',
      fr: 'French',
      de: 'German',
      es: 'Spanish'
    };

    // Gather hidden per-language fields
    var languageFields = {};
    Object.keys(langLabels).forEach(function (code) {
      var el = document.querySelector('[name="description_' + code + '"]');
      if (el) languageFields[code] = el;
    });

    // Cache typed text per language during this session
    var cache = {};

    // Track whether we are updating programmatically to avoid redundant work
    var isProgrammatic = false;

    // Track if we're currently switching languages to prevent unsaved changes trigger
    var isLanguageSwitching = false;

    // Determine current language from the dropdown
    var currentLang = select.value || 'en';

    // Seed cache from existing values in the language fields (DB values)
    Object.keys(languageFields).forEach(function (code) {
      var val = languageFields[code].value;
      if (val !== undefined && val !== null && val !== '') {
        cache[code] = val;
      }
    });

    // If the textarea is pre-filled (e.g., initial load), seed the cache for current language
    if (textarea.value && !cache[currentLang]) {
      cache[currentLang] = textarea.value;
    }

    function setPlaceholder(code) {
      var label = langLabels[code] || code.toUpperCase();
      textarea.placeholder = 'Description (' + label + ')';
    }

    // Push visible textarea content into cache and the matching hidden field
    function syncVisibleToHidden() {
      if (!currentLang) return;
      var val = textarea.value;
      cache[currentLang] = val;
      if (languageFields[currentLang]) {
        languageFields[currentLang].value = val;
        // Dispatch input event but mark it as programmatic to avoid unsaved changes
        try {
          var event = new Event('input', { bubbles: true });
          event.isProgrammatic = true;
          languageFields[currentLang].dispatchEvent(event);
        } catch (e) {}
      }
    }

    // Load content from cache/hidden into the visible textarea for a given language
    function loadLanguageIntoVisible(code) {
      var fromCache = cache.hasOwnProperty(code) ? cache[code] : null;
      var fromField =
        languageFields[code] && languageFields[code].value
          ? languageFields[code].value
          : '';

      var nextVal = fromCache !== null ? fromCache : fromField;

      isProgrammatic = true;
      isLanguageSwitching = true; // Mark as language switching
      textarea.value = nextVal || '';
      isProgrammatic = false;
      isLanguageSwitching = false; // Done switching
    }

    function switchLanguage(newLang) {
      if (newLang === currentLang) return;

      // Save current textarea value to its hidden field and cache
      syncVisibleToHidden();

      // Switch and load new language's value
      currentLang = newLang;
      loadLanguageIntoVisible(currentLang);
      setPlaceholder(currentLang);
    }

    // Real-time: typing in visible textarea updates cache + corresponding hidden field
    textarea.addEventListener('input', function () {
      if (isProgrammatic || isLanguageSwitching) return;
      syncVisibleToHidden();
    });

    // Real-time: typing in a hidden field should update cache and,
    // if it corresponds to the currently selected language, also update visible textarea
    Object.keys(languageFields).forEach(function (code) {
      var field = languageFields[code];
      if (!field) return;

      field.addEventListener('input', function (e) {
        // Skip if this was triggered programmatically
        if (e.isProgrammatic) return;
        
        // Update cache for this language
        cache[code] = field.value;

        // If this hidden field is for the currently selected language,
        // reflect the text into the visible textarea immediately
        if (code === currentLang) {
          isProgrammatic = true;
          textarea.value = field.value || '';
          isProgrammatic = false;
          try {
            var event = new Event('input', { bubbles: true });
            event.isProgrammatic = true;
            textarea.dispatchEvent(event);
          } catch (e) {}
        }
      });
    });

    // Handle dropdown changes
    select.addEventListener('change', function (e) {
      switchLanguage(e.target.value);
    });

    // Before submit, ensure the latest visible text is saved and all cached values are flushed
    var form = textarea.closest('form');
    if (form) {
      form.addEventListener('submit', function () {
        // Save currently visible textarea to its hidden field
        syncVisibleToHidden();

        // Flush cache for all languages to their fields
        Object.keys(cache).forEach(function (code) {
          if (languageFields[code]) {
            languageFields[code].value = cache[code] || '';
          }
        });
      });
    }

    // Initial sync: ensure visible textarea shows the selected language's content
    loadLanguageIntoVisible(currentLang);
    setPlaceholder(currentLang);
  });
})();