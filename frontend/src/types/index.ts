export type ThemeMode = 'light' | 'dark' | 'black';

export type CodeTheme =
  | 'monokai'
  | 'monokai-fire'
  | 'monokai-solenoid'
  | 'vscode-dark'
  | 'github-dark'
  | 'dracula'
  | 'tokyo-night'
  | 'nord';

export type AppIconType = 'monogram' | 'brain' | 'terminal' | 'book' | 'zap' | 'database' | 'sparkles';

export type SystemView = 'all' | 'favorites' | 'pinned' | 'trash' | 'recent' | 'settings' | 'docs';

export interface Note {
  id: string;
  title: string;
  content: string; // Raw markdown text
  folderId: string | null;
  category: string;
  tags: string[];
  keywords?: string[];
  isPinned: boolean;
  isFavorite: boolean;
  isDeleted?: boolean;
  createdAt: string; // ISO string
  updatedAt: string; // ISO string
  file_path?: string;
  snippet?: string;
}

export interface Folder {
  id: string;
  name: string;
  icon?: string;
  count?: number;
}

export interface CategoryStat {
  category: string;
  count: number;
}

export interface VersionItem {
  id: number;
  memory_id: string;
  version_number: number;
  title: string;
  category: string;
  tags: string[] | string;
  content: string;
  content_hash?: string;
  created_at: string;
}

export interface SearchResult {
  id: string;
  title: string;
  category: string;
  file_path?: string;
  score?: number;
  final_score?: number;
  vector_score?: number;
  text_score?: number;
  snippet?: string;
  content?: string;
  tags?: string[];
}

export interface AuditSummary {
  status: string;
  auto_fixed?: boolean;
  total_db_records: number;
  total_files: number;
  total_vector_chunks: number;
  orphan_files_count: number;
  orphan_indexes_count: number;
  orphan_chunks_count: number;
  orphan_files?: string[];
  orphan_indexes?: string[];
  orphan_chunks?: string[];
  action_summary?: {
    reconciled_files?: number;
    cleaned_indexes?: number;
    cleaned_chunks?: number;
  };
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolExecuted?: {
    tool: string;
    status: string;
    result?: any;
  };
  memoriesUsed?: {
    id: string;
    title: string;
    category: string;
    score?: number;
  }[];
  timestamp: string;
  model?: string;
}

export interface ModelOption {
  id: string;
  name?: string;
  description?: string;
}

export interface ProviderModelInfo {
  name: string;
  available: boolean;
  base_url: string;
  total_count: number;
  fast_models: string[];
  reasoning_models: string[];
  generative_models?: any[];
  embedding_models?: any[];
  all_models: string[];
  current_default?: string;
}

export interface ModelsResponse {
  status: string;
  selected_provider?: string;
  providers?: {
    ollama?: ProviderModelInfo;
    openai?: ProviderModelInfo;
    [key: string]: ProviderModelInfo | undefined;
  };
  fast_models: string[];
  reasoning_models: string[];
  all_models: string[];
  generative_models?: { id: string; object?: string; owned_by?: string; status?: string }[];
  embedding_models?: { id: string; object?: string; owned_by?: string; status?: string }[];
  current_default?: string;
  total_count?: number;
}

export interface MergeMemoriesRequest {
  memory_ids: string[];
  target_title?: string;
  target_category?: string;
  target_tags?: string[];
  delete_sources?: boolean;
  instruction?: string;
  use_ai?: boolean;
}

export interface MergeMemoriesResponse {
  status: string;
  action: string;
  merged_memory_id: string;
  title: string;
  category: string;
  tags: string[];
  file_path: string;
  chunk_count: number;
  merged_source_count: number;
  deleted_source_ids: string[];
  content_preview: string;
}

export interface MemoryOrganizeRequest {
  instruction?: string;
  use_ai?: boolean;
  generate_title?: boolean;
}

export interface MemoryOrganizeResponse {
  status: string;
  action: string;
  memory_id: string;
  title: string;
  category: string;
  tags: string[];
  file_path: string;
  chunk_count: number;
  content: string;
  content_preview: string;
}

export interface GenerateTitleRequest {
  content: string;
  current_title?: string;
  instruction?: string;
  memory_id?: string;
  save_to_memory?: boolean;
}

export interface GenerateTitleResponse {
  status: string;
  title: string;
  memory_id?: string;
}

export interface TextTransformRequest {
  selected_text: string;
  instruction?: string;
  mode?: 'polish' | 'summarize' | 'technical' | 'simplify' | 'expand' | 'title' | string;
  full_context?: string;
}

export interface TextTransformResponse {
  status: string;
  action: string;
  mode: string;
  transformed_text: string;
  title?: string;
}

export interface CorrelationItem {
  id: string;
  title: string;
  category: string;
  tags: string[];
  shared_tags: string[];
  same_category: boolean;
  similarity_score: number;
  similarity_percent: number;
  snippet: string;
}
