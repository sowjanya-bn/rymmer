// RYM Collector — artist page content script
// Collects discography metadata from /artist/* pages

const SERVER = "http://localhost:7842";

function extractArtistData() {
  const url = window.location.href;
  const name = document.querySelector("h1.artist_name_hdr")?.textContent.trim()
    || document.title.split(" discography")[0].trim();

  const albums = [];
  for (const row of document.querySelectorAll("div.disco_release")) {
    const titleEl = row.querySelector("a.album");
    const yearEl = row.querySelector("span.year");
    const ratingEl = row.querySelector("span.avg_rating");
    if (!titleEl) continue;
    albums.push({
      title: titleEl.textContent.trim(),
      url: titleEl.href,
      year: yearEl ? yearEl.textContent.trim() : null,
      rating: ratingEl ? parseFloat(ratingEl.textContent.trim()) : null,
    });
  }

  return { type: "artist", url, name, albums, collected_at: new Date().toISOString() };
}

async function run() {
  const data = extractArtistData();
  if (!data.albums.length) return;

  try {
    await fetch(`${SERVER}/collect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  } catch (e) {
    console.warn("[RYM Collector] Could not reach local server:", e.message);
  }
}

run();
