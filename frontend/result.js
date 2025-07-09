/**
 * Holt einen Query-Parameter aus der URL (?name=...)
 * @param {string} name - Der Parametername
 * @returns {string} - Der Wert oder leerer String
 */
function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name) || "";
}

/**
 * Erstellt einen HTML-Block für ein Ergebnis
 * @param {Object} result - Ein Eintrag vom Backend
 * @returns {HTMLElement}
 */
function createResultElement(result) {
  const resultBlock = document.createElement("div");
  resultBlock.className = "result";

  resultBlock.innerHTML = `
    <div class="url">${result.url}</div>
    <a href="${result.url}" target="_blank" class="title">${result.title}</a>
    <div class="snippet">${result.snippet}</div>
  `;

  return resultBlock;
}

/**
 * Zeigt alle Suchergebnisse im DOM an
 * @param {Array} data - Array von Suchergebnissen
 */
function renderResults(data) {
  const container = document.getElementById("results");
  container.innerHTML = "";

  data.forEach(result => {
    const el = createResultElement(result);
    container.appendChild(el);
  });
}

/**
 * Führt die Suche aus und zeigt Ergebnisse
 */
function initSearchPage() {
  const query = getQueryParam("q");

  // Setzt den Suchbegriff in die Eingabe
  const input = document.getElementById("searchBox");
  if (input) input.value = query;

  // Ruft API auf
  if (query.trim()) {
    fetch(`http://localhost:5050/api/search?q=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(renderResults)
      .catch(err => {
        console.error("Fehler beim Laden der Ergebnisse:", err);
        document.getElementById("results").innerText = "Fehler beim Laden der Ergebnisse.";
      });
  }
}

/**
 * Reagiert auf neue Suche im Suchformular
 */
function initSearchFormHandler() {
  const form = document.getElementById("searchForm");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = document.getElementById("searchBox");
      const newQuery = input.value.trim();

      if (newQuery) {
        // Starte neue Suche mit page=1
        window.location.href = `result.html?q=${encodeURIComponent(newQuery)}&page=1`;
      }
    });
  }
}

// Seite initialisieren
window.addEventListener("DOMContentLoaded", () => {
  initSearchPage();
  initSearchFormHandler();
});
