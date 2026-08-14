import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  ArrowLeft,
  Search,
  Code,
  Layers,
  Sparkles,
  Bot,
  Terminal,
  ShieldCheck,
  Zap,
  HardDrive,
  Copy,
  Check,
  FileCode,
  Sliders,
  Keyboard,
  ExternalLink,
  Database,
  Folder,
} from 'lucide-react';

import { useNotesStore } from '@/store/useNotesStore';
import { cn } from '@/lib/utils';

type DocSection = 'overview' | 'markdown' | 'api' | 'mcp' | 'shortcuts' | 'architecture';

export const DocsPanel: React.FC = () => {
  const { setActiveView } = useNotesStore();
  const [activeSection, setActiveSection] = useState<DocSection>('overview');
  const [copiedText, setCopiedText] = useState<string | null>(null);

  // Press Escape to exit docs back to notes
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        setActiveView('all');
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [setActiveView]);

  const copyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedText(id);
    setTimeout(() => setCopiedText(null), 2000);
  };

  const navItems: { id: DocSection; label: string; icon: React.FC<{ className?: string }> }[] = [
    { id: 'overview', label: 'Overview & Features', icon: Sparkles },
    { id: 'markdown', label: 'Markdown Syntax Guide', icon: FileCode },
    { id: 'api', label: 'REST API Reference', icon: Terminal },
    { id: 'mcp', label: 'MCP Tools Ecosystem', icon: Bot },
    { id: 'shortcuts', label: 'Keyboard Shortcuts', icon: Keyboard },
    { id: 'architecture', label: 'Storage & Architecture', icon: Layers },
  ];

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-background text-foreground animate-in fade-in duration-150 select-none">
      {/* Header Bar */}
      <header className="h-14 px-6 border-b border-border flex items-center justify-between gap-4 shrink-0 bg-surface-sidebar">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-foreground text-background font-bold text-xs">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold leading-tight">Memorize System Documentation</h2>
            <p className="text-[11px] text-muted-foreground font-mono">
              Complete guide for Markdown, REST APIs, MCP Tools, and Architecture
            </p>
          </div>
        </div>

        {/* Back / Done Button */}
        <button
          onClick={() => setActiveView('all')}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-foreground text-background text-xs font-semibold hover:opacity-90 transition-opacity shadow-xs"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Notes</span>
          <kbd className="px-1.5 py-0.5 rounded bg-background/20 font-mono text-[10px]">Esc</kbd>
        </button>
      </header>

      {/* Main Body with Left Nav & Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Navigation Sidebar */}
        <nav className="w-64 border-r border-border bg-surface-sidebar p-3 space-y-1 overflow-y-auto shrink-0 select-none">
          <div className="px-3 py-2 text-[10px] uppercase font-bold text-muted-foreground tracking-wider">
            Documentation Index
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={cn(
                  'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all text-left',
                  isActive
                    ? 'bg-surface-selected text-foreground font-semibold shadow-xs'
                    : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
                )}
              >
                <Icon className={cn('w-4 h-4', isActive ? 'text-foreground' : 'text-muted-foreground')} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Content Viewer */}
        <main className="flex-1 overflow-y-auto p-8 sm:p-12 max-w-4xl mx-auto space-y-8 select-text">
          {/* SECTION 1: OVERVIEW */}
          {activeSection === 'overview' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-bold tracking-tight mb-2">Welcome to Memorize</h1>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Memorize is an ultra-fast, local-first note-taking and knowledge engine with a strict monochrome Apple Notes-inspired interface, powered by hybrid vector search, dual WYSIWYG & Raw Markdown editing, and automated AI companion tool invocation.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl border border-border bg-surface-hover/50 space-y-1.5">
                  <div className="flex items-center gap-2 font-bold text-xs text-foreground">
                    <ShieldCheck className="w-4 h-4 text-emerald-500" />
                    <span>Local-First Privacy</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    All notes exist as plain Markdown files in <code>data/memories</code> with full SQLite database indexing.
                  </p>
                </div>

                <div className="p-4 rounded-xl border border-border bg-surface-hover/50 space-y-1.5">
                  <div className="flex items-center gap-2 font-bold text-xs text-foreground">
                    <Search className="w-4 h-4 text-foreground" />
                    <span>Hybrid RAG Search</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Combines exact BM25 keyword matching with ChromaDB vector embeddings for instant recall.
                  </p>
                </div>

                <div className="p-4 rounded-xl border border-border bg-surface-hover/50 space-y-1.5">
                  <div className="flex items-center gap-2 font-bold text-xs text-foreground">
                    <Bot className="w-4 h-4 text-foreground" />
                    <span>Tool-Enabled AI</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    AI Companion can directly create, search, summarize, and manage memories through tool calls.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 2: MARKDOWN GUIDE */}
          {activeSection === 'markdown' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-bold tracking-tight mb-2">Markdown Syntax Reference</h1>
                <p className="text-sm text-muted-foreground">
                  Memorize fully supports CommonMark, GFM (GitHub Flavored Markdown), task lists, tables, and code syntax highlighting.
                </p>
              </div>

              <div className="space-y-4">
                <div className="p-4 rounded-xl border border-border bg-surface-hover/30 space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">Headers & Emphasis</h3>
                  <pre className="p-3 bg-surface-hover rounded-lg font-mono text-xs overflow-x-auto text-foreground">
{`# Heading 1
## Heading 2
### Heading 3

**Bold Text**, *Italic Text*, ~~Strikethrough~~, \`inline code\``}
                  </pre>
                </div>

                <div className="p-4 rounded-xl border border-border bg-surface-hover/30 space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">Task Lists & Lists</h3>
                  <pre className="p-3 bg-surface-hover rounded-lg font-mono text-xs overflow-x-auto text-foreground">
{`- [x] Finished memory indexing
- [ ] Implement new model selector
- Standard bullet item 1
  - Nested item 1.1`}
                  </pre>
                </div>

                <div className="p-4 rounded-xl border border-border bg-surface-hover/30 space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">Code Blocks with Language Tagging</h3>
                  <pre className="p-3 bg-surface-hover rounded-lg font-mono text-xs overflow-x-auto text-foreground">
{`\`\`\`python
def memorize(title: str, content: str):
    return api.save_memory(title=title, content=content)
\`\`\``}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 3: REST API REFERENCE */}
          {activeSection === 'api' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-bold tracking-tight mb-2">FastAPI REST Endpoints</h1>
                <p className="text-sm text-muted-foreground font-mono">
                  Base URL: <code>http://localhost:6999/api</code>
                </p>
              </div>

              <div className="space-y-4">
                {[
                  {
                    method: 'GET',
                    path: '/api/memories',
                    desc: 'Fetch all active notes, with optional category/tag filtering',
                    sample: 'curl http://localhost:6999/api/memories',
                  },
                  {
                    method: 'POST',
                    path: '/api/memories',
                    desc: 'Create or overwrite a note memory in SQLite, ChromaDB, and Markdown file',
                    sample: `curl -X POST http://localhost:6999/api/memories \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Note Title", "content": "# Content", "category": "personal", "action": "overwrite"}'`,
                  },
                  {
                    method: 'POST',
                    path: '/api/search',
                    desc: 'Perform hybrid text and vector semantic search across all memories',
                    sample: `curl -X POST http://localhost:6999/api/search \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Rust concurrency", "top_k": 5}'`,
                  },
                  {
                    method: 'GET',
                    path: '/api/models?provider=ollama',
                    desc: 'List discovered models strictly bifurcated by provider (ollama or openai)',
                    sample: 'curl "http://localhost:6999/api/models?provider=ollama"',
                  },
                  {
                    method: 'POST',
                    path: '/api/chat',
                    desc: 'Send prompt to AI Companion with automatic RAG retrieval & tool execution',
                    sample: `curl -X POST http://localhost:6999/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "What did I write about Python?", "provider": "ollama"}'`,
                  },
                ].map((ep, idx) => (
                  <div key={idx} className="p-4 rounded-xl border border-border bg-surface-hover/30 space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 font-mono text-xs">
                        <span className={cn(
                          'px-2 py-0.5 rounded font-bold text-[10px]',
                          ep.method === 'GET' ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400' : 'bg-sky-500/20 text-sky-600 dark:text-sky-400'
                        )}>
                          {ep.method}
                        </span>
                        <span className="font-semibold text-foreground">{ep.path}</span>
                      </div>
                      <button
                        onClick={() => copyCode(ep.sample, `api_${idx}`)}
                        className="text-muted-foreground hover:text-foreground p-1"
                        title="Copy curl command"
                      >
                        {copiedText === `api_${idx}` ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    <p className="text-xs text-muted-foreground">{ep.desc}</p>
                    <pre className="p-2.5 bg-surface-hover rounded font-mono text-[11px] overflow-x-auto text-foreground">
                      {ep.sample}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SECTION 4: MCP TOOLS */}
          {activeSection === 'mcp' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-bold tracking-tight mb-2">Model Context Protocol (MCP) Server</h1>
                <p className="text-sm text-muted-foreground">
                  Memorize registers 5 lean core MCP tools allowing any MCP-compliant agent (e.g. Claude Desktop, Google Gemini, Cursor, Antigravity) to store, update, delete, fetch, and search knowledge memories.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  { name: 'store', desc: 'Stores a memory into the system. If no category is given, auto-categorizes using the 11-category taxonomy.' },
                  { name: 'update', desc: 'Updates an existing memory. Overwrites, merges, or appends new information cleanly.' },
                  { name: 'delete', desc: 'Deletes a memory across disk markdown storage, SQLite DB index, and ChromaDB vector store.' },
                  { name: 'fetch', desc: 'Fetches full memory metadata and markdown content by ID/title, or lists stored memories.' },
                  { name: 'hybrid_fetch', desc: 'Performs 50/30/20 weighted hybrid RAG search combining vector similarity, tag matches, and categories.' },
                ].map((tool) => (
                  <div key={tool.name} className="p-3.5 rounded-xl border border-border bg-surface-hover/40 space-y-1">
                    <span className="font-mono font-bold text-xs text-foreground block">
                      ⚡ {tool.name}
                    </span>
                    <p className="text-[11px] text-muted-foreground">{tool.desc}</p>
                  </div>
                ))}
              </div>

              {/* Predefined Categories Taxonomy */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center gap-2">
                  <Folder className="w-4 h-4 text-foreground" />
                  <h3 className="text-sm font-bold text-foreground">Standard Categories Taxonomy for AI Auto-Assignment</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  {[
                    { cat: 'personal', desc: 'Habits, daily routine, diary, health, sleep, preferences, contacts, bio.' },
                    { cat: 'development', desc: 'Code snippets, languages (Python, TS, Rust), frameworks, algorithms, CSS, git.' },
                    { cat: 'projects', desc: 'App builds, side projects, product specs, feature roadmaps, blueprints.' },
                    { cat: 'job', desc: 'Career history, resume, employment, interviews, company projects, salary.' },
                    { cat: 'education', desc: 'College/university courses, study notes, degrees, exam prep, academic papers.' },
                    { cat: 'finance', desc: 'Budget, expenses, stock portfolio, investments, crypto, banking, tax.' },
                    { cat: 'gaming', desc: 'Video games, gameplay strategies, achievements, platforms (Steam, PS5).' },
                    { cat: 'achievements', desc: 'Competitive exam ranks (JEE, SAT), awards, hackathon prizes, milestones.' },
                    { cat: 'integration', desc: 'MCP servers, APIs, webhooks, SSH, WSL, cloud pipelines, OAuth setup.' },
                    { cat: 'media', desc: 'Books, movies, podcasts, reading lists, YouTube channels, OCR scans.' },
                    { cat: 'others', desc: 'Miscellaneous reference material and temporary unclassified notes.' },
                  ].map((c) => (
                    <div key={c.cat} className="p-2.5 rounded-lg border border-border bg-surface-list space-y-0.5">
                      <span className="font-mono font-bold text-xs text-foreground block">📂 {c.cat}</span>
                      <span className="text-[10px] text-muted-foreground block leading-tight">{c.desc}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}



          {/* SECTION 5: KEYBOARD SHORTCUTS */}
          {activeSection === 'shortcuts' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-bold tracking-tight mb-2">Global Keyboard Shortcuts</h1>
                <p className="text-sm text-muted-foreground">
                  Navigate, edit, search, and manage notes at maximum speed with zero mouse reliance.
                </p>
              </div>

              <div className="divide-y divide-border/60 border border-border rounded-xl bg-surface-hover/30 overflow-hidden">
                {[
                  { action: 'Save Note Immediately', mac: '⌘ S', win: 'Ctrl + S' },
                  { action: 'Create New Note', mac: '⌘ N', win: 'Ctrl + N' },
                  { action: 'Delete / Trash Active Note', mac: '⌘ ⌫', win: 'Ctrl + Delete' },
                  { action: 'Pin / Unpin Active Note', mac: '⌘ ⇧ P', win: 'Alt + P' },
                  { action: 'Favorite / Star Active Note', mac: '⌘ ⇧ S', win: 'Alt + S' },
                  { action: 'Global Hybrid Search', mac: '⌘ K', win: 'Ctrl + K' },
                  { action: 'Open Full Settings View', mac: '⌘ ,', win: 'Ctrl + ,' },
                  { action: 'Toggle AI Companion Drawer', mac: '⌘ ⇧ A', win: 'Ctrl + Shift + A' },
                  { action: 'Exit View / Back to Notes', mac: 'Esc', win: 'Esc' },
                  { action: 'Shortcuts Reference Sheet', mac: '⌘ /', win: 'Ctrl + /' },
                ].map((sc, i) => (
                  <div key={i} className="px-4 py-3 flex items-center justify-between text-xs">
                    <span className="font-semibold text-foreground">{sc.action}</span>
                    <div className="flex items-center gap-2">
                      <kbd className="px-2 py-1 rounded bg-surface-selected border border-border font-mono text-[11px] font-bold">
                        {sc.mac}
                      </kbd>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SECTION 6: ARCHITECTURE */}
          {activeSection === 'architecture' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-bold tracking-tight mb-2">Storage & Engine Architecture</h1>
                <p className="text-sm text-muted-foreground">
                  How Memorize coordinates filesystem markdown, relational SQLite, and vector embeddings without data drift.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-border bg-surface-hover/40 font-mono text-xs space-y-3">
                <div className="font-bold text-foreground flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  <span>3-Layer Persistent Data Pipeline:</span>
                </div>
                <div className="pl-4 space-y-2 text-muted-foreground">
                  <p>1. <strong>Filesystem Markdown (<code>data/memories/</code>)</strong>: Single source of truth in human-readable Markdown with YAML frontmatter.</p>
                  <p>2. <strong>SQLite Database (<code>data/memorize.db</code>)</strong>: Fast relational querying, revisions history, tag indexing, and soft-delete trash bin.</p>
                  <p>3. <strong>ChromaDB Vector Store (<code>data/chroma_db/</code>)</strong>: Sliding-window chunked embeddings (300 tokens + 50 overlap) with cosine similarity ranking.</p>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
