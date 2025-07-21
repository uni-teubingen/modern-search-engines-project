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
    alert("🚫 Das Backend ist momentan am crawlen.");
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("searchForm");
  if (form) {
    form.addEventListener("submit", handleSearch);
  }
});

document.addEventListener('DOMContentLoaded', () => {
  const palmer_switch = document.getElementById('disablePalmer');
  const denied_sound = new Audio("/assets/audio/denied.mp3");
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