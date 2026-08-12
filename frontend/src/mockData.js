export const initialCategories = [
  { id: 'all', name: 'All Notes', count: 4 },
  { id: 'technology', name: 'Technology', count: 2 },
  { id: 'research', name: 'Research', count: 1 },
  { id: 'personal', name: 'Personal', count: 1 },
];

export const initialModels = {
  active_model: 'gpt-4o-mini',
  active_engine: 'langgraph',
  generative_models: [
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini (OpenAI)', provider: 'openai', status: 'active' },
    { id: 'gpt-4o', name: 'GPT-4o (OpenAI)', provider: 'openai', status: 'available' },
    { id: 'mistral:7b-ollama', name: 'Mistral 7B (Ollama Local)', provider: 'ollama', status: 'available' },
    { id: 'llama3:70b-ollama', name: 'Llama 3 70B (Ollama Local)', provider: 'ollama', status: 'available' },
    { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet (Anthropic)', provider: 'anthropic', status: 'available' },
  ],
  embedding_models: [
    { id: 'text-embedding-3-small', name: 'Text Embedding 3 Small (1536d)' },
    { id: 'nomic-embed-text', name: 'Nomic Embed Text (Ollama Local)' },
  ],
};

export const initialNotes = [
  {
    id: 'mem_01h8x9a2k1',
    title: 'Neural Network Pruning & Compression',
    category: 'technology',
    tags: ['ai', 'neural_networks', 'optimization', 'deep_learning'],
    summary: 'Techniques for structured and unstructured weight pruning in transformer models to reduce memory footprint.',
    content: `# Neural Network Pruning & Compression\n\nPruning involves eliminating non-essential weights in deep neural networks to lower memory usage and speed up inference latency without significant accuracy drop.\n\n### Key Methods:\n1. **Magnitude Pruning**: Zeroing out weights below a specified absolute threshold.\n2. **Structured Pruning**: Removing entire channels or filter blocks for direct GPU speedups.\n3. **Quantization Aware Training (QAT)**: Simulating INT8 precision during training.`,
    updated_at: '2026-08-12T19:20:00Z',
    content_hash: 'a1b2c3d4e5f6',
    versions: [
      { version_number: 1, created_at: '2026-08-10T14:00:00Z', summary: 'Initial draft on pruning methods.' },
      { version_number: 2, created_at: '2026-08-12T19:20:00Z', summary: 'Added Quantization Aware Training section.' },
    ]
  },
  {
    id: 'mem_02j9y0b3m2',
    title: 'GraphRAG Companion & Workflow Architecture',
    category: 'architecture',
    tags: ['graphrag', 'langgraph', 'vector_db', 'fastapi'],
    summary: 'Multi-hop entity linking pipeline integrating ChromaDB hybrid retrieval with LangGraph workflows.',
    content: `# GraphRAG Companion Architecture\n\nThe Memorize GraphRAG workflow connects unstructured Markdown memories with structured graph entity extraction.\n\n### Core Execution Pipeline:\n- **Intent Classification**: Evaluates user query (Search vs Mutate vs Summarize).\n- **Hybrid Search**: Combines keyword search with dense ChromaDB vectors.\n- **Entity Linking**: Extracts relationships between notes dynamically.\n- **LLM Synthesis**: Uses selected active LLM model to construct answer with citations.`,
    updated_at: '2026-08-11T16:45:00Z',
    content_hash: 'f6e5d4c3b2a1',
    versions: [
      { version_number: 1, created_at: '2026-08-11T16:45:00Z', summary: 'Architectural overview.' },
    ]
  },
  {
    id: 'mem_03k0z1c4n3',
    title: 'Three-Way Storage Synchronization System',
    category: 'research',
    tags: ['sqlite', 'chromadb', 'markdown', 'sync'],
    summary: 'Audit mechanism enforcing zero drift across local Markdown files, SQLite indexes, and vector stores.',
    content: `# Three-Way Storage Synchronization\n\nTo ensure total memory integrity, Memorize maintains high-speed consistency across three layers:\n1. **Markdown Files on Disk**: Human-readable source of truth.\n2. **SQLite Index**: Relational index for fast category, tag, and date queries.\n3. **ChromaDB Vector Store**: Dense embedding chunks for semantic vector lookup.`,
    updated_at: '2026-08-09T11:10:00Z',
    content_hash: '9876543210ab',
    versions: [
      { version_number: 1, created_at: '2026-08-09T11:10:00Z', summary: 'Storage specification.' },
    ]
  },
  {
    id: 'mem_04l1a2d5o4',
    title: 'Weekly Standup Notes & Ideas',
    category: 'personal',
    tags: ['notes', 'standup', 'planning'],
    summary: 'Internal team action items: UI skeleton buildout, LLM client provider updates, and testing guide.',
    content: `# Weekly Standup Notes\n\n- [x] Complete backend 3-way audit API.\n- [ ] Design sleek monochrome Apple/Google Notes UI skeleton.\n- [ ] Integrate Lucide brain icon with hollow/filled toggle.\n- [ ] Connect LLM auto-organize endpoint.`,
    updated_at: '2026-08-08T09:30:00Z',
    content_hash: '112233445566',
    versions: [
      { version_number: 1, created_at: '2026-08-08T09:30:00Z', summary: 'Standup list.' },
    ]
  }
];

export const mockAuditData = {
  status: 'healthy',
  timestamp: '2026-08-12T19:50:00Z',
  markdown_files_count: 4,
  sqlite_records_count: 4,
  chromadb_chunks_count: 18,
  integrity_drift: false,
  message: 'All 3 storage layers (Markdown, SQLite, ChromaDB) are 100% in sync.'
};

export const mockMetrics = {
  total_memories: 4,
  total_tokens_processed: 18450,
  avg_llm_latency_ms: 312.4,
  vector_search_latency_ms: 18.2,
  active_llm_provider: 'OpenAI (gpt-4o-mini)',
  active_embedding_model: 'text-embedding-3-small',
};

// Simulation helper for LLM Auto-Organize
export function simulateAutoOrganizeNote(content, currentTitle = '', activeModel = 'gpt-4o-mini') {
  const cleanContent = content.trim();
  if (!cleanContent) {
    return {
      status: 'error',
      message: 'Content cannot be empty.'
    };
  }

  const firstLine = cleanContent.split('\n')[0].replace(/^#+\s*/, '').trim();
  const title = currentTitle && currentTitle !== 'Untitled Note' 
    ? currentTitle 
    : (firstLine.slice(0, 40) || 'Auto-Organized Note');

  const wordList = cleanContent.toLowerCase().match(/\b[a-z]{4,}\b/g) || [];
  const freqMap = {};
  wordList.forEach(w => {
    if (!['with', 'that', 'this', 'from', 'have', 'your', 'about', 'note'].includes(w)) {
      freqMap[w] = (freqMap[w] || 0) + 1;
    }
  });
  const tags = Object.keys(freqMap).sort((a, b) => freqMap[b] - freqMap[a]).slice(0, 4);
  if (tags.length === 0) tags.push('general', 'notes');

  let category = 'personal';
  if (cleanContent.toLowerCase().includes('neural') || cleanContent.toLowerCase().includes('ai') || cleanContent.toLowerCase().includes('code')) {
    category = 'technology';
  } else if (cleanContent.toLowerCase().includes('sync') || cleanContent.toLowerCase().includes('arch') || cleanContent.toLowerCase().includes('db')) {
    category = 'architecture';
  } else if (cleanContent.toLowerCase().includes('audit') || cleanContent.toLowerCase().includes('research')) {
    category = 'research';
  }

  const summary = `Executive summary generated by ${activeModel}: "${cleanContent.slice(0, 110)}..."`;
  const organizedContent = `# ${title}\n\n${cleanContent}\n\n--- \n*Auto-formatted and summarized via ${activeModel} engine.*`;

  return {
    status: 'success',
    title,
    category,
    tags,
    summary,
    organized_content: organizedContent
  };
}

// Simulation helper for LLM Smart Merge & Memory Modification
export function simulateSmartMergeNote(content, existingNote, activeModel = 'gpt-4o-mini') {
  const title = existingNote?.title || 'Merged Memory Note';
  const category = existingNote?.category || 'personal';
  const existingTags = existingNote?.tags || ['memory'];
  const mergedTags = Array.from(new Set([...existingTags, 'llm_merged']));
  const summary = `Contextual memory merge generated by ${activeModel} engine.`;
  const mergedContent = `# ${title}\n\n${content}\n\n--- \n*Contextual LLM memory update merged via ${activeModel}.*`;

  return {
    status: 'success',
    title,
    category,
    tags: mergedTags,
    summary,
    organized_content: mergedContent
  };
}

export function simulateGraphChat(query) {
  return {
    status: 'success',
    message: query,
    reply: `I searched across your active memories using hybrid semantic search and LangGraph reasoning.\n\nBased on your query **"${query}"**, I found relevant insights in *Neural Network Pruning* and *GraphRAG Architecture*. Would you like me to synthesize a detailed summary or save a new memory topic?`,
    entities: ['Pruning', 'GraphRAG', 'ChromaDB'],
    latency_ms: 245.8,
  };
}
