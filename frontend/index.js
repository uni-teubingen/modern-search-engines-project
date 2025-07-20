/**
 * Holt den Suchbegriff und leitet zur results.html weiter
 * @param {Event} event - Das Submit-Event vom Formular
 */
async function handleSearch(event) {
  event.preventDefault();

  const input = document.getElementById("searchInput");
  const query = input?.value.trim();

  if (!query) return;

  try {
    const response = await fetch("http://localhost:5050/api/health-check");
    if (!response.ok) {
      throw new Error("Backend nicht erreichbar");
    }

    const targetUrl = `result.html?q=${encodeURIComponent(query)}`;
    window.location.href = targetUrl;

  } catch (error) {
    alert("🚫 Das Backend ist momentan nicht erreichbar.\nBitte versuche es später erneut.");
  }
}

// Beim Laden Eventlistener registrieren
window.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("searchForm");
  if (form) {
    form.addEventListener("submit", handleSearch);
  }
});
