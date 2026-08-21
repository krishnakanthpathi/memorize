import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  ArrowLeft,
  Search,
  Code,
  Layers,
  Sparkles,
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
    { id: 'mcp', label: 'MCP Tools Ecosystem', icon: Zap },
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
                    <Sparkles className="w-4 h-4 text-violet-500" />
                    <span>AI Synthesis & Polish</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Intelligently synthesize multiple notes, generate smart titles, and polish structured markdown content.
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
                    path: '/api/memories/merge',
                    desc: 'Merge & synthesize multiple notes with AI into a unified knowledge note',
                    sample: `curl -X POST http://localhost:6999/api/memories/merge \\
  -H "Content-Type: application/json" \\
  -d '{"memory_ids": ["mem_1", "mem_2"], "use_ai": true, "delete_sources": false}'`,
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

          {/* SECTION 4: MCP TOOLS & PROTOCOL */}
          {activeSection === 'mcp' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-bold tracking-tight mb-2">Model Context Protocol (MCP) Ecosystem</h1>
                <p className="text-sm text-muted-foreground">
                  The Model Context Protocol (MCP) turns Memorize into an external long-term memory system for any AI agent (Claude Desktop, Cursor, Gemini, Antigravity, Claude Code). It enables autonomous note creation, semantic RAG retrieval, synthesis, and synchronization across Markdown, SQLite, and ChromaDB.
                </p>
              </div>

              {/* MCP Configuration Snippets */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-foreground" />
                  <h3 className="text-sm font-bold text-foreground">MCP Client Configuration (JSON)</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {/* Claude Desktop Config */}
                  <div className="p-4 rounded-xl border border-border bg-surface-hover/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-foreground">Claude Desktop</span>
                      <button
                        onClick={() =>
                          copyCode(
                            JSON.stringify(
                              {
                                mcpServers: {
                                  memorize: {
                                    command: "python3",
                                    args: ["/Users/krishnakanth/Projects/memorize/main.py"],
                                    env: {
                                      PYTHONPATH: "/Users/krishnakanth/Projects/memorize",
                                    },
                                  },
                                },
                              },
                              null,
                              2
                            ),
                            'claude-json'
                          )
                        }
                        className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-surface-selected hover:bg-surface-hover border border-border cursor-pointer transition-colors"
                      >
                        {copiedText === 'claude-json' ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                        {copiedText === 'claude-json' ? 'Copied' : 'Copy JSON'}
                      </button>
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                      Add to <code className="font-mono text-[10px] bg-surface-selected px-1 py-0.5 rounded">~/Library/Application Support/Claude/claude_desktop_config.json</code>
                    </p>
                    <pre className="p-2.5 rounded-lg bg-surface-list border border-border font-mono text-[10px] text-muted-foreground overflow-x-auto">
                      {`{
  "mcpServers": {
    "memorize": {
      "command": "python3",
      "args": ["/Users/krishnakanth/Projects/memorize/main.py"]
    }
  }
}`}
                    </pre>
                  </div>

                  {/* Cursor IDE Config */}
                  <div className="p-4 rounded-xl border border-border bg-surface-hover/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-foreground">Cursor / Antigravity</span>
                      <button
                        onClick={() =>
                          copyCode(
                            JSON.stringify(
                              {
                                mcpServers: {
                                  memorize: {
                                    command: "python3",
                                    args: ["main.py"],
                                    cwd: "/Users/krishnakanth/Projects/memorize",
                                  },
                                },
                              },
                              null,
                              2
                            ),
                            'cursor-json'
                          )
                        }
                        className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-surface-selected hover:bg-surface-hover border border-border cursor-pointer transition-colors"
                      >
                        {copiedText === 'cursor-json' ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                        {copiedText === 'cursor-json' ? 'Copied' : 'Copy JSON'}
                      </button>
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                      Add to <code className="font-mono text-[10px] bg-surface-selected px-1 py-0.5 rounded">~/.cursor/mcp.json</code> or project settings
                    </p>
                    <pre className="p-2.5 rounded-lg bg-surface-list border border-border font-mono text-[10px] text-muted-foreground overflow-x-auto">
                      {`{
  "mcpServers": {
    "memorize": {
      "command": "python3",
      "args": ["main.py"],
      "cwd": "/Users/krishnakanth/Projects/memorize"
    }
  }
}`}
                    </pre>
                  </div>

                  {/* Remote / SSE Config */}
                  <div className="p-4 rounded-xl border border-border bg-surface-hover/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-foreground">Remote / SSE (Google Gemini / Webhooks)</span>
                      <button
                        onClick={() =>
                          copyCode(
                            JSON.stringify(
                              {
                                mcpServers: {
                                  memorize: {
                                    url: "http://localhost:7777/sse",
                                  },
                                },
                              },
                              null,
                              2
                            ),
                            'sse-json'
                          )
                        }
                        className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-surface-selected hover:bg-surface-hover border border-border cursor-pointer transition-colors"
                      >
                        {copiedText === 'sse-json' ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                        {copiedText === 'sse-json' ? 'Copied' : 'Copy URL'}
                      </button>
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                      Direct HTTP/SSE endpoint (served simultaneously on port 7777)
                    </p>
                    <pre className="p-2.5 rounded-lg bg-surface-list border border-border font-mono text-[10px] text-muted-foreground overflow-x-auto">
                      {`{
  "mcpServers": {
    "memorize": {
      "url": "http://localhost:7777/sse"
    }
  }
}`}
                    </pre>
                  </div>

                  {/* Claude Code CLI */}
                  <div className="p-4 rounded-xl border border-border bg-surface-hover/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-foreground">Claude Code CLI</span>
                      <button
                        onClick={() =>
                          copyCode(
                            "claude mcp add memorize -- python3 /Users/krishnakanth/Projects/memorize/main.py",
                            'cli-cmd'
                          )
                        }
                        className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-surface-selected hover:bg-surface-hover border border-border cursor-pointer transition-colors"
                      >
                        {copiedText === 'cli-cmd' ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                        {copiedText === 'cli-cmd' ? 'Copied' : 'Copy Command'}
                      </button>
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                      Run directly in terminal to register Memorize globally
                    </p>
                    <pre className="p-2.5 rounded-lg bg-surface-list border border-border font-mono text-[10px] text-muted-foreground overflow-x-auto">
                      claude mcp add memorize -- python3 /Users/krishnakanth/Projects/memorize/main.py
                    </pre>
                  </div>
                </div>
              </div>

              {/* 12 Core Registered MCP Tools */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-foreground" />
                    <h3 className="text-sm font-bold text-foreground">12 Registered FastMCP Tools</h3>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-surface-selected font-mono text-[10px] font-bold text-foreground">
                    12 Active Tools
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[
                    { name: 'store', desc: 'Saves a new memory. Auto-categorizes into the 11-category taxonomy and generates embeddings.' },
                    { name: 'update', desc: 'Updates, appends, or cleanly merges content with existing notes without data loss.' },
                    { name: 'delete', desc: 'Purges a note permanently across Markdown storage, SQLite index, and ChromaDB vector store.' },
                    { name: 'fetch', desc: 'Retrieves full Markdown content, YAML frontmatter, and metadata by ID or title.' },
                    { name: 'hybrid_fetch', desc: '50/30/20 weighted hybrid RAG search combining vector similarity, tag matches, and categories.' },
                    { name: 'list_memories', desc: 'Lists stored memory summaries with optional category/tag filters and limit.' },
                    { name: 'get_categories', desc: 'Returns all 11 standard predefined categories with note counts and semantic descriptions.' },
                    { name: 'merge_memories', desc: 'Consolidates multiple notes into a single master document with AI or deterministic merging.' },
                    { name: 'find_correlated_memories', desc: 'Discovers semantically related notes using vector similarity and tag overlap.' },
                    { name: 'organize_memory', desc: 'Polishes, restructures, or summarizes a note using AI with automatic rollback snapshot.' },
                    { name: 'generate_title', desc: 'Generates a concise, high-signal 3-7 word title from note content.' },
                    { name: 'organize_selection', desc: 'Transforms or polishes a selected passage (polish, summarize, technical, expand).' },
                  ].map((tool) => (
                    <div key={tool.name} className="p-3.5 rounded-xl border border-border bg-surface-hover/40 space-y-1">
                      <span className="font-mono font-bold text-xs text-foreground block">
                        ⚡ {tool.name}
                      </span>
                      <p className="text-[11px] text-muted-foreground">{tool.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Predefined Categories Taxonomy */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center gap-2">
                  <Folder className="w-4 h-4 text-foreground" />
                  <h3 className="text-sm font-bold text-foreground">Standard 11-Category Taxonomy</h3>
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

              {/* Safety, Concurrency & Performance FAQ */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-foreground" />
                  <h3 className="text-sm font-bold text-foreground">Architecture, Safety & Concurrency</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3.5 rounded-xl border border-border bg-surface-list space-y-1">
                    <span className="text-xs font-bold text-foreground block">Does it lock or corrupt the database?</span>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      No. SQLite operates in WAL (Write-Ahead Logging) mode and ChromaDB uses isolated persistent embeddings. Running the FastAPI web app and MCP server concurrently causes zero file locks.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-xl border border-border bg-surface-list space-y-1">
                    <span className="text-xs font-bold text-foreground block">What if an AI accidentally modifies or deletes notes?</span>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      Memorize takes version snapshots on every update and preserves deleted note snapshots. You can restore historical versions anytime from the Version History drawer or Backup Manager.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-xl border border-border bg-surface-list space-y-1">
                    <span className="text-xs font-bold text-foreground block">Does it slow down LLM conversations?</span>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      MCP tool execution runs locally in under 50ms. RAG retrieval queries top-k ranked chunks, injecting minimal tokens to prevent prompt bloat.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-xl border border-border bg-surface-list space-y-1">
                    <span className="text-xs font-bold text-foreground block">How to run without port conflicts?</span>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      The FastAPI backend on port 7777 automatically serves both REST routes and Universal MCP (<code className="font-mono text-[10px]">/mcp</code> and <code className="font-mono text-[10px]">/sse</code>). For Claude Desktop or Cursor, use standard stdio transport (<code className="font-mono text-[10px]">python3 main.py</code>).
                    </p>
                  </div>
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
