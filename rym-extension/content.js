// RYM Collector — album page content script
// Runs once per page load on rateyourmusic.com/release/album/*/*

const SERVER = "http://localhost:7842";

function getText(selector) {
  const el = document.querySelector(selector);
  return el ? el.textContent.trim() : null;
}

function extractAlbumData() {
  const url = window.location.href;

  // Title: h1 with class containing release_page_title, fallback to <title>
  let title = getText("h1.release_page_title");
  if (!title) {
    const m = document.title.match(/^(.+?)\s+by\s+/);
    title = m ? m[1].trim() : document.title;
  }

  // Artist — first /artist/ link on the page is the primary artist
  const artistLink = document.querySelector("a[href*='/artist/']");
  let artist = artistLink ? artistLink.textContent.trim() : null;
  if (!artist) {
    const m = document.title.match(/\bby\s+(.+?)(\s+[-|]|$)/);
    artist = m ? m[1].trim() : null;
  }

  // Year
  let year = getText(".issue_year");
  if (!year) {
    // Try release info table
    const rows = document.querySelectorAll("table.release_info tr");
    for (const row of rows) {
      if (row.textContent.includes("Released")) {
        const m = row.textContent.match(/\b(19|20)\d{2}\b/);
        if (m) { year = m[0]; break; }
      }
    }
  }

  // Rating
  const ratingEl = document.querySelector(".avg_rating");
  const rating = ratingEl ? parseFloat(ratingEl.textContent.trim()) : null;

  // Ratings count
  const ratingsCountEl = document.querySelector(".num_ratings b span");
  const ratings_count = ratingsCountEl
    ? parseInt(ratingsCountEl.textContent.replace(/,/g, "").trim(), 10)
    : null;

  // Rank — look for a table cell that follows one containing "Ranked"
  let rank_year = null;
  let rank_year_label = null;
  const cells = document.querySelectorAll("td");
  for (let i = 0; i < cells.length; i++) {
    if (cells[i].textContent.trim() === "Ranked") {
      const next = cells[i + 1];
      if (next) {
        const b = next.querySelector("b");
        const raw = b ? b.textContent.trim() : next.textContent.trim();
        // Format: "#1045 for 2016"
        const m = raw.match(/#?(\d+)\s+for\s+(\d{4})/);
        if (m) { rank_year = m[1]; rank_year_label = m[2]; }
      }
      break;
    }
  }

  // Genres (primary + secondary)
  const genres = [
    ...document.querySelectorAll(".release_pri_genres a"),
    ...document.querySelectorAll(".release_sec_genres a"),
  ].map(a => a.textContent.trim()).filter(Boolean);

  // Descriptors
  const descEl = document.querySelector(".release_pri_descriptors");
  const descriptors = descEl
    ? descEl.textContent.split(",").map(s => s.trim()).filter(Boolean)
    : [];

  // Reviews — extract text from the unnamed child element (skips tracklist + rating + status)
  const reviews = [];
  const reviewEls = document.querySelectorAll(".review");
  for (const rev of reviewEls) {
    const authorEl = rev.querySelector('.review_header [title^="User"]');
    const bodyEl = rev.querySelector(".review_body");
    if (!bodyEl) continue;
    // The review text is in a child with no class (anonymous span/div), skip track_rating, review_title, review_publish_status
    const textEl = Array.from(bodyEl.children).find(
      el => !el.className && el.textContent.trim().length > 20
    );
    if (!textEl) continue;
    reviews.push({
      author: authorEl ? authorEl.textContent.trim() : "",
      text: textEl.textContent.trim(),
    });
  }

  return {
    url,
    title,
    artist,
    year,
    genres,
    descriptors,
    rating,
    ratings_count,
    rank_year,
    rank_year_label,
    reviews,
    collected_at: new Date().toISOString(),
  };
}

function showBadge(msg) {
  const badge = document.createElement("div");
  badge.textContent = msg;
  badge.style.cssText = [
    "position:fixed",
    "bottom:16px",
    "right:16px",
    "background:#1a1a2e",
    "color:#e0e0e0",
    "padding:8px 14px",
    "border-radius:6px",
    "font:13px/1.4 sans-serif",
    "z-index:999999",
    "box-shadow:0 2px 8px rgba(0,0,0,.4)",
    "opacity:0.95",
  ].join(";");
  document.body.appendChild(badge);
  setTimeout(() => badge.remove(), 3000);
}

async function run() {
  const data = extractAlbumData();

  try {
    const res = await fetch(`${SERVER}/collect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const json = await res.json();
    if (json.status === "duplicate") {
      showBadge("RYM: already collected");
    } else {
      showBadge("RYM: saved ✓");
    }
  } catch (e) {
    console.warn("[RYM Collector] Could not reach local server:", e.message);
  }
}

run();
