"""
Swipe File Boards — localStorage-based board system for saving and organizing ads.
Users can save ads to named boards (like Pinterest), then view boards as collections.
"""


def get_swipe_boards_html() -> str:
    """Return HTML/CSS/JS for the swipe boards feature."""
    return """
<!-- Swipe Boards — Save & Organize Ads -->
<style>
/* Board drawer */
.boards-drawer {
  position: fixed; top: 0; right: -420px; width: 420px; height: 100vh;
  background: white; z-index: 400; overflow-y: auto;
  box-shadow: -4px 0 24px rgba(0,0,0,0.15);
  transition: right 0.3s ease; padding: 0;
}
.boards-drawer.open { right: 0; }
.boards-header {
  padding: 20px 24px; border-bottom: 1px solid #E4E6EB;
  display: flex; align-items: center; gap: 12px;
  position: sticky; top: 0; background: white; z-index: 1;
}
.boards-header h2 { font-size: 18px; flex: 1; }
.boards-header .close-boards {
  width: 32px; height: 32px; border-radius: 50%; border: none;
  background: #F0F2F5; cursor: pointer; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
}
.boards-body { padding: 16px 24px; }
.board-create {
  display: flex; gap: 8px; margin-bottom: 16px;
}
.board-create input {
  flex: 1; padding: 8px 12px; border: 1px solid #DADDE1;
  border-radius: 8px; font-size: 14px; font-family: inherit;
}
.board-create button {
  padding: 8px 16px; background: #1877F2; color: white;
  border: none; border-radius: 8px; font-size: 13px;
  font-weight: 600; cursor: pointer;
}
.board-item {
  padding: 12px; border: 1px solid #E4E6EB; border-radius: 8px;
  margin-bottom: 8px; cursor: pointer; transition: all 0.15s;
}
.board-item:hover { background: #F0F2F5; }
.board-item-header {
  display: flex; align-items: center; gap: 8px;
}
.board-item-name { font-size: 14px; font-weight: 600; flex: 1; }
.board-item-count {
  font-size: 12px; color: #65676B; background: #F0F2F5;
  padding: 2px 8px; border-radius: 10px;
}
.board-item-preview {
  display: flex; gap: 4px; margin-top: 8px; overflow: hidden;
}
.board-item-preview img {
  width: 48px; height: 48px; border-radius: 4px; object-fit: cover;
}
.board-item-delete {
  font-size: 12px; color: #E4405F; cursor: pointer; margin-left: 8px;
}
/* Save button on cards */
.save-to-board {
  width: 28px; height: 28px; border: 1px solid #DADDE1; border-radius: 6px;
  background: white; cursor: pointer; display: flex; align-items: center;
  justify-content: center; transition: all 0.15s; font-size: 14px;
}
.save-to-board:hover { background: #F0F2F5; }
.save-to-board.saved { background: #FFF3E0; border-color: #F7B928; }
/* Board view overlay */
.board-view-overlay {
  display: none; position: fixed; inset: 0; background: white; z-index: 500;
  overflow-y: auto; padding: 24px;
}
.board-view-overlay.open { display: block; }
.board-view-header {
  display: flex; align-items: center; gap: 16px; margin-bottom: 24px;
  padding-bottom: 16px; border-bottom: 1px solid #E4E6EB;
}
.board-view-header h2 { font-size: 20px; flex: 1; }
.board-view-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
</style>

<div class="boards-drawer" id="boardsDrawer">
  <div class="boards-header">
    <h2>Swipe File</h2>
    <button class="close-boards" onclick="closeBoardsDrawer()">×</button>
  </div>
  <div class="boards-body">
    <div class="board-create">
      <input type="text" id="newBoardName" placeholder="New board name..." onkeydown="if(event.key==='Enter')createBoard()">
      <button onclick="createBoard()">Create</button>
    </div>
    <div id="boardsList"></div>
  </div>
</div>

<div class="board-view-overlay" id="boardView">
  <div class="board-view-header">
    <button onclick="closeBoardView()" style="padding:8px 16px;border:1px solid #DADDE1;border-radius:8px;background:white;cursor:pointer;font-size:13px;">← Back</button>
    <h2 id="boardViewTitle"></h2>
    <span id="boardViewCount" style="color:#65676B;font-size:14px;"></span>
  </div>
  <div class="board-view-grid" id="boardViewGrid"></div>
</div>

<script>
(function() {
  const BOARDS_KEY = 'tc_ads_qa_boards';

  function getBoards() {
    try { return JSON.parse(localStorage.getItem(BOARDS_KEY) || '{}'); } catch { return {}; }
  }
  function saveBoards(boards) {
    localStorage.setItem(BOARDS_KEY, JSON.stringify(boards));
  }

  window.openBoardsDrawer = function() {
    document.getElementById('boardsDrawer').classList.add('open');
    renderBoardsList();
  };
  window.closeBoardsDrawer = function() {
    document.getElementById('boardsDrawer').classList.remove('open');
  };

  window.createBoard = function() {
    const input = document.getElementById('newBoardName');
    const name = input.value.trim();
    if (!name) return;
    const boards = getBoards();
    if (!boards[name]) boards[name] = [];
    saveBoards(boards);
    input.value = '';
    renderBoardsList();
  };

  window.saveAdToBoard = function(boardName, adKey, adData) {
    const boards = getBoards();
    if (!boards[boardName]) boards[boardName] = [];
    // Avoid duplicates
    if (!boards[boardName].find(a => a.key === adKey)) {
      boards[boardName].push({
        key: adKey,
        advertiser: adData.advertiser || '',
        copy: adData.copy || '',
        img: adData.img || '',
        score: adData.score || '',
        url: adData.url || '',
      });
    }
    saveBoards(boards);
    renderBoardsList();
  };

  window.saveCardToBoard = function(card) {
    const boards = getBoards();
    const boardNames = Object.keys(boards);
    if (boardNames.length === 0) {
      alert('Create a board first! Click the Swipe File button in the nav.');
      return;
    }
    // Quick save to first board, or prompt
    const boardName = boardNames.length === 1 ? boardNames[0] : prompt('Save to board:\\n' + boardNames.join('\\n'));
    if (!boardName || !boards[boardName]) return;

    const adKey = card.dataset.advertiser + '_' + (card.querySelector('.tag-id')?.textContent || Math.random());
    const adData = {
      advertiser: card.querySelector('.card-meta .name')?.textContent || '',
      copy: card.querySelector('.card-copy p')?.textContent || '',
      img: card.querySelector('.card-creative img')?.src || '',
      score: card.querySelector('.score-pill')?.textContent || '',
      url: card.querySelector('.btn-primary')?.getAttribute('onclick')?.match(/'([^']+)'/)?.[1] || '',
    };
    saveAdToBoard(boardName, adKey, adData);
    // Visual feedback
    const btn = card.querySelector('.save-to-board');
    if (btn) { btn.classList.add('saved'); btn.textContent = '★'; }
  };

  function renderBoardsList() {
    const boards = getBoards();
    const container = document.getElementById('boardsList');
    container.innerHTML = '';
    for (const [name, ads] of Object.entries(boards)) {
      const el = document.createElement('div');
      el.className = 'board-item';
      el.innerHTML = `
        <div class="board-item-header">
          <span class="board-item-name">${name}</span>
          <span class="board-item-count">${ads.length} ads</span>
          <span class="board-item-delete" onclick="event.stopPropagation();deleteBoard('${name}')">Delete</span>
        </div>
        <div class="board-item-preview">
          ${ads.slice(0, 4).map(a => a.img ? `<img src="${a.img}" alt="">` : '').join('')}
        </div>
      `;
      el.addEventListener('click', () => openBoardView(name));
      container.appendChild(el);
    }
    if (Object.keys(boards).length === 0) {
      container.innerHTML = '<p style="color:#8A8D91;font-size:13px;text-align:center;padding:20px;">No boards yet. Create one above to start saving ads.</p>';
    }
  }

  window.deleteBoard = function(name) {
    if (!confirm(`Delete board "${name}"?`)) return;
    const boards = getBoards();
    delete boards[name];
    saveBoards(boards);
    renderBoardsList();
  };

  window.openBoardView = function(name) {
    const boards = getBoards();
    const ads = boards[name] || [];
    document.getElementById('boardViewTitle').textContent = name;
    document.getElementById('boardViewCount').textContent = `${ads.length} ads`;
    const grid = document.getElementById('boardViewGrid');
    grid.innerHTML = '';
    for (const ad of ads) {
      grid.innerHTML += `
        <div style="background:white;border:1px solid #E4E6EB;border-radius:12px;overflow:hidden;">
          ${ad.img ? `<img src="${ad.img}" style="width:100%;max-height:300px;object-fit:contain;background:#F0F2F5;">` : '<div style="height:120px;background:#F0F2F5;display:flex;align-items:center;justify-content:center;color:#8A8D91;">No preview</div>'}
          <div style="padding:12px;">
            <div style="font-weight:600;font-size:14px;">${ad.advertiser}</div>
            <div style="font-size:13px;color:#65676B;margin-top:4px;">${ad.copy?.substring(0, 150) || ''}</div>
            ${ad.score ? `<div style="margin-top:8px;"><span style="background:#1877F2;color:white;padding:2px 8px;border-radius:6px;font-size:12px;font-weight:700;">${ad.score}</span></div>` : ''}
            ${ad.url ? `<a href="${ad.url}" target="_blank" style="display:inline-block;margin-top:8px;font-size:12px;color:#1877F2;">View Original →</a>` : ''}
          </div>
        </div>
      `;
    }
    document.getElementById('boardView').classList.add('open');
    closeBoardsDrawer();
  };

  window.closeBoardView = function() {
    document.getElementById('boardView').classList.remove('open');
  };
})();
</script>
"""