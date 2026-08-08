const API_BASE = '/api';

export async function fetchMemories(category = null, tag = null) {
  let url = `${API_BASE}/memories`;
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (tag) params.append('tag', tag);
  if (params.toString()) url += `?${params.toString()}`;

  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch memories');
  return res.json();
}

export async function fetchMemoryDetail(memoryId) {
  const res = await fetch(`${API_BASE}/memories/${memoryId}`);
  if (!res.ok) throw new Error('Failed to fetch memory detail');
  return res.json();
}

export async function fetchCategories() {
  const res = await fetch(`${API_BASE}/categories`);
  if (!res.ok) throw new Error('Failed to fetch categories');
  return res.json();
}

export async function createOrUpdateMemory(memoryData) {
  const res = await fetch(`${API_BASE}/memories`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(memoryData),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to save memory');
  }
  return res.json();
}

export async function deleteMemory(memoryId) {
  const res = await fetch(`${API_BASE}/memories/${memoryId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete memory');
  return res.json();
}

export async function searchMemories(query, categoryFilter = null) {
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, category_filter: categoryFilter, top_k: 6 }),
  });
  if (!res.ok) throw new Error('Failed to search memories');
  return res.json();
}

export async function getBackupStatus() {
  const res = await fetch(`${API_BASE}/backup`);
  if (!res.ok) throw new Error('Failed to fetch backup status');
  return res.json();
}

export async function triggerBackup() {
  const res = await fetch(`${API_BASE}/backup`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to trigger backup');
  return res.json();
}

export async function sendChatMessage(message, model = null) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, model }),
  });
  if (!res.ok) throw new Error('Failed to send chat message');
  return res.json();
}

export async function purgeAllData() {
  const res = await fetch(`${API_BASE}/purge`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to purge data');
  return res.json();
}

export async function syncMemories() {
  const res = await fetch(`${API_BASE}/sync`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to sync memories');
  return res.json();
}

export async function fetchMemoryVersions(memoryId) {
  const res = await fetch(`${API_BASE}/memories/${memoryId}/versions`);
  if (!res.ok) throw new Error('Failed to fetch memory versions');
  return res.json();
}

export async function revertMemory(memoryId, versionNumber = null) {
  const res = await fetch(`${API_BASE}/memories/${memoryId}/revert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ version_number: versionNumber }),
  });
  if (!res.ok) throw new Error('Failed to revert memory');
  return res.json();
}

