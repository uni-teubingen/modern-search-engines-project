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

  window.dispatchEvent(
    new CustomEvent("searchResultsLoaded", { detail: data })
  );

  
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

// Palmer-AI-Assistant:

/**
 * Fügt Animation zu Assisten hinzu
 */
function animateAssistant() {
  const img = document.getElementById("assistantImg");
  if (img) {
    img.classList.add("animate");
  }
}

/**
 * Spielt zufällig einen Spruch ab (Vorab muss Autoplay im Browser aktiviert werden)
 */

function playRandomSound(){
  const random = Math.floor(Math.random() * 5) + 1;
  const audio = new Audio(`/assets/audio/${random}.mp3`);
  audio.play().catch(err => console.warn("Autoplay disabled:", err));
}
/**
 * Erstellt eine Sprechblase
 */
function createSpeechBubble(){
  const wrapper = document.getElementById('assistantWrapper');
  const bubble = document.createElement('div');
  bubble.id = 'speechBubble';
  bubble.className = 'speech-bubble';
  wrapper.appendChild(bubble); 
}

/**
 * Bestimmt die passende Stimmung von Palmer
 */
function determineStateOfHappiness(emotion){
  const wrapper = document.getElementById('assistantWrapper');
  const lower_jaw = document.createElement('img');
  lower_jaw.id = 'assistantImgLower';
  lower_jaw.className = 'assistant-img-lower';
  lower_jaw.alt ='Palmer-AI-Assistant';
  lower_jaw.width='200px';
  lower_jaw.src = `assets/img/assistant_lower.png`;
  const upper_jaw = document.createElement('img');
  upper_jaw.id = 'assistantImgUpper';
  upper_jaw.className = 'assistant-img animate';
  upper_jaw.alt ='Palmer-AI-Assistant';
  upper_jaw.width='200px';
  upper_jaw.src = `assets/img/assistant_upper_${emotion}.png`;
  wrapper.appendChild(lower_jaw);
  wrapper.appendChild(upper_jaw);
}

/**
 * Kommentiert die Suche & Initialisiert die Stimmung
 */
function commentSearchQuery(){
  const query = getQueryParam("q");
  const query_lower = query.toLowerCase();
  if (query_lower.includes('car')) {
    determineStateOfHappiness('angry');
    var new_query = query_lower.replace('car', 'bicycle');
    var print_query = query_lower.replace('car', '<b>bicycle</b>');
    while(new_query.includes('car')){
      new_query = new_query.replace('car', 'bicycle');
      var print_query = print_query.replace('car', '<b>bicycle</b>');
    }
    createSpeechBubble();
    const bubble = document.getElementById('speechBubble');
    bubble.innerHTML = `Did you mean: <a href=http://localhost:8080/result.html?q=${new_query}><i>${print_query}</i></a>?`
  }
  else if (!window.hasPalmerScore) { // TODO: Hier muss gecheckt werden / die Condition replaced werden
    determineStateOfHappiness('sad');
    createSpeechBubble();
    const bubble = document.getElementById('speechBubble');
    bubble.innerHTML = `Did you mean: <a href=http://localhost:8080/result.html?q=${query}%20Boris%20Palmer><i>${query} <b>Boris Palmer</b></i> </a>?`
  } else {
    determineStateOfHappiness('happy');
    createSpeechBubble();
    const bubble = document.getElementById('speechBubble');
    bubble.innerHTML = "I like these results. Keep up the good searching!"
  }
}


/**
 * Initialisiere den Palmer-AI-Assistant
 */
function initAssistant(){
  window.addEventListener(
    "searchResultsLoaded",
    (e) => {
      const data = e.detail;

      // OR über alle palmer_score-Felder
      window.hasPalmerScore = data.some(item => item.palmer_score === true);

      commentSearchQuery();
      animateAssistant();
      playRandomSound();      // jetzt stehen alle Infos bereit
    },
    { once: true }                 // nur einmal reagieren
  );
}


// Seite initialisieren
window.addEventListener("DOMContentLoaded", () => {
  initSearchPage();
  initSearchFormHandler();
  initAssistant();
});
