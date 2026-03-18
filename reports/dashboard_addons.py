"""
Dashboard addon components for TC Ads QA Dashboard v2.
Compare (head-to-head) and Export (print) features.
"""


def get_compare_html() -> str:
    """Return self-contained HTML + CSS + JS for the ad comparison feature."""
    return """
<!-- ═══════════════════════════════════════
     Compare Feature — Head-to-Head Ad Comparison
     ═══════════════════════════════════════ -->
<style>
/* ── Compare Bar (floating bottom bar) ── */
.compare-bar {
  position: fixed; bottom: -80px; left: 0; right: 0;
  background: #1C1E21; color: #fff; z-index: 300;
  transition: bottom 0.3s ease;
  box-shadow: 0 -4px 24px rgba(0,0,0,0.25);
}
.compare-bar.visible { bottom: 0; }
.compare-bar-inner {
  max-width: 1400px; margin: 0 auto;
  display: flex; align-items: center; padding: 12px 24px; gap: 16px;
}
.compare-bar .compare-items {
  display: flex; gap: 12px; flex: 1;
}
.compare-bar .compare-item {
  display: flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,0.1); border-radius: 8px;
  padding: 6px 12px; font-size: 13px; font-weight: 500;
}
.compare-bar .compare-item img {
  width: 36px; height: 36px; border-radius: 4px; object-fit: cover;
}
.compare-bar .compare-item .remove-compare {
  background: none; border: none; color: rgba(255,255,255,0.6);
  cursor: pointer; font-size: 16px; padding: 0 4px; line-height: 1;
}
.compare-bar .compare-item .remove-compare:hover { color: #fff; }
.compare-bar .compare-count {
  font-size: 13px; color: rgba(255,255,255,0.7);
}
.compare-bar .compare-launch {
  padding: 10px 24px; border: none; border-radius: 8px;
  background: #1877F2; color: #fff; font-size: 14px; font-weight: 600;
  cursor: pointer; font-family: 'Inter', sans-serif;
  transition: background 0.15s;
}
.compare-bar .compare-launch:hover { background: #166FE5; }
.compare-bar .compare-launch:disabled {
  background: rgba(255,255,255,0.15); cursor: default; color: rgba(255,255,255,0.4);
}
.compare-bar .compare-clear {
  background: none; border: 1px solid rgba(255,255,255,0.3);
  color: rgba(255,255,255,0.8); border-radius: 8px;
  padding: 10px 16px; font-size: 13px; cursor: pointer;
  font-family: 'Inter', sans-serif; transition: all 0.15s;
}
.compare-bar .compare-clear:hover {
  border-color: rgba(255,255,255,0.6); color: #fff;
}

/* ── Compare Button on cards ── */
.btn-compare {
  padding: 6px 12px; border: 1px solid #DADDE1;
  border-radius: 6px; font-size: 12px; font-weight: 500;
  cursor: pointer; background: #FFFFFF; color: #1C1E21;
  font-family: 'Inter', sans-serif; transition: all 0.15s;
}
.btn-compare:hover { background: #F0F2F5; }
.btn-compare.selected {
  background: #E7F3FF; color: #1877F2; border-color: #1877F2;
}

/* ── Compare Modal ── */
.compare-modal-overlay {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,0.6); z-index: 400;
  backdrop-filter: blur(4px);
}
.compare-modal-overlay.open { display: flex; align-items: flex-start; justify-content: center; overflow-y: auto; }
.compare-modal {
  background: #fff; border-radius: 12px;
  width: 95%; max-width: 1100px; margin: 40px auto;
  box-shadow: 0 16px 64px rgba(0,0,0,0.25);
  animation: compareSlideIn 0.25s ease;
}
@keyframes compareSlideIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.compare-modal-header {
  display: flex; align-items: center; padding: 20px 24px;
  border-bottom: 1px solid #DADDE1;
}
.compare-modal-header h2 {
  font-size: 18px; font-weight: 700; flex: 1;
}
.compare-modal-close {
  width: 36px; height: 36px; border-radius: 50%;
  border: none; background: #F0F2F5; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.15s;
}
.compare-modal-close:hover { background: #DADDE1; }

.compare-columns {
  display: grid; grid-template-columns: 1fr 1fr; min-height: 400px;
}
.compare-col {
  padding: 24px; border-right: 1px solid #E4E6EB;
}
.compare-col:last-child { border-right: none; }
.compare-col .col-advertiser {
  font-size: 16px; font-weight: 700; margin-bottom: 4px;
}
.compare-col .col-score-pill {
  display: inline-block; padding: 4px 12px; border-radius: 12px;
  font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 12px;
}
.compare-col .col-image {
  width: 100%; max-height: 300px; object-fit: contain;
  border-radius: 8px; background: #F8F9FA; margin-bottom: 12px;
}
.compare-col .col-copy {
  font-size: 14px; line-height: 1.6; color: #1C1E21;
  margin-bottom: 16px; max-height: 120px; overflow-y: auto;
}
.compare-col .col-scores { margin-bottom: 12px; }
.compare-score-row {
  display: flex; align-items: center; gap: 8px; margin: 6px 0;
}
.compare-score-row .csr-label {
  width: 90px; font-size: 12px; color: #65676B; text-align: right;
}
.compare-score-row .csr-bar {
  flex: 1; height: 6px; background: #E4E6EB; border-radius: 3px; position: relative;
}
.compare-score-row .csr-bar-fill {
  height: 100%; border-radius: 3px;
}
.compare-score-row .csr-val {
  width: 28px; font-size: 12px; font-weight: 600;
}
.compare-score-row .csr-arrow {
  width: 20px; font-size: 14px; text-align: center;
}
.compare-col .col-issues { margin-top: 8px; }
.compare-col .col-issues-title {
  font-size: 12px; font-weight: 600; color: #65676B;
  text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;
}
.compare-col .col-issue-item {
  display: flex; align-items: start; gap: 6px;
  font-size: 12px; color: #65676B; margin: 4px 0;
}
.compare-col .col-issue-dot {
  width: 6px; height: 6px; border-radius: 50%;
  margin-top: 5px; flex-shrink: 0;
}
.compare-winner-badge {
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 11px; font-weight: 600; margin-left: 8px;
}
.winner { background: #E6F9ED; color: #31A24C; }
.loser { background: #FDECEF; color: #E4405F; }

@media (max-width: 768px) {
  .compare-columns { grid-template-columns: 1fr; }
  .compare-col { border-right: none; border-bottom: 1px solid #E4E6EB; }
}
</style>

<!-- Compare Bar -->
<div class="compare-bar" id="compareBar">
  <div class="compare-bar-inner">
    <div class="compare-items" id="compareItems"></div>
    <span class="compare-count" id="compareCount">0 of 2 selected</span>
    <button class="compare-clear" onclick="clearCompare()">Clear</button>
    <button class="compare-launch" id="compareLaunchBtn" disabled onclick="openCompareModal()">Compare Side-by-Side</button>
  </div>
</div>

<!-- Compare Modal -->
<div class="compare-modal-overlay" id="compareModalOverlay" onclick="if(event.target===this)closeCompareModal()">
  <div class="compare-modal">
    <div class="compare-modal-header">
      <h2>Head-to-Head Comparison</h2>
      <button class="compare-modal-close" onclick="closeCompareModal()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <div class="compare-columns" id="compareColumns"></div>
  </div>
</div>

<script>
/* ── Compare Feature JS ── */
(function() {
  const compareList = [];
  const MAX_COMPARE = 2;

  // Inject compare buttons into all card footers
  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.card-footer').forEach(footer => {
      const card = footer.closest('.ad-card');
      if (!card) return;
      const btn = document.createElement('button');
      btn.className = 'btn-compare';
      btn.textContent = 'Compare';
      btn.onclick = function(e) {
        e.stopPropagation();
        toggleCompare(card, btn);
      };
      footer.insertBefore(btn, footer.firstChild);
    });
  });

  function getCardData(card) {
    const imgEl = card.querySelector('.card-creative img');
    const nameEl = card.querySelector('.card-meta .name');
    const copyEl = card.querySelector('.card-copy p');
    const scorePill = card.querySelector('.card-meta .score-pill');
    const score = parseFloat(card.dataset.score) || 0;

    // Extract category scores from score bars
    const cats = {};
    card.querySelectorAll('.score-row').forEach(row => {
      const lbl = row.querySelector('.lbl');
      const val = row.querySelector('.val');
      if (lbl && val) {
        cats[lbl.textContent.trim()] = parseFloat(val.textContent) || 0;
      }
    });

    // Extract issues
    const issues = [];
    card.querySelectorAll('.issue-item').forEach(item => {
      const dot = item.querySelector('.issue-dot');
      issues.push({
        text: item.textContent.trim(),
        color: dot ? dot.style.background : '#8A8D91'
      });
    });

    return {
      el: card,
      advertiser: nameEl ? nameEl.textContent.trim() : card.dataset.advertiser || 'Unknown',
      img: imgEl ? imgEl.src : '',
      copy: copyEl ? copyEl.textContent.trim() : '',
      score: score,
      scorePillBg: scorePill ? getComputedStyle(scorePill).backgroundColor : '#8A8D91',
      cats: cats,
      issues: issues
    };
  }

  function scoreColor(s) {
    if (s >= 75) return '#31A24C';
    if (s >= 50) return '#F7B928';
    return '#E4405F';
  }

  window.toggleCompare = function(card, btn) {
    const idx = compareList.findIndex(c => c.el === card);
    if (idx >= 0) {
      compareList.splice(idx, 1);
      btn.classList.remove('selected');
      btn.textContent = 'Compare';
    } else {
      if (compareList.length >= MAX_COMPARE) return;
      compareList.push(getCardData(card));
      btn.classList.add('selected');
      btn.textContent = 'Selected';
    }
    updateCompareBar();
  };

  function updateCompareBar() {
    const bar = document.getElementById('compareBar');
    const items = document.getElementById('compareItems');
    const count = document.getElementById('compareCount');
    const launch = document.getElementById('compareLaunchBtn');

    if (compareList.length === 0) {
      bar.classList.remove('visible');
      return;
    }
    bar.classList.add('visible');
    count.textContent = compareList.length + ' of 2 selected';
    launch.disabled = compareList.length < 2;
    if (compareList.length === 2) {
      launch.textContent = '2 selected \u2014 Compare Side-by-Side';
    } else {
      launch.textContent = 'Compare Side-by-Side';
    }

    items.innerHTML = compareList.map((c, i) => `
      <div class="compare-item">
        ${c.img ? '<img src="' + c.img + '" alt="">' : ''}
        <span>${c.advertiser}</span>
        <button class="remove-compare" onclick="event.stopPropagation();removeCompare(${i})">&times;</button>
      </div>
    `).join('');
  }

  window.removeCompare = function(idx) {
    const removed = compareList.splice(idx, 1)[0];
    if (removed && removed.el) {
      const btn = removed.el.querySelector('.btn-compare');
      if (btn) { btn.classList.remove('selected'); btn.textContent = 'Compare'; }
    }
    updateCompareBar();
  };

  window.clearCompare = function() {
    while (compareList.length) {
      const c = compareList.pop();
      if (c && c.el) {
        const btn = c.el.querySelector('.btn-compare');
        if (btn) { btn.classList.remove('selected'); btn.textContent = 'Compare'; }
      }
    }
    updateCompareBar();
  };

  window.openCompareModal = function() {
    if (compareList.length < 2) return;
    const overlay = document.getElementById('compareModalOverlay');
    const cols = document.getElementById('compareColumns');
    const a = compareList[0], b = compareList[1];
    const aWins = a.score >= b.score;

    cols.innerHTML = [a, b].map((ad, idx) => {
      const other = idx === 0 ? b : a;
      const isWinner = ad.score >= other.score && ad.score !== other.score;
      const isLoser = ad.score < other.score && ad.score !== other.score;
      const badge = isWinner ? '<span class="compare-winner-badge winner">Higher</span>'
                   : isLoser ? '<span class="compare-winner-badge loser">Lower</span>' : '';

      // Score bars for categories
      let catHtml = '';
      const allCats = new Set([...Object.keys(ad.cats), ...Object.keys(other.cats)]);
      allCats.forEach(cat => {
        const v = ad.cats[cat] || 0;
        const ov = other.cats[cat] || 0;
        const arrow = v > ov ? '<span style="color:#31A24C">&#9650;</span>'
                    : v < ov ? '<span style="color:#E4405F">&#9660;</span>'
                    : '<span style="color:#8A8D91">&#9644;</span>';
        catHtml += `
          <div class="compare-score-row">
            <span class="csr-label">${cat}</span>
            <div class="csr-bar"><div class="csr-bar-fill" style="width:${v*10}%;background:${scoreColor(v*10)}"></div></div>
            <span class="csr-val">${v}/10</span>
            <span class="csr-arrow">${arrow}</span>
          </div>`;
      });

      // Issues
      let issuesHtml = '';
      if (ad.issues.length) {
        issuesHtml = '<div class="col-issues"><div class="col-issues-title">Issues</div>' +
          ad.issues.map(iss =>
            `<div class="col-issue-item"><span class="col-issue-dot" style="background:${iss.color}"></span>${iss.text}</div>`
          ).join('') + '</div>';
      }

      return `
        <div class="compare-col">
          <div class="col-advertiser">${ad.advertiser} ${badge}</div>
          <div class="col-score-pill" style="background:${scoreColor(ad.score)}">${ad.score}/100</div>
          ${ad.img ? '<img class="col-image" src="' + ad.img + '" alt="">' : ''}
          <div class="col-copy">${ad.copy}</div>
          <div class="col-scores">${catHtml}</div>
          ${issuesHtml}
        </div>`;
    }).join('');

    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  };

  window.closeCompareModal = function() {
    document.getElementById('compareModalOverlay').classList.remove('open');
    document.body.style.overflow = '';
  };

  function scoreColor(s) {
    if (s >= 75) return '#31A24C';
    if (s >= 50) return '#F7B928';
    return '#E4405F';
  }
})();
</script>
"""


def get_export_html(stats: dict) -> str:
    """Return self-contained HTML + CSS + JS for the print/export feature.

    Args:
        stats: dict with summary data, e.g. {'total': 133, 'trilogy': 30, ...}
    """
    total = stats.get("total", 0)
    trilogy = stats.get("trilogy", 0)
    competitors = total - trilogy
    avg_score = stats.get("avg_score", "")
    date_str = stats.get("date", "")

    return f"""
<!-- ═══════════════════════════════════════
     Export / Print Feature
     ═══════════════════════════════════════ -->
<style>
/* ── Export Button ── */
.btn-export {{
  padding: 8px 16px; border: 1px solid #DADDE1;
  border-radius: 6px; font-size: 13px; font-weight: 500;
  cursor: pointer; background: #FFFFFF; color: #1C1E21;
  font-family: 'Inter', sans-serif; transition: all 0.15s;
  display: inline-flex; align-items: center; gap: 6px;
}}
.btn-export:hover {{ background: #F0F2F5; }}
.btn-export svg {{ color: #65676B; }}

/* ── Print-only view ── */
.print-export-view {{
  display: none;
}}

@media print {{
  /* Hide everything except the export view */
  body > *:not(.print-export-view) {{
    display: none !important;
  }}
  .print-export-view {{
    display: block !important;
    padding: 0;
    margin: 0;
  }}
  .compare-bar, .compare-modal-overlay, .drawer-overlay, .drawer {{
    display: none !important;
  }}
  @page {{
    margin: 20mm 15mm;
    size: A4 portrait;
  }}
}}

.print-export-view {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #1C1E21; max-width: 800px; margin: 0 auto;
}}
.pev-header {{
  text-align: center; margin-bottom: 32px; padding-bottom: 20px;
  border-bottom: 2px solid #1877F2;
}}
.pev-header h1 {{
  font-size: 24px; font-weight: 700; margin-bottom: 4px;
}}
.pev-header .pev-date {{
  font-size: 14px; color: #65676B;
}}
.pev-stats {{
  display: flex; gap: 16px; margin-bottom: 32px; flex-wrap: wrap;
}}
.pev-stat {{
  flex: 1; min-width: 120px; background: #F0F2F5;
  border-radius: 8px; padding: 16px; text-align: center;
}}
.pev-stat .pev-val {{
  font-size: 28px; font-weight: 700; color: #1877F2;
}}
.pev-stat .pev-lbl {{
  font-size: 12px; color: #65676B; margin-top: 4px;
}}
.pev-section {{
  margin-bottom: 28px;
}}
.pev-section h2 {{
  font-size: 16px; font-weight: 700; margin-bottom: 12px;
  padding-bottom: 6px; border-bottom: 1px solid #E4E6EB;
}}
.pev-ad-row {{
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid #E4E6EB;
}}
.pev-ad-row .pev-rank {{
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; color: #fff; flex-shrink: 0;
}}
.pev-ad-row .pev-ad-info {{
  flex: 1;
}}
.pev-ad-row .pev-ad-name {{
  font-size: 14px; font-weight: 600;
}}
.pev-ad-row .pev-ad-copy {{
  font-size: 12px; color: #65676B; margin-top: 2px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  max-width: 500px;
}}
.pev-ad-row .pev-ad-score {{
  padding: 4px 12px; border-radius: 12px;
  font-size: 13px; font-weight: 700; color: #fff; flex-shrink: 0;
}}
.pev-insights {{
  font-size: 14px; line-height: 1.7; color: #1C1E21;
}}
.pev-insights li {{
  margin-bottom: 6px;
}}
.pev-footer {{
  margin-top: 32px; padding-top: 16px;
  border-top: 1px solid #E4E6EB;
  font-size: 11px; color: #8A8D91; text-align: center;
}}
</style>

<!-- Hidden print-optimized view (populated by JS on export) -->
<div class="print-export-view" id="printExportView"></div>

<script>
/* ── Export Feature JS ── */
(function() {{
  const exportStats = {{
    total: {total},
    trilogy: {trilogy},
    competitors: {competitors},
    avg_score: "{avg_score}",
    date: "{date_str}"
  }};

  // Inject export button into header
  document.addEventListener('DOMContentLoaded', function() {{
    const headerMeta = document.querySelector('.header-meta');
    if (headerMeta) {{
      const btn = document.createElement('button');
      btn.className = 'btn-export';
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Export';
      btn.onclick = triggerExport;
      headerMeta.parentNode.insertBefore(btn, headerMeta);
    }}
  }});

  function scoreColor(s) {{
    if (s >= 75) return '#31A24C';
    if (s >= 50) return '#F7B928';
    return '#E4405F';
  }}

  function triggerExport() {{
    // Gather all card data
    const cards = [];
    document.querySelectorAll('.ad-card').forEach(card => {{
      const nameEl = card.querySelector('.card-meta .name');
      const copyEl = card.querySelector('.card-copy p');
      const score = parseFloat(card.dataset.score) || -1;
      cards.push({{
        advertiser: nameEl ? nameEl.textContent.trim() : 'Unknown',
        copy: copyEl ? copyEl.textContent.trim() : '',
        score: score
      }});
    }});

    // Sort by score descending
    const scored = cards.filter(c => c.score >= 0).sort((a, b) => b.score - a.score);
    const top3 = scored.slice(0, 3);
    const bottom3 = scored.slice(-3).reverse();

    // Gather insights
    const insightItems = [];
    document.querySelectorAll('.drawer .insight-item').forEach(el => {{
      insightItems.push(el.textContent.trim());
    }});
    document.querySelectorAll('.drawer .rec-item').forEach(el => {{
      insightItems.push(el.textContent.trim());
    }});

    // Compute live stats if not provided
    const total = exportStats.total || cards.length;
    const trilogy = exportStats.trilogy || cards.filter(c => c.advertiser === 'Trilogy Care').length;
    const competitors = total - trilogy;
    const avgNum = scored.length ? (scored.reduce((s, c) => s + c.score, 0) / scored.length).toFixed(1) : '0';
    const reportDate = exportStats.date || new Date().toLocaleDateString('en-AU', {{ day: 'numeric', month: 'long', year: 'numeric' }});

    function adRow(ad, idx, color) {{
      return `
        <div class="pev-ad-row">
          <div class="pev-rank" style="background:${{color}}">${{idx + 1}}</div>
          <div class="pev-ad-info">
            <div class="pev-ad-name">${{ad.advertiser}}</div>
            <div class="pev-ad-copy">${{ad.copy.substring(0, 120)}}${{ad.copy.length > 120 ? '...' : ''}}</div>
          </div>
          <div class="pev-ad-score" style="background:${{scoreColor(ad.score)}}">${{ad.score}}/100</div>
        </div>`;
    }}

    const html = `
      <div class="pev-header">
        <h1>TC Ads QA Report — Support at Home</h1>
        <div class="pev-date">${{reportDate}}</div>
      </div>

      <div class="pev-stats">
        <div class="pev-stat"><div class="pev-val">${{total}}</div><div class="pev-lbl">Total Ads</div></div>
        <div class="pev-stat"><div class="pev-val">${{trilogy}}</div><div class="pev-lbl">Trilogy Care</div></div>
        <div class="pev-stat"><div class="pev-val">${{competitors}}</div><div class="pev-lbl">Competitors</div></div>
        <div class="pev-stat"><div class="pev-val">${{avgNum}}</div><div class="pev-lbl">Avg Score</div></div>
      </div>

      <div class="pev-section">
        <h2>Top 3 Performing Ads</h2>
        ${{top3.map((a, i) => adRow(a, i, '#31A24C')).join('')}}
      </div>

      <div class="pev-section">
        <h2>Bottom 3 Performing Ads</h2>
        ${{bottom3.map((a, i) => adRow(a, i, '#E4405F')).join('')}}
      </div>

      <div class="pev-section">
        <h2>Competitive Insights</h2>
        <div class="pev-insights">
          <ul>${{insightItems.slice(0, 8).map(i => '<li>' + i + '</li>').join('')}}</ul>
        </div>
      </div>

      <div class="pev-footer">
        Generated by TC Ads QA &middot; Trilogy Care &middot; ${{reportDate}}
      </div>
    `;

    document.getElementById('printExportView').innerHTML = html;

    // Small delay to let DOM render, then print
    setTimeout(function() {{
      window.print();
    }}, 200);
  }}

  // Expose for external calls
  window.triggerExport = triggerExport;
}})();
</script>
"""


def get_human_review_html() -> str:
    """Return HTML/CSS/JS for thumbs up/down human review on ad cards."""
    return """
<!-- Human Review — Thumbs Up/Down -->
<style>
.human-review { display: flex; gap: 4px; margin-left: auto; }
.review-btn {
  width: 28px; height: 28px; border: 1px solid #DADDE1; border-radius: 6px;
  background: white; cursor: pointer; display: flex; align-items: center;
  justify-content: center; transition: all 0.15s; font-size: 14px;
}
.review-btn:hover { background: #F0F2F5; }
.review-btn.up-active { background: #E8F5E9; border-color: #31A24C; }
.review-btn.down-active { background: #FFEBE9; border-color: #E4405F; }
.review-count { font-size: 10px; color: #8A8D91; margin-top: 2px; text-align: center; }
</style>
<script>
(function() {
  // Load reviews from localStorage
  const STORAGE_KEY = 'tc_ads_qa_reviews';
  function getReviews() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch { return {}; }
  }
  function saveReviews(reviews) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reviews));
  }

  window.reviewAd = function(adKey, vote) {
    const reviews = getReviews();
    const current = reviews[adKey];
    if (current === vote) {
      delete reviews[adKey]; // Toggle off
    } else {
      reviews[adKey] = vote; // 'up' or 'down'
    }
    saveReviews(reviews);
    updateReviewUI(adKey);
  };

  function updateReviewUI(adKey) {
    const reviews = getReviews();
    const vote = reviews[adKey];
    const container = document.querySelector(`[data-review-key="${adKey}"]`);
    if (!container) return;
    container.querySelector('.up-btn')?.classList.toggle('up-active', vote === 'up');
    container.querySelector('.down-btn')?.classList.toggle('down-active', vote === 'down');
  }

  // Init all review UIs on page load
  document.addEventListener('DOMContentLoaded', function() {
    const reviews = getReviews();
    for (const [key, vote] of Object.entries(reviews)) {
      updateReviewUI(key);
    }
    // Show review stats
    const ups = Object.values(reviews).filter(v => v === 'up').length;
    const downs = Object.values(reviews).filter(v => v === 'down').length;
    const total = Object.keys(reviews).length;
    if (total > 0) {
      console.log(`Human reviews: ${ups} up, ${downs} down, ${total} total`);
    }
  });
})();
</script>
"""


def get_lightbox_html() -> str:
    """Return HTML/CSS/JS for a full-screen image lightbox with ad details."""
    return """
<!-- Lightbox — Full-screen ad preview -->
<style>
.lightbox-overlay {
  display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85);
  z-index: 500; backdrop-filter: blur(8px);
  justify-content: center; align-items: center; padding: 40px;
}
.lightbox-overlay.open { display: flex; }
.lightbox-content {
  background: white; border-radius: 12px; max-width: 900px; width: 100%;
  max-height: 90vh; overflow-y: auto; display: flex;
}
.lightbox-image {
  flex: 1; min-width: 400px; background: #F0F2F5;
  display: flex; align-items: center; justify-content: center;
  border-radius: 12px 0 0 12px; overflow: hidden;
}
.lightbox-image img { max-width: 100%; max-height: 80vh; object-fit: contain; }
.lightbox-details {
  width: 320px; padding: 24px; border-left: 1px solid #E4E6EB;
  overflow-y: auto;
}
.lightbox-details h3 { font-size: 16px; margin-bottom: 8px; }
.lightbox-details .meta { font-size: 13px; color: #65676B; margin-bottom: 16px; }
.lightbox-details .copy { font-size: 14px; line-height: 1.6; margin-bottom: 16px; }
.lightbox-details .actions { display: flex; gap: 8px; margin-top: 16px; }
.lightbox-details .actions a, .lightbox-details .actions button {
  padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 600;
  text-decoration: none; cursor: pointer; border: 1px solid #DADDE1;
  background: white; color: #1C1E21;
}
.lightbox-details .actions .primary { background: #1877F2; color: white; border-color: #1877F2; }
.lightbox-close {
  position: fixed; top: 16px; right: 16px; z-index: 501;
  width: 40px; height: 40px; border-radius: 50%;
  background: rgba(255,255,255,0.2); border: none; color: white;
  font-size: 24px; cursor: pointer; display: none;
  align-items: center; justify-content: center;
}
.lightbox-overlay.open ~ .lightbox-close { display: flex; }
@media (max-width: 768px) {
  .lightbox-content { flex-direction: column; }
  .lightbox-image { min-width: auto; border-radius: 12px 12px 0 0; }
  .lightbox-details { width: auto; }
}
</style>

<div class="lightbox-overlay" id="lightbox" onclick="if(event.target===this)closeLightbox()">
  <div class="lightbox-content">
    <div class="lightbox-image" id="lbImage"></div>
    <div class="lightbox-details" id="lbDetails"></div>
  </div>
</div>
<button class="lightbox-close" id="lbClose" onclick="closeLightbox()">×</button>

<script>
(function() {
  window.openLightbox = function(card) {
    const img = card.querySelector('.card-creative img');
    const name = card.querySelector('.card-meta .name')?.textContent || '';
    const sub = card.querySelector('.card-meta .sub')?.textContent || '';
    const copy = card.querySelector('.card-copy p')?.textContent || '';
    const score = card.querySelector('.score-pill')?.textContent || '';
    const url = card.querySelector('.card-creative')?.getAttribute('onclick')?.match(/'([^']+)'/)?.[1] || '#';
    const tags = card.querySelector('.card-copy .tags')?.innerHTML || '';

    const imgHtml = img ? `<img src="${img.src}" alt="Ad">` : '<div style="padding:60px;color:#8A8D91;">No preview</div>';
    document.getElementById('lbImage').innerHTML = imgHtml;
    document.getElementById('lbDetails').innerHTML = `
      <h3>${name}</h3>
      <div class="meta">${sub}${score ? ' · Score: <strong>' + score + '</strong>' : ''}</div>
      <div class="copy">${copy}</div>
      <div style="margin:8px 0;">${tags}</div>
      <div class="actions">
        <a href="${url}" target="_blank" class="primary">View Original →</a>
      </div>
    `;
    document.getElementById('lightbox').classList.add('open');
  };

  window.closeLightbox = function() {
    document.getElementById('lightbox').classList.remove('open');
  };

  // ESC key closes lightbox
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeLightbox();
  });
})();
</script>
"""
