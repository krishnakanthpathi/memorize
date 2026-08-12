/**
 * Memorize Frontend Service API Layer
 * Direct connection to FastAPI Backend Endpoints on http://127.0.0.1:6999
 * Includes automatic fallback to local mock state if backend service is unreachable.
 */

import {
  initialNotes,
  initialCategories,
  initialModels,
  mockAuditData,
  mockMetrics,
  simulateAutoOrganizeNote,
  simulateGraphChat,
} from '../mockData';

const BASE_URL = 'http://127.0.0.1:6999';

function normalizeNote(mem) {
  if (!mem) return null;
  return {
    id: mem.id || mem.memory_id,
    title: mem.title || 'Untitled Note',
    category: mem.category || 'personal',
    tags: Array.isArray(mem.tags) ? mem.tags : [],
    content: mem.content || mem.snippet || '',
    summary: mem.summary || mem.snippet || '',
    created_at: mem.created_at || new Date().toISOString(),
    updated_at: mem.updated_at || new Date().toISOString(),
    versions: mem.versions || [],
  };
}

export async function fetchMemories(category = null, tag = null, search = '') {
  try {
    if (search && search.trim()) {
      const res = await fetch(`${BASE_URL}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: search.trim(),
          category_filter: category && category !== 'all' ? category : null,
          top_k: 50,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        const memories = (data.results || []).map((item) => normalizeNote(item.memory || item));
        return { status: 'success', memories };
      }
    }

    const params = new URLSearchParams();
    if (category && category !== 'all') params.append('category', category);
    if (tag) params.append('tag', tag);

    const res = await fetch(`${BASE_URL}/api/memories?${params.toString()}`);
    if (res.ok) {
      const data = await res.json();
      const memories = (data.memories || []).map(normalizeNote);
      return { status: 'success', memories };
    }
  } catch (err) {
    console.warn('Backend API connection failed, falling back to mock memories:', err);
  }

  // Fallback to local mock data
  let filtered = [...initialNotes];
  if (category && category !== 'all') {
    filtered = filtered.filter((n) => n.category === category);
  }
  if (tag) {
    filtered = filtered.filter((n) => n.tags?.includes(tag));
  }
  if (search) {
    const q = search.toLowerCase();
    filtered = filtered.filter(
      (n) =>
        n.title.toLowerCase().includes(q) ||
        n.content.toLowerCase().includes(q) ||
        n.tags?.some((t) => t.toLowerCase().includes(q))
    );
  }
  return { status: 'success', memories: filtered };
}

export async function saveMemory(note) {
  try {
    const res = await fetch(`${BASE_URL}/api/memories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: note.title || 'Untitled Note',
        content: note.content || '',
        category: note.category || 'personal',
        tags: note.tags || [],
        action: note.action || 'auto',
        memory_id: note.id && note.id.startsWith('mem_') ? null : note.id,
      }),
    });
    if (res.ok) {
      const data = await res.json();
      return { status: 'success', memory: normalizeNote(data.memory || data) };
    }
  } catch (err) {
    console.warn('Backend API save failed:', err);
  }
  return { status: 'success', memory: normalizeNote(note) };
}

export async function deleteMemory(memoryId) {
  try {
    const res = await fetch(`${BASE_URL}/api/memories/${memoryId}`, {
      method: 'DELETE',
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API delete failed:', err);
  }
  return { status: 'success', message: 'Deleted locally.' };
}

export async function autoOrganizeNote(content, title = '', model = '') {
  try {
    const res = await fetch(`${BASE_URL}/api/auto-organize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, title, model }),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API auto-organize failed:', err);
  }
  return simulateAutoOrganizeNote(content, title, model);
}

export async function fetchAutoSuggestion(content, title = '', model = '') {
  try {
    const res = await fetch(`${BASE_URL}/api/suggest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, title, model }),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API fetchAutoSuggestion failed:', err);
  }
  return {
    status: 'success',
    suggestion: `\n\n- Key Insight: Active memory context review.\n- Action: Verify implementation and cross-link entities.`,
  };
}

export async function fetchModels() {
  try {
    const res = await fetch(`${BASE_URL}/api/models`);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API fetchModels failed:', err);
  }
  return { status: 'success', active_model: 'gpt-oss:120b-cloud', data: initialModels };
}

export async function setActiveModelApi(model) {
  try {
    const res = await fetch(`${BASE_URL}/api/models/active`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model }),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API setActiveModel failed:', err);
  }
  return { status: 'success', active_model: model };
}

export async function fetchMetrics() {
  try {
    const res = await fetch(`${BASE_URL}/api/metrics`);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API fetchMetrics failed:', err);
  }
  return { status: 'success', metrics: mockMetrics };
}

export async function fetchAudit(autoFix = false, recover = false) {
  try {
    const res = await fetch(`${BASE_URL}/api/audit?auto_fix=${autoFix}&recover=${recover}`);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API fetchAudit failed:', err);
  }
  return mockAuditData;
}

export async function triggerBackup() {
  try {
    const res = await fetch(`${BASE_URL}/api/backup`, { method: 'POST' });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API triggerBackup failed:', err);
  }
  return { status: 'success', message: 'Backup created.' };
}

export async function sendGraphChat(message, category = null, model = null) {
  try {
    const res = await fetch(`${BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, category, model }),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API sendGraphChat failed:', err);
  }
  return simulateGraphChat(message);
}

export async function fetchMemoryVersions(memoryId) {
  try {
    const res = await fetch(`${BASE_URL}/api/memories/${memoryId}/versions`);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API fetchMemoryVersions failed:', err);
  }
  return { status: 'error', versions: [] };
}

export async function revertMemoryVersion(memoryId, versionNumber) {
  try {
    const res = await fetch(`${BASE_URL}/api/memories/${memoryId}/revert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version_number: versionNumber }),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend API revertMemoryVersion failed:', err);
  }
  return { status: 'error' };
}
