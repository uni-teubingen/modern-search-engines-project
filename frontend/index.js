/**
 * Holt den Suchbegriff und leitet zur results.html weiter
 * @param {Event} event - Das Submit-Event vom Formular
 */
function handleSearch(event) {
  event.preventDefault();

  const input = document.getElementById("searchInput");
  const query = input?.value.trim();

  if (query) {
    const targetUrl = `result.html?q=${encodeURIComponent(query)}`;
    window.location.href = targetUrl;
  }
}

// Beim Laden Eventlistener registrieren
window.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("searchForm");
  if (form) {
    form.addEventListener("submit", handleSearch);
  }
});

/**
 * Unabstellbarer Switch des AI-Assistenten
 */
document.addEventListener('DOMContentLoaded', () => {
  const palmer_switch = document.getElementById('disablePalmer');
  const denied_sound = new Audio("/assets/audio/1.mp3");
  denied_sound.preload = 'auto';
  palmer_switch.addEventListener('change', () => {
  if(!palmer_switch.checked) {
    
      denied_sound.play().catch(() => {});
    
    setTimeout(() => {
      palmer_switch.checked = true;
    }, 150);
  }
  });
});
