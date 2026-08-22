import {
  AuditSummary,
  AutoTagRequest,
  AutoTagResponse,
  CategoryStat,
  CorrelationItem,
  GenerateTitleResponse,
  MediaItem,
  MediaOcrResponse,
  MediaUploadResponse,
  MemoryOrganizeResponse,
  MergeMemoriesRequest,
  MergeMemoriesResponse,
  ModelsResponse,
  Note,
  PromptsMap,
  SearchResult,
  TextTransformResponse,
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

  async deleteBatchMemories(memoryIds: string[]): Promise<any> {
    const res = await fetch(`${API_BASE}/memories/batch-delete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ memory_ids: memoryIds }),
    });
    if (!res.ok) throw new Error(`Batch delete failed: ${res.statusText}`);
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

  // Single-Memory AI Organize & Restructure
  async organizeMemory(
    memoryId: string,
    instruction?: string,
    useAi: boolean = true,
    generateTitle: boolean = false
  ): Promise<MemoryOrganizeResponse> {
    const res = await fetch(`${API_BASE}/memories/${encodeURIComponent(memoryId)}/organize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instruction, use_ai: useAi, generate_title: generateTitle }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Organize failed (${res.status})`);
    }
    return res.json();
  },

  // Note Title Generation
  async generateTitle(
    content: string,
    currentTitle?: string,
    instruction?: string,
    memoryId?: string,
    saveToMemory: boolean = false
  ): Promise<GenerateTitleResponse> {
    const res = await fetch(`${API_BASE}/memories/generate-title`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content,
        current_title: currentTitle,
        instruction,
        memory_id: memoryId,
        save_to_memory: saveToMemory,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Title generation failed (${res.status})`);
    }
    return res.json();
  },

  // Selected Text / Paragraph Organizer
  async transformSelection(
    selectedText: string,
    instruction?: string,
    mode: string = "polish",
    fullContext?: string
  ): Promise<TextTransformResponse> {
    const res = await fetch(`${API_BASE}/memories/transform-selection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        selected_text: selectedText,
        instruction,
        mode,
        full_context: fullContext,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Selection transform failed (${res.status})`);
    }
    return res.json();
  },

  // Auto LLM Tagging & Classification
  async autoTagNote(data: AutoTagRequest): Promise<AutoTagResponse> {
    const res = await fetch(`${API_BASE}/memories/auto-tag`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Auto-tagging failed (${res.status})`);
    }
    return res.json();
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

  // Test LLM Connection
  async testLlmConnection(model?: string, provider?: string, baseUrl?: string): Promise<{
    status: string;
    provider: string;
    model: string;
    reply?: string;
    error?: string;
  }> {
    const res = await fetch(`${API_BASE}/settings/test-llm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model, provider, base_url: baseUrl }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `LLM test failed: ${res.statusText}`);
    }
    return await res.json();
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
      orphan_media_count: summary.orphan_media_count ?? (details.orphan_media ? details.orphan_media.length : 0),
      orphan_files: (details.orphan_files || []).map((f: any) => typeof f === "string" ? f : f.file_name || f.file_path),
      orphan_indexes: (details.orphan_indexes || []).map((i: any) => typeof i === "string" ? i : i.title || i.memory_id),
      orphan_chunks: (details.orphan_chunks || []).map((c: any) => typeof c === "string" ? c : c.id || JSON.stringify(c)),
      orphan_media: details.orphan_media || [],
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

  async getStoragePaths(): Promise<{
    status: string;
    memories_dir: string;
    storage_layout: string;
    default_memories_dir: string;
    media_dir: string;
    db_path: string;
    validation: {
      valid: boolean;
      resolved_path?: string;
      total_bytes?: number;
      used_bytes?: number;
      free_bytes?: number;
      free_gb?: number;
      error?: string;
    };
    total_memories: number;
    total_media: number;
  }> {
    const res = await fetch(`${API_BASE}/settings/storage-paths`);
    if (!res.ok) throw new Error(`Fetch storage paths failed: ${res.statusText}`);
    return res.json();
  },

  async updateStoragePaths(payload: {
    memories_dir?: string;
    storage_layout?: string;
    migrate_existing?: boolean;
  }): Promise<any> {
    const res = await fetch(`${API_BASE}/settings/storage-paths`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Update storage paths failed (${res.status})`);
    }
    return res.json();
  },

  async migrateStorageLayout(payload: {
    storage_layout?: string;
    reclassify?: boolean;
  } = {}): Promise<any> {
    const res = await fetch(`${API_BASE}/settings/migrate-storage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Storage migration failed (${res.status})`);
    }
    return res.json();
  },

  // AI Prompt Templates Registry
  async getPrompts(): Promise<PromptsMap> {
    try {
      const res = await fetch(`${API_BASE}/settings/prompts`);
      if (res.ok) {
        const data = await res.json();
        if (data.prompts && Object.keys(data.prompts).length > 0) {
          return data.prompts;
        }
      }
    } catch (e) {
      console.warn("Using static prompt registry fallback:", e);
    }
    // Fallback static prompt registry
    return {
      smart_merge: {
        name: "Smart Memory Merge Prompt",
        description: "Used when updating existing memories to intelligently blend new details with existing content.",
        template: `You are an expert AI memory manager. Your task is to intelligently merge new information or edits into an existing Markdown memory document.\n\nRules:\n1. Preserve unchanged context, facts, and structure from the existing memory.\n2. Replace outdated or superseded details with the new facts.\n3. Seamlessly integrate new details into relevant existing sections or add new logical section headers if needed.\n4. Do NOT naively append '### Update' sections at the bottom unless it represents a distinct timeline event.\n5. Do NOT include conversation preambles, intros, or markdown block ticks (e.g. \`\`\`markdown ... \`\`\`).\n6. Output ONLY the complete, cleanly updated Markdown content body.`,
      },
      multi_merge: {
        name: "Multi-Memory Merge Prompt",
        description: "Used when consolidating multiple related memory notes into a unified knowledge document.",
        template: `You are an expert AI knowledge curator and technical editor.\nYour task is to merge multiple related Markdown memory notes into a single, cohesive, authoritative, well-structured, and non-redundant document.\n\nCore Merge Guidelines:\n1. Synthesize all unique insights, code snippets, mathematical formulas ($...$, $$...$$), technical details, configurations, and key facts.\n2. Eliminate redundancies, repeated explanations, and duplicate headings.\n3. Structure the consolidated document with clear, logical Markdown hierarchies (# Document Title, ## Major Sections, ### Subsections, bullet points, tables where helpful).\n4. Maintain a professional, clean Markdown style without conversation preambles, introductory filler, or code fence wrappers around the entire document.\n5. If custom merge instructions are provided below, prioritize them.\n6. Output ONLY the unified Markdown content body.`,
      },
      organize: {
        name: "Single Memory AI Organizer Prompt",
        description: "Used to polish, restructure, clean up, or summarize individual memory notes.",
        template: `You are an expert AI technical editor and document architect.\nYour task is to take an existing Markdown memory note and polish, restructure, and organize it for maximum clarity, readability, and precision.\n\nGuidelines:\n1. Preserve all factual information, code snippets, mathematical formulas ($...$, $$...$$), and specific technical values. Do NOT invent new facts.\n2. Structure the document with clear, logical Markdown hierarchies (# Document Title, ## Major Sections, ### Subsections, bullet points, key takeaways, tables where applicable).\n3. Fix messy formatting, inconsistent indentation, grammatical errors, and typos.\n4. Remove redundant conversational fluff and repeated phrasing.\n5. If custom instructions or goals are specified below, prioritize them.\n6. Output ONLY the polished, cleanly formatted Markdown content body.`,
      },
      generate_title: {
        name: "Note Title Generation Prompt",
        description: "Used to generate concise, high-signal, descriptive titles for notes and excerpts.",
        template: `You are an expert AI editor and document architect.\nYour task is to generate a clear, concise, descriptive, and high-signal title (3 to 7 words) for the provided Markdown note content or excerpt.\n\nRules:\n1. Do NOT enclose the title in quotes, backticks, or markdown bold/italics.\n2. Do NOT add prefixes like "Title:", "Note:", or "Summary:".\n3. Capture the core subject, entity, technical topic, or intent accurately.\n4. Return ONLY the title text on a single line.`,
      },
      organize_selection: {
        name: "Selected Paragraph / Text Organizer Prompt",
        description: "Used to polish, summarize, or transform selected paragraphs and text excerpts.",
        template: `You are an expert AI text editor and writing assistant.\nYour task is to rewrite, organize, or transform the user's selected text snippet or paragraph according to their requested goal.\n\nGuidelines:\n1. Maintain context, accurate terminology, and technical fidelity ($...$, $$...$$, code syntax, and key parameters).\n2. Output ONLY the replacement text for the selected passage.\n3. Do NOT include conversational introductory preambles or wrap the entire output in markdown code fences.\n4. Ensure clean, elegant formatting matching standard Markdown.`,
      },
      auto_classify: {
        name: "Auto-Classification & Tagging Prompt",
        description: "Classifies documents into categories and extracts relevant tags.",
        template: `You are an expert AI memory classifier. Analyze the provided text and determine the single best category and 3-5 concise tags.\nYou MUST choose the category strictly from the provided list of available categories.\nDo NOT invent or modify category names.\n\nReturn ONLY valid JSON matching this exact structure:\n{\n  "category": "one_of_allowed_categories",\n  "tags": ["tag1", "tag2", "tag3"],\n  "confidence": 0.95\n}`,
      },
      summary: {
        name: "Executive Summary Prompt",
        description: "Generates concise 2-3 sentence summaries for search snippets and previews.",
        template: `You are a concise summarizer. Generate a clear 2-3 sentence executive summary of the provided text.\nPreserve key technical terms, dates, metrics, and actionable takeaways. Output ONLY the summary text.`,
      },
    };
  },

  // Uncompressed Original Media & Local Ollama GLM-OCR
  async uploadMedia(
    file: File | Blob,
    filename?: string,
    memoryId?: string,
    runOcr: boolean = true,
    customPrompt?: string,
    signal?: AbortSignal
  ): Promise<MediaUploadResponse> {
    const formData = new FormData();
    formData.append("file", file, filename || (file instanceof File ? file.name : "image.png"));
    if (filename) formData.append("filename", filename);
    if (memoryId) formData.append("memory_id", memoryId);
    formData.append("run_ocr", String(runOcr));
    if (customPrompt) formData.append("custom_prompt", customPrompt);

    const res = await fetch(`${API_BASE}/media/upload`, {
      method: "POST",
      body: formData,
      signal,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Media upload failed: ${res.statusText}`);
    }
    return res.json();
  },

  async uploadMediaFromDataUrl(
    dataUrl: string,
    filename?: string,
    memoryId?: string,
    runOcr: boolean = true,
    customPrompt?: string
  ): Promise<MediaUploadResponse> {
    const formData = new FormData();
    formData.append("data_url", dataUrl);
    if (filename) formData.append("filename", filename);
    if (memoryId) formData.append("memory_id", memoryId);
    formData.append("run_ocr", String(runOcr));
    if (customPrompt) formData.append("custom_prompt", customPrompt);

    const res = await fetch(`${API_BASE}/media/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Media upload failed: ${res.statusText}`);
    }
    return res.json();
  },

  async uploadMediaFromUrl(
    imageUrl: string,
    memoryId?: string,
    runOcr: boolean = true,
    customPrompt?: string
  ): Promise<MediaUploadResponse> {
    const formData = new FormData();
    formData.append("image_url", imageUrl);
    if (memoryId) formData.append("memory_id", memoryId);
    formData.append("run_ocr", String(runOcr));
    if (customPrompt) formData.append("custom_prompt", customPrompt);

    const res = await fetch(`${API_BASE}/media/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Media upload failed: ${res.statusText}`);
    }
    return res.json();
  },

  async getMediaItem(mediaId: string): Promise<{ status: string; media: MediaItem }> {
    const res = await fetch(`${API_BASE}/media/item/${encodeURIComponent(mediaId)}`);
    if (!res.ok) throw new Error(`Fetch media item failed: ${res.statusText}`);
    return res.json();
  },

  async triggerMediaOcr(mediaId: string, customPrompt?: string): Promise<MediaOcrResponse> {
    const res = await fetch(`${API_BASE}/media/${encodeURIComponent(mediaId)}/ocr`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: customPrompt }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `OCR execution failed: ${res.statusText}`);
    }
    return res.json();
  },

  async listMedia(): Promise<{ status: string; total: number; media: MediaItem[] }> {
    const res = await fetch(`${API_BASE}/media/list`);
    if (!res.ok) throw new Error(`List media failed: ${res.statusText}`);
    return res.json();
  },

  async deleteMedia(mediaId: string): Promise<{ status: string; media_id: string; deleted: boolean }> {
    const res = await fetch(`${API_BASE}/media/${encodeURIComponent(mediaId)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`Delete media failed: ${res.statusText}`);
    return res.json();
  },
};




