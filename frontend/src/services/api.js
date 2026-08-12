/**
 * Memorize Frontend Service API Layer
 * Currently operates in Skeleton Mode (using mockData), but structured
 * for seamless swap to FastAPI backend endpoints (/api/memories, /api/models, /api/auto-organize).
 */

import {
  initialNotes,
  initialCategories,
  initialModels,
  mockAuditData,
  mockMetrics,
  simulateAutoOrganizeNote,
} from '../mockData';

const IS_MOCK_MODE = true;

export async function fetchMemories(category, tag, search) {
  if (IS_MOCK_MODE) {
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
  const res = await fetch(`/api/memories?category=${category || ''}&tag=${tag || ''}`);
  return await res.json();
}

export async function autoOrganizeNote(content, title, model) {
  if (IS_MOCK_MODE) {
    // Simulate LLM latency
    await new Promise((resolve) => setTimeout(resolve, 800));
    return simulateAutoOrganizeNote(content, title, model);
  }
  const res = await fetch('/api/auto-organize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, title, model }),
  });
  return await res.json();
}

export async function fetchModels() {
  if (IS_MOCK_MODE) {
    return { status: 'success', data: initialModels };
  }
  const res = await fetch('/api/models');
  return await res.json();
}

export async function fetchMetrics() {
  if (IS_MOCK_MODE) {
    return { status: 'success', metrics: mockMetrics };
  }
  const res = await fetch('/api/metrics');
  return await res.json();
}

export async function fetchAudit() {
  if (IS_MOCK_MODE) {
    return mockAuditData;
  }
  const res = await fetch('/api/audit');
  return await res.json();
}
