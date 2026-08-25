/**
 * Mem0 Local Memory Manager Frontend Application
 */

const API_BASE = '/api/v1';

// State
let allMemories = [];
let currentSearchQuery = '';

// DOM Elements
const memoriesGrid = document.getElementById('memoriesGrid');
const emptyState = document.getElementById('emptyState');
const resultsCount = document.getElementById('resultsCount');
const searchInput = document.getElementById('searchInput');
const btnSearch = document.getElementById('btnSearch');
const btnResetSearch = document.getElementById('btnResetSearch');
const filterProject = document.getElementById('filterProject');
const filterCategory = document.getElementById('filterCategory');
const filterUser = document.getElementById('filterUser');
const btnRefresh = document.getElementById('btnRefresh');

// Header Stats
const statTotal = document.getElementById('statTotal');
const statProjects = document.getElementById('statProjects');

// Modal Elements
const memoryModal = document.getElementById('memoryModal');
const modalTitle = document.getElementById('modalTitle');
const modalMemoryId = document.getElementById('modalMemoryId');
const modalContent = document.getElementById('modalContent');
const modalProject = document.getElementById('modalProject');
const modalCategory = document.getElementById('modalCategory');
const modalTags = document.getElementById('modalTags');
const modalMetadata = document.getElementById('modalMetadata');
const btnModalClose = document.getElementById('btnModalClose');
const btnModalCancel = document.getElementById('btnModalCancel');
const btnModalSave = document.getElementById('btnModalSave');
const btnOpenAddModal = document.getElementById('btnOpenAddModal');

// History Modal
const historyModal = document.getElementById('historyModal');
const historyList = document.getElementById('historyList');
const btnHistoryClose = document.getElementById('btnHistoryClose');
const btnHistoryDone = document.getElementById('btnHistoryDone');

// Export / Import
const btnExport = document.getElementById('btnExport');
const btnImport = document.getElementById('btnImport');
const importModal = document.getElementById('importModal');
const importPayload = document.getElementById('importPayload');
const btnImportClose = document.getElementById('btnImportClose');
const btnImportCancel = document.getElementById('btnImportCancel');
const btnImportSubmit = document.getElementById('btnImportSubmit');

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadStats();
  fetchMemories();
});

function setupEventListeners() {
  btnSearch.addEventListener('click', handleSearch);
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSearch();
  });
  btnResetSearch.addEventListener('click', resetSearch);

  filterProject.addEventListener('change', () => {
    if (currentSearchQuery) handleSearch();
    else fetchMemories();
  });

  filterCategory.addEventListener('change', () => {
    if (currentSearchQuery) handleSearch();
    else fetchMemories();
  });

  filterUser.addEventListener('change', () => {
    if (currentSearchQuery) handleSearch();
    else fetchMemories();
  });

  btnRefresh.addEventListener('click', () => {
    loadStats();
    if (currentSearchQuery) handleSearch();
    else fetchMemories();
  });

  // Modal controls
  btnOpenAddModal.addEventListener('click', () => openMemoryModal());
  btnModalClose.addEventListener('click', closeMemoryModal);
  btnModalCancel.addEventListener('click', closeMemoryModal);
  btnModalSave.addEventListener('click', saveMemory);

  btnHistoryClose.addEventListener('click', () => historyModal.classList.remove('open'));
  btnHistoryDone.addEventListener('click', () => historyModal.classList.remove('open'));

  // Export / Import
  btnExport.addEventListener('click', handleExport);
  btnImport.addEventListener('click', () => importModal.classList.add('open'));
  btnImportClose.addEventListener('click', () => importModal.classList.remove('open'));
  btnImportCancel.addEventListener('click', () => importModal.classList.remove('open'));
  btnImportSubmit.addEventListener('click', handleImport);
}

// Fetch Stats
async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) return;
    const data = await res.json();
    statTotal.textContent = data.total_memories || 0;
    statProjects.textContent = Object.keys(data.projects || {}).length;

    // Update project filter options dynamically
    const currentProjVal = filterProject.value;
    filterProject.innerHTML = '<option value="all">All Projects</option>';
    const projects = Object.keys(data.projects || {});
    projects.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = `${p} (${data.projects[p]})`;
      filterProject.appendChild(opt);
    });
    if (projects.includes(currentProjVal)) {
      filterProject.value = currentProjVal;
    }
  } catch (err) {
    console.error('Failed to load stats', err);
  }
}

// Fetch Memories List
async function fetchMemories() {
  try {
    resultsCount.textContent = 'Loading...';
    const params = new URLSearchParams();
    const proj = filterProject.value;
    const cat = filterCategory.value;
    const user = filterUser.value;

    if (proj && proj !== 'all') params.append('project', proj);
    if (cat && cat !== 'all') params.append('category', cat);
    if (user && user !== 'all') params.append('user_id', user);
    params.append('limit', '100');

    const res = await fetch(`${API_BASE}/memories?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch memories');
    const data = await res.json();
    allMemories = data.memories || [];
    renderMemories(allMemories);
    resultsCount.textContent = `${allMemories.length} memories displayed`;
  } catch (err) {
    console.error(err);
    resultsCount.textContent = 'Error loading memories';
  }
}

// Semantic Search
async function handleSearch() {
  const query = searchInput.value.trim();
  currentSearchQuery = query;
  if (!query) {
    resetSearch();
    return;
  }

  btnResetSearch.style.display = 'inline-flex';
  resultsCount.textContent = 'Searching vector space...';

  try {
    const proj = filterProject.value !== 'all' ? filterProject.value : null;
    const cat = filterCategory.value !== 'all' ? filterCategory.value : null;
    const user = filterUser.value !== 'all' ? filterUser.value : null;

    const res = await fetch(`${API_BASE}/memories/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        project: proj,
        category: cat,
        user_id: user,
        limit: 50
      })
    });

    if (!res.ok) throw new Error('Search failed');
    const results = await res.json();
    renderMemories(results);
    resultsCount.textContent = `${results.length} semantic matches found`;
  } catch (err) {
    console.error(err);
    resultsCount.textContent = 'Search failed';
  }
}

function resetSearch() {
  searchInput.value = '';
  currentSearchQuery = '';
  btnResetSearch.style.display = 'none';
  fetchMemories();
}

// Render Memory Cards
function renderMemories(memories) {
  memoriesGrid.innerHTML = '';
  if (!memories || memories.length === 0) {
    emptyState.style.display = 'block';
    return;
  }
  emptyState.style.display = 'none';

  memories.forEach(mem => {
    const card = document.createElement('div');
    card.className = 'memory-card';

    const catClass = `badge-cat-${(mem.category || 'general').toLowerCase()}`;
    const dateFormatted = new Date((mem.updated_at || mem.created_at) * 1000).toLocaleString();

    let tagsHtml = '';
    if (mem.tags && mem.tags.length > 0) {
      tagsHtml = `<div class="card-tags">${mem.tags.map(t => `<span class="tag-pill">#${escapeHtml(t)}</span>`).join('')}</div>`;
    }

    let scoreBadge = '';
    if (mem.relevance_score !== undefined) {
      const pct = Math.round(mem.relevance_score * 100);
      scoreBadge = `<span class="relevance-score" title="Cosine similarity score">${pct}% match</span>`;
    }

    card.innerHTML = `
      <div class="card-top">
        <div class="badges-group">
          <span class="badge badge-proj">${escapeHtml(mem.project || 'general')}</span>
          <span class="badge ${catClass}">${escapeHtml(mem.category || 'general')}</span>
          ${scoreBadge}
        </div>
        <span class="card-date">${dateFormatted}</span>
      </div>
      <div class="card-body">${escapeHtml(mem.content)}</div>
      ${tagsHtml}
      <div class="card-actions">
        <button class="btn btn-secondary btn-sm" onclick="viewHistory('${mem.id}')">History</button>
        <button class="btn btn-secondary btn-sm" onclick="editMemory('${mem.id}')">Edit</button>
        <button class="btn btn-danger-text btn-sm" onclick="deleteMemory('${mem.id}')">Delete</button>
      </div>
    `;

    memoriesGrid.appendChild(card);
  });
}

// Open Add/Edit Modal
function openMemoryModal(mem = null) {
  if (mem) {
    modalTitle.textContent = 'Edit Memory';
    modalMemoryId.value = mem.id;
    modalContent.value = mem.content;
    modalProject.value = mem.project || 'general';
    modalCategory.value = mem.category || 'general';
    modalTags.value = (mem.tags || []).join(', ');
    modalMetadata.value = JSON.stringify(mem.metadata || {}, null, 2);
  } else {
    modalTitle.textContent = 'Add New Memory';
    modalMemoryId.value = '';
    modalContent.value = '';
    modalProject.value = filterProject.value !== 'all' ? filterProject.value : 'fieldnation';
    modalCategory.value = filterCategory.value !== 'all' ? filterCategory.value : 'guideline';
    modalTags.value = '';
    modalMetadata.value = '{}';
  }
  memoryModal.classList.add('open');
}

function closeMemoryModal() {
  memoryModal.classList.remove('open');
}

// Save Memory (Create or Update)
async function saveMemory() {
  const content = modalContent.value.trim();
  if (!content) {
    alert('Please enter memory content');
    return;
  }

  const id = modalMemoryId.value;
  const project = modalProject.value.trim() || 'general';
  const category = modalCategory.value;
  const tags = modalTags.value.split(',').map(t => t.trim()).filter(Boolean);
  
  let metadata = {};
  try {
    metadata = JSON.parse(modalMetadata.value || '{}');
  } catch (err) {
    alert('Invalid JSON in custom metadata field');
    return;
  }

  btnModalSave.disabled = true;
  btnModalSave.textContent = 'Saving...';

  try {
    if (id) {
      // Update
      const res = await fetch(`${API_BASE}/memories/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, project, category, tags, metadata })
      });
      if (!res.ok) throw new Error('Update failed');
    } else {
      // Create
      const res = await fetch(`${API_BASE}/memories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          project,
          category,
          tags,
          metadata,
          user_id: 'default'
        })
      });
      if (!res.ok) throw new Error('Create failed');
    }

    closeMemoryModal();
    loadStats();
    if (currentSearchQuery) handleSearch();
    else fetchMemories();
  } catch (err) {
    alert('Failed to save memory: ' + err.message);
  } finally {
    btnModalSave.disabled = false;
    btnModalSave.textContent = 'Save Memory';
  }
}

// Edit Memory
window.editMemory = async function(id) {
  try {
    const res = await fetch(`${API_BASE}/memories/${id}`);
    if (!res.ok) throw new Error('Memory not found');
    const mem = await res.json();
    openMemoryModal(mem);
  } catch (err) {
    alert('Could not load memory details: ' + err.message);
  }
};

// Delete Memory
window.deleteMemory = async function(id) {
  if (!confirm('Are you sure you want to delete this memory? It will be removed from local vector storage.')) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/memories/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Delete failed');
    loadStats();
    if (currentSearchQuery) handleSearch();
    else fetchMemories();
  } catch (err) {
    alert('Could not delete memory: ' + err.message);
  }
};

// View History
window.viewHistory = async function(id) {
  try {
    const res = await fetch(`${API_BASE}/memories/${id}/history`);
    if (!res.ok) throw new Error('Could not fetch history');
    const data = await res.json();
    const history = data.history || [];

    historyList.innerHTML = '';
    if (history.length === 0) {
      historyList.innerHTML = '<p class="text-muted">No modification history recorded for this entry.</p>';
    } else {
      history.forEach(h => {
        const item = document.createElement('div');
        item.className = 'timeline-item';
        const dateStr = new Date(h.timestamp * 1000).toLocaleString();
        item.innerHTML = `
          <div class="timeline-marker"></div>
          <div class="timeline-time">${dateStr}</div>
          <div class="timeline-action">Action: <span class="badge badge-cat-decision">${h.action}</span></div>
          <div class="timeline-content">${escapeHtml(h.new_content || h.previous_content || 'Metadata update')}</div>
        `;
        historyList.appendChild(item);
      });
    }

    historyModal.classList.add('open');
  } catch (err) {
    alert('Could not load history: ' + err.message);
  }
};

// Export Data
async function handleExport() {
  try {
    const res = await fetch(`${API_BASE}/export`, { method: 'POST' });
    if (!res.ok) throw new Error('Export failed');
    const data = await res.json();
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mem0-backup-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert('Failed to export backup: ' + err.message);
  }
}

// Import Data
async function handleImport() {
  const payloadStr = importPayload.value.trim();
  if (!payloadStr) {
    alert('Please paste JSON payload');
    return;
  }

  try {
    const payload = JSON.parse(payloadStr);
    btnImportSubmit.disabled = true;
    btnImportSubmit.textContent = 'Importing...';

    const res = await fetch(`${API_BASE}/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('Import failed');
    const result = await res.json();
    alert(`Successfully imported ${result.imported_count} memories!`);
    importModal.classList.remove('open');
    importPayload.value = '';
    loadStats();
    fetchMemories();
  } catch (err) {
    alert('Import failed: ' + err.message);
  } finally {
    btnImportSubmit.disabled = false;
    btnImportSubmit.textContent = 'Import Memories';
  }
}

// Utility: Escape HTML to prevent XSS
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
