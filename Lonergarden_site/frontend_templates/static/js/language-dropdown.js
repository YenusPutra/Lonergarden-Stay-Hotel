(function() {

  const setLanguageUrl = "/i18n/setlang/";        // url to your backend view
  function getCookie(name) {     // get CSRF token from cookie
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }
  document.addEventListener("DOMContentLoaded", function () {     // handle click events once DOM is ready
    document.querySelectorAll('#language-dropdown a[data-lang]').forEach(link => {
      link.addEventListener('click', e => {
        e.preventDefault();
        const lang = link.dataset.lang;
         let currentPath = window.location.pathname;    // Get current path without language prefix
        // Handle root path specially
        let basePath;
        if (currentPath === '/') {
          basePath = '/';  // Keep as root
        } else {
          // Remove any existing language prefix for non-root paths
          basePath = currentPath.replace(/^\/(en|ja|id|fr|de|es)(\/|$)/, '/');
          // If basePath becomes empty after replacement, set to '/'
          if (basePath === '') basePath = '/';
        }
        // Construct the new path
        const newPath = `/${lang}${basePath}`;

        console.log('Current path:', currentPath);
        console.log('Base path:', basePath);
        console.log('New path:', newPath);

        fetch(setLanguageUrl, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken'),
          },
          body: new URLSearchParams({ 
            language: lang,
            next: newPath  // Use the new path WITH language prefix
           }),    
        })
        .then(r => {
          if (r.ok) {
            window.location.href = newPath;  // Navigate to the language-prefixed URL  
          } else {
            alert('Error changing language');
          }
        })
        .catch(err => console.error(err));
      });
    });
  });
})();
