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
