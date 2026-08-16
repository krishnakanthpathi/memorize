import {
  AuditSummary,
  CategoryStat,
  ChatMessage,
  CorrelationItem,
  MergeMemoriesRequest,
  MergeMemoriesResponse,
  ModelsResponse,
  Note,
  SearchResult,
  VersionItem,
} from "@/types";

const API_BASE = "/api";

function stripLeadingTitle(content: string, title: string): string {
  if (!content) return "";
  let clean = content.trim();
  if (title && title.trim()) {
    const escapedTitle = title.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`^(?:#+\\s+${escapedTitle}|Title:\\s*${escapedTitle})\\r?\\n*`, 'i');
    if (regex.test(clean)) {
      clean = clean.replace(regex, '').trim();
    }
  }
  return clean;
}

export const api = {
  // Memories
  async getMemories(category?: string, tag?: string): Promise<Note[]> {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (tag) params.append("tag", tag);

    const url = `${API_BASE}/memories${params.toString() ? `?${params.toString()}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed to fetch memories: ${res.statusText}`);
    }
    const data = await res.json();
    const rawMemories = data.memories || [];
    return rawMemories.map((m: any) => {
      const title = m.title || "Untitled Note";
      const content = stripLeadingTitle(m.content || "", title);
      return {
        id: m.id || m.memory_id,
        title,
        content,
        category: m.category || "personal",
        folderId: m.category || "personal",
        tags: Array.isArray(m.tags) ? m.tags : (typeof m.tags === "string" ? JSON.parse(m.tags || "[]") : []),
        keywords: Array.isArray(m.keywords) ? m.keywords : (typeof m.keywords === "string" ? JSON.parse(m.keywords || "[]") : []),
        isPinned: false,
        isFavorite: false,
        createdAt: m.created_at || new Date().toISOString(),
        updatedAt: m.updated_at || new Date().toISOString(),
        file_path: m.file_path,
        snippet: m.snippet,
      };
    });
  },

  async getMemoryDetail(memoryId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/memories/${encodeURIComponent(memoryId)}`);
    if (!res.ok) throw new Error(`Memory detail error: ${res.statusText}`);
    return res.json();
  },

  async saveMemory(data: {
    title: string;
    content: string;
    category?: string;
    tags?: string[];
    action?: string;
    memory_id?: string;
  }): Promise<any> {
    const payload = {
      title: data.title.trim() || "Untitled Note",
      content: data.content || "",
      category: data.category || "personal",
      tags: data.tags || [],
      action: data.action || "auto",
      memory_id: data.memory_id || undefined,
    };
    const res = await fetch(`${API_BASE}/memories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Save failed (${res.status})`);
    }
    return res.json();
  },

  async deleteMemory(memoryId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/memories/${encodeURIComponent(memoryId)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`Delete failed: ${res.statusText}`);
    return res.json();
  },

  // Multi-Memory LLM Merge
  async mergeMemories(data: MergeMemoriesRequest): Promise<MergeMemoriesResponse> {
    const res = await fetch(`${API_BASE}/memories/merge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Merge failed (${res.status})`);
    }
    return res.json();
  },

  async getCorrelatedMemories(memoryId: string, topK: number = 5): Promise<CorrelationItem[]> {
    const res = await fetch(`${API_BASE}/memories/${encodeURIComponent(memoryId)}/correlations?top_k=${topK}`);
    if (!res.ok) throw new Error(`Fetch correlations failed: ${res.statusText}`);
    const data = await res.json();
    return data.correlations || [];
  },

  // Versioning
  async getVersions(memoryId: string): Promise<VersionItem[]> {
    const res = await fetch(`${API_BASE}/memories/${encodeURIComponent(memoryId)}/versions`);
    if (!res.ok) throw new Error(`Fetch versions failed: ${res.statusText}`);
    const data = await res.json();
    return (data.versions || []).map((v: any) => ({
      ...v,
      tags: typeof v.tags === "string" ? JSON.parse(v.tags || "[]") : v.tags || [],
    }));
  },

  async revertVersion(memoryId: string, versionNumber?: number): Promise<any> {
    const res = await fetch(`${API_BASE}/memories/${encodeURIComponent(memoryId)}/revert`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version_number: versionNumber }),
    });
    if (!res.ok) throw new Error(`Revert failed: ${res.statusText}`);
    return res.json();
  },

  // Search
  async searchMemories(query: string, categoryFilter?: string, topK: number = 10): Promise<SearchResult[]> {
    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        category_filter: categoryFilter || null,
        top_k: topK,
      }),
    });
    if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
    const data = await res.json();
    return data.results || [];
  },

  // Chat
  async sendChatMessage(message: string, model?: string, provider?: string): Promise<{
    reply: string;
    tool_executed?: {
      tool: string;
      status: string;
      result?: any;
    };
    memories_used: { id: string; title: string; category: string; score?: number }[];
  }> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, model, provider }),
    });
    if (!res.ok) throw new Error(`Chat request failed: ${res.statusText}`);
    const data = await res.json();
    return {
      reply: data.reply || "",
      tool_executed: data.tool_executed,
      memories_used: data.memories_used || [],
    };
  },

  // Categories
  async getCategories(): Promise<CategoryStat[]> {
    const res = await fetch(`${API_BASE}/categories`);
    if (!res.ok) throw new Error(`Failed to fetch categories: ${res.statusText}`);
    const data = await res.json();
    const cats = data.categories || [];
    if (Array.isArray(cats)) {
      return cats.map((c: any) =>
        typeof c === "string"
          ? { category: c, count: 0 }
          : { category: c.category || "", count: c.count || 0 }
      );
    }
    return Object.entries(cats).map(([category, count]) => ({
      category,
      count: Number(count),
    }));
  },

  // Storage Audit
  async getAuditSummary(): Promise<AuditSummary> {
    const res = await fetch(`${API_BASE}/audit/summary`);
    if (!res.ok) throw new Error(`Audit failed: ${res.statusText}`);
    const data = await res.json();
    const summary = data.summary || {};
    const details = data.details || {};

    return {
      status: data.status || "success",
      auto_fixed: data.auto_fix_applied,
      total_db_records: data.total_db_records ?? (details.orphan_indexes ? details.orphan_indexes.length : 0) + (data.total_memories || 1),
      total_files: data.total_files ?? (details.orphan_files ? details.orphan_files.length : 0) + (data.total_memories || 1),
      total_vector_chunks: data.total_vector_chunks ?? (details.orphan_chunks ? details.orphan_chunks.length : 0),
      orphan_files_count: summary.orphan_files_count ?? (details.orphan_files ? details.orphan_files.length : 0),
      orphan_indexes_count: summary.orphan_indexes_count ?? (details.orphan_indexes ? details.orphan_indexes.length : 0),
      orphan_chunks_count: summary.orphan_chunks_count ?? (details.orphan_chunks ? details.orphan_chunks.length : 0),
      orphan_files: (details.orphan_files || []).map((f: any) => typeof f === "string" ? f : f.file_name || f.file_path),
      orphan_indexes: (details.orphan_indexes || []).map((i: any) => typeof i === "string" ? i : i.title || i.memory_id),
      orphan_chunks: (details.orphan_chunks || []).map((c: any) => typeof c === "string" ? c : c.id || JSON.stringify(c)),
    };
  },

  async runAuditFix(): Promise<AuditSummary> {
    const res = await fetch(`${API_BASE}/audit/summary`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ auto_fix: true }),
    });
    if (!res.ok) throw new Error(`Audit auto-fix failed: ${res.statusText}`);
    return this.getAuditSummary();
  },

  async deleteOrphans(type: "files" | "indexes" | "chunks"): Promise<any> {
    const res = await fetch(`${API_BASE}/audit/orphan-${type}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`Delete orphan ${type} failed: ${res.statusText}`);
    return res.json();
  },

  async recoverOrphans(): Promise<any> {
    const res = await fetch(`${API_BASE}/audit/recover`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`Recover orphans failed: ${res.statusText}`);
    return res.json();
  },

  // Backup & Purge
  async getBackupInfo(): Promise<{ status: string; readme_text: string }> {
    const res = await fetch(`${API_BASE}/backup`);
    if (!res.ok) throw new Error(`Fetch backup info failed: ${res.statusText}`);
    return res.json();
  },

  async createBackup(): Promise<any> {
    const res = await fetch(`${API_BASE}/backup`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`Backup trigger failed: ${res.statusText}`);
    return res.json();
  },

  async purgeAllMemories(): Promise<any> {
    const res = await fetch(`${API_BASE}/purge`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`Purge memories failed: ${res.statusText}`);
    return res.json();
  },

  // Models
  async getModels(provider?: string, baseUrl?: string, apiKey?: string): Promise<ModelsResponse> {
    const params = new URLSearchParams();
    if (provider) params.append("provider", provider);
    if (baseUrl) params.append("base_url", baseUrl);
    if (apiKey) params.append("api_key", apiKey);

    const url = `${API_BASE}/models${params.toString() ? `?${params.toString()}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Fetch models failed: ${res.statusText}`);
    const data = await res.json();
    return {
      status: data.status || "success",
      selected_provider: data.selected_provider,
      providers: data.providers,
      fast_models: Array.isArray(data.fast_models) ? data.fast_models : [],
      reasoning_models: Array.isArray(data.reasoning_models) ? data.reasoning_models : [],
      all_models: Array.isArray(data.all_models) ? data.all_models : [],
      generative_models: Array.isArray(data.generative_models) ? data.generative_models : [],
      embedding_models: Array.isArray(data.embedding_models) ? data.embedding_models : [],
      current_default: data.current_default || (data.fast_models && data.fast_models[0]) || (data.all_models && data.all_models[0]) || "",
      total_count: data.total_count || (data.all_models ? data.all_models.length : 0),
    };
  },

  // Configuration & Settings
  async getSettings(): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error(`Fetch settings failed: ${res.statusText}`);
    const data = await res.json();
    return data.settings || {};
  },

  async updateSettings(settings: Record<string, any>): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error(`Update settings failed: ${res.statusText}`);
    const data = await res.json();
    return data.settings || {};
  },
};


