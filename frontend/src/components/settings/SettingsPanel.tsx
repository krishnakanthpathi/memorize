import React, { useEffect, useState } from 'react';
import {
  Settings,
  Cpu,
  Zap,
  Brain,
  X,
  Loader2,
  CheckCircle2,
  Moon,
  Sun,
  Palette,
  Terminal,
  Sparkles,
  Server,
  ShieldCheck,
  HardDriveDownload,
  Trash2,
  RefreshCw,
  ArrowLeft,
  Check,
  Database,
  FileCode,
  Keyboard,
  BookOpen,
  Sliders,
  Save,
} from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';
import { api } from '@/services/api';
import { ModelsResponse, AuditSummary, CodeTheme, AppIconType } from '@/types';
import { cn } from '@/lib/utils';

export const SettingsPanel: React.FC = () => {
  const {
    theme,
    setTheme,
    codeTheme,
    setCodeTheme,
    appIcon,
    setAppIcon,
    selectedModel,
    selectedProvider,
    setSelectedModel,
    setSelectedProvider,
    setActiveView,
    fetchNotes,
    fetchCategories,
  } = useNotesStore();

  const [ollamaData, setOllamaData] = useState<ModelsResponse | null>(null);
  const [openaiData, setOpenaiData] = useState<ModelsResponse | null>(null);
  const [loadingModels, setLoadingModels] = useState(false);
  const [testStatus, setTestStatus] = useState<string | null>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // MCP & Model Settings
  const [useLlm, setUseLlm] = useState<boolean>(false);
  const [embeddingModel, setEmbeddingModel] = useState<string>('all-MiniLM-L6-v2');
  const [classificationModel, setClassificationModel] = useState<string>('gpt-oss:120b-cloud');
  const [fallbackModel, setFallbackModel] = useState<string>('all-MiniLM-L6-v2');
  const [embeddingProvider, setEmbeddingProvider] = useState<string>('local');

  // Storage audit & repair state
  const [auditData, setAuditData] = useState<AuditSummary | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [fixLoading, setFixLoading] = useState(false);

  // Backup state
  const [backupLoading, setBackupLoading] = useState(false);
  const [backupMsg, setBackupMsg] = useState<string | null>(null);

  // Shortcuts customization presets
  const [shortcutPreset, setShortcutPreset] = useState<'standard' | 'vim' | 'compact'>('standard');

  const loadBackendSettings = async () => {
    try {
      const s = await api.getSettings();
      if (s) {
        if (typeof s.use_llm === 'boolean') setUseLlm(s.use_llm);
        if (s.embedding_model) setEmbeddingModel(s.embedding_model);
        if (s.classification_model) setClassificationModel(s.classification_model);
        if (s.fallback_model) setFallbackModel(s.fallback_model);
        if (s.embedding_provider) setEmbeddingProvider(s.embedding_provider);
      }
    } catch (err) {
      console.error('Failed to load settings from backend:', err);
    }
  };

  const loadAllModels = async () => {
    setLoadingModels(true);
    try {
      const [ollamaRes, openaiRes] = await Promise.all([
        api.getModels('ollama').catch(() => null),
        api.getModels('openai').catch(() => null),
      ]);
      setOllamaData(ollamaRes);
      setOpenaiData(openaiRes);

      // Default model selection if not set
      if (!selectedModel) {
        if (ollamaRes?.all_models && ollamaRes.all_models.length > 0) {
          setSelectedModel(ollamaRes.all_models[0]);
          setSelectedProvider('ollama');
        } else if (openaiRes?.all_models && openaiRes.all_models.length > 0) {
          setSelectedModel(openaiRes.all_models[0]);
          setSelectedProvider('openai');
        }
      }
    } catch (err) {
      console.error('Failed to load models:', err);
    } finally {
      setLoadingModels(false);
    }
  };

  const loadAudit = async () => {
    setAuditLoading(true);
    try {
      const data = await api.getAuditSummary();
      setAuditData(data);
    } catch (err) {
      console.error('Failed to fetch audit:', err);
    } finally {
      setAuditLoading(false);
    }
  };

  useEffect(() => {
    loadBackendSettings();
    loadAllModels();
    loadAudit();
  }, []);

  // Pressing Escape exits settings back to notes
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

  const handleToggleLlm = async () => {
    const nextVal = !useLlm;
    setUseLlm(nextVal);
    try {
      await api.updateSettings({ use_llm: nextVal });
    } catch (err) {
      console.error('Failed to update LLM setting:', err);
    }
  };

  const handleSaveSettings = async () => {
    localStorage.setItem('memorize_theme', theme);
    localStorage.setItem('memorize_code_theme', codeTheme);
    localStorage.setItem('memorize_app_icon', appIcon);
    localStorage.setItem('memorize_selected_model', selectedModel);
    localStorage.setItem('memorize_selected_provider', selectedProvider);

    try {
      await api.updateSettings({
        use_llm: useLlm,
        embedding_model: embeddingModel,
        classification_model: classificationModel,
        fallback_model: fallbackModel,
        embedding_provider: embeddingProvider,
        llm_provider: selectedProvider,
        ollama_model: selectedModel,
      });
      setSaveStatus('Configuration & MCP Settings Saved Successfully!');
    } catch (err: any) {
      setSaveStatus(`Saved locally (backend sync: ${err.message})`);
    }
    setTimeout(() => setSaveStatus(null), 3000);
  };


  const handleTestChat = async () => {
    setTestLoading(true);
    setTestStatus(null);
    try {
      const res = await api.testLlmConnection(
        selectedModel || undefined,
        selectedProvider || undefined
      );
      setTestStatus(`Connected! Model (${res.model}) replied: "${(res.reply || 'OK').slice(0, 80)}..."`);
    } catch (err: any) {
      setTestStatus(`Connection error: ${err.message}`);
    } finally {
      setTestLoading(false);
    }
  };

  const handleRunAuditFix = async () => {
    setFixLoading(true);
    try {
      const res = await api.runAuditFix();
      setAuditData(res);
      await fetchNotes();
      await fetchCategories();
    } catch (err) {
      console.error('Audit fix error:', err);
    } finally {
      setFixLoading(false);
    }
  };

  const handleCreateBackup = async () => {
    setBackupLoading(true);
    setBackupMsg(null);
    try {
      await api.createBackup();
      setBackupMsg("Backup created successfully in data/backups!");
    } catch (err: any) {
      setBackupMsg(`Backup failed: ${err.message}`);
    } finally {
      setBackupLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-background text-foreground overflow-hidden select-none animate-in fade-in duration-150">
      {/* Header */}
      <header className="h-14 px-6 border-b border-border flex items-center justify-between gap-4 shrink-0 bg-surface-sidebar">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-surface-hover border border-border/80 text-foreground">
            <Settings className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold leading-tight">Settings & Engine Control</h2>
            <p className="text-[11px] text-muted-foreground font-mono">
              Appearance, Unified LLMs, Shortcuts, and System Health
            </p>
          </div>
        </div>

        {/* Action Buttons: Save + Docs + Back to Notes */}
        <div className="flex items-center gap-2">
          {/* Save Button */}
          <button
            onClick={handleSaveSettings}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-foreground text-background text-xs font-semibold hover:opacity-90 transition-all shadow-xs"
          >
            {saveStatus ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Save className="w-3.5 h-3.5" />}
            <span>{saveStatus ? 'Saved!' : 'Save Settings'}</span>
          </button>

          <button
            onClick={() => setActiveView('docs')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-hover border border-border/80 text-xs font-semibold text-foreground hover:bg-surface-selected transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Documentation</span>
          </button>

          <button
            onClick={() => setActiveView('all')}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-hover border border-border/80 text-xs font-semibold hover:bg-surface-selected transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Notes</span>
            <kbd className="px-1.5 py-0.5 rounded bg-surface-selected font-mono text-[10px] border border-border/60">Esc</kbd>
          </button>
        </div>
      </header>

      {/* Save Success Banner */}
      {saveStatus && (
        <div className="bg-emerald-500/10 border-b border-emerald-500/20 px-6 py-2 flex items-center justify-between text-xs text-emerald-500 font-medium animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{saveStatus}</span>
          </div>
          <span className="text-[11px] font-mono opacity-80">All preferences synchronized</span>
        </div>
      )}

      {/* Main Settings Content */}
      <div className="flex-1 overflow-y-auto p-6 sm:p-10 max-w-4xl mx-auto w-full space-y-8 text-xs">
        {/* Section 1: Appearance & Brand Icon */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 border-b border-border/60 pb-2">
            <Palette className="w-4 h-4 text-foreground" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
              Monochrome Appearance Modes
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
            <div
              onClick={() => setTheme('light')}
              className={cn(
                'p-4 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2',
                theme === 'light'
                  ? 'border-foreground bg-white text-zinc-900 shadow-md font-bold ring-1 ring-foreground/20'
                  : 'border-border bg-surface-hover text-muted-foreground hover:text-foreground'
              )}
            >
              <Sun className="w-5 h-5 text-amber-600" />
              <div>
                <span className="block text-xs font-semibold">Light Mode</span>
                <span className="text-[10px] opacity-70">Crisp Pure White</span>
              </div>
            </div>

            <div
              onClick={() => setTheme('dark')}
              className={cn(
                'p-4 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2',
                theme === 'dark'
                  ? 'border-foreground bg-zinc-900 text-white shadow-md font-bold ring-1 ring-zinc-700'
                  : 'border-border bg-surface-hover text-muted-foreground hover:text-foreground'
              )}
            >
              <Moon className="w-5 h-5 text-zinc-300" />
              <div>
                <span className="block text-xs font-semibold">Dark Mode</span>
                <span className="text-[10px] opacity-70">Slate Zinc (Default)</span>
              </div>
            </div>

            <div
              onClick={() => setTheme('black')}
              className={cn(
                'p-4 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2',
                theme === 'black'
                  ? 'border-zinc-500 bg-black text-white shadow-md font-bold ring-1 ring-zinc-700'
                  : 'border-border bg-surface-hover text-muted-foreground hover:text-foreground'
              )}
            >
              <Zap className="w-5 h-5 text-white" />
              <div>
                <span className="block text-xs font-semibold">Pitch Black</span>
                <span className="text-[10px] opacity-70">OLED High Contrast</span>
              </div>
            </div>
          </div>

          {/* Panel App Icon Selector */}
          <div className="pt-2">
            <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block mb-2.5 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-foreground" />
              Sidebar Brand & Panel Icon
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
              {[
                { id: 'monogram' as const, label: 'Monogram', icon: () => <span className="font-bold text-xs">M</span> },
                { id: 'brain' as const, label: 'Brain', icon: () => <Brain className="w-4 h-4" /> },
                { id: 'terminal' as const, label: 'Terminal', icon: () => <Terminal className="w-4 h-4" /> },
                { id: 'book' as const, label: 'Notebook', icon: () => <BookOpen className="w-4 h-4" /> },
                { id: 'zap' as const, label: 'Zap', icon: () => <Zap className="w-4 h-4" /> },
                { id: 'database' as const, label: 'Vault', icon: () => <Database className="w-4 h-4" /> },
                { id: 'sparkles' as const, label: 'Sparkles', icon: () => <Sparkles className="w-4 h-4" /> },
              ].map((ic) => {
                const IconComponent = ic.icon;
                const isSelected = appIcon === ic.id;
                return (
                  <div
                    key={ic.id}
                    onClick={() => setAppIcon(ic.id)}
                    className={cn(
                      'p-2.5 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-1.5',
                      isSelected
                        ? 'border-foreground bg-surface-selected text-foreground font-bold shadow-xs ring-1 ring-foreground/20'
                        : 'border-border bg-surface-hover/50 text-muted-foreground hover:text-foreground hover:bg-surface-hover'
                    )}
                  >
                    <div className="w-7 h-7 rounded-lg bg-foreground text-background flex items-center justify-center">
                      <IconComponent />
                    </div>
                    <span className="text-[10px] truncate">{ic.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Section 2: Code Syntax Highlighting Theme */}
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-2">
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-foreground" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                Code Block Syntax Themes (Python, Java, Rust, TypeScript)
              </h3>
            </div>
            <span className="text-[10px] font-mono text-muted-foreground">
              Active: {codeTheme.toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {[
              { id: 'monokai' as const, name: 'Monokai Classic', badge: 'Vibrant Lime/Pink', accent: 'bg-[#f92672]' },
              { id: 'monokai-fire' as const, name: 'Monokai Fire', badge: 'Volcano Red/Orange', accent: 'bg-[#ff3366]' },
              { id: 'monokai-solenoid' as const, name: 'Monokai Solenoid', badge: 'Octagon Emerald', accent: 'bg-[#bad761]' },
              { id: 'vscode-dark' as const, name: 'VS Code Dark+', badge: 'Official Microsoft', accent: 'bg-[#569cd6]' },
              { id: 'github-dark' as const, name: 'GitHub Dark', badge: 'Coral & Sky Blue', accent: 'bg-[#ff7b72]' },
              { id: 'dracula' as const, name: 'Dracula', badge: 'Purple & Pink', accent: 'bg-[#bd93f9]' },
              { id: 'tokyo-night' as const, name: 'Tokyo Night', badge: 'Cyberpunk Neon', accent: 'bg-[#bb9af7]' },
              { id: 'nord' as const, name: 'Nord Frost', badge: 'Arctic Blue', accent: 'bg-[#88c0d0]' },
            ].map((ct) => (
              <div
                key={ct.id}
                onClick={() => setCodeTheme(ct.id)}
                className={cn(
                  'p-3 rounded-xl border cursor-pointer transition-all flex flex-col justify-between gap-2',
                  codeTheme === ct.id
                    ? 'border-foreground bg-surface-selected text-foreground font-bold shadow-xs ring-1 ring-foreground/20'
                    : 'border-border bg-surface-hover/50 text-muted-foreground hover:text-foreground hover:bg-surface-hover'
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold">{ct.name}</span>
                  <div className={cn("w-2.5 h-2.5 rounded-full", ct.accent)} />
                </div>
                <span className="text-[10px] opacity-70">{ct.badge}</span>
              </div>
            ))}
          </div>

          {/* Live Syntax Preview */}
          <div className={cn("p-4 rounded-xl border border-border transition-colors", `code-theme-${codeTheme}`)}>
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-[10px] text-muted-foreground uppercase font-bold">
                Live Preview (Python & Java):
              </span>
              <span className="px-2 py-0.5 rounded bg-surface-hover font-mono text-[10px] text-foreground font-semibold">
                theme: {codeTheme}
              </span>
            </div>
            <pre className="p-3.5 rounded-lg font-mono text-xs overflow-x-auto leading-relaxed border border-border/40 space-y-1">
              <div><span className="token comment"># Python Knowledge Engine</span></div>
              <div><span className="token keyword">import</span> asyncio</div>
              <div><span className="token keyword">from</span> typing <span className="token keyword">import</span> <span className="token class-name">List</span>, <span className="token class-name">Optional</span></div>
              <div><span className="token keyword">class</span> <span className="token class-name">MemoryEngine</span>:</div>
              <div>    <span className="token keyword">def</span> <span className="token function">recall</span>(<span className="token builtin">self</span>, query: <span className="token class-name">str</span>) -&gt; <span className="token class-name">Optional</span>[<span className="token class-name">dict</span>]:</div>
              <div>        <span className="token function">print</span>(<span className="token string">f"Querying vector database: "</span> + query)</div>
              <div>        <span className="token keyword">return</span> &#123;<span className="token string">"status"</span>: <span className="token string">"success"</span>, <span className="token string">"chunks"</span>: <span className="token number">42</span>, <span className="token string">"synced"</span>: <span className="token boolean">True</span>&#125;</div>
              <div className="pt-2"><span className="token comment">// Java Memory Service</span></div>
              <div><span className="token keyword">public class</span> <span className="token class-name">MemorizeApp</span> &#123;</div>
              <div>    <span className="token keyword">public static void</span> <span className="token function">main</span>(<span className="token class-name">String</span>[] args) &#123;</div>
              <div>        <span className="token class-name">System</span>.out.<span className="token function">println</span>(<span className="token string">"Monokai Fire &amp; VS Code Dark active!"</span>);</div>
              <div>    &#125;</div>
              <div>&#125;</div>
            </pre>
          </div>
        </section>

        {/* Section 3: MCP & UNIFIED MODEL CONFIGURATION */}
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-2">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-foreground" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                MCP Model Parameters & LLM Engine Control
              </h3>
            </div>
            <button
              onClick={loadAllModels}
              className="text-[11px] text-muted-foreground hover:text-foreground underline"
            >
              Re-scan Providers
            </button>
          </div>

          {/* Master LLM Toggle Switch Card */}
          <div className="p-4 rounded-xl border border-border bg-surface-hover/60 flex items-center justify-between gap-4">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <span className="font-bold text-xs text-foreground">
                  LLM AI Augmentation Mode
                </span>
                <span className={cn(
                  "px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase",
                  useLlm ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-muted text-muted-foreground border border-border"
                )}>
                  {useLlm ? "Enabled" : "Offline / Disabled"}
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground">
                {useLlm
                  ? "LLM is active for smart context merging, auto-classification, and AI chat."
                  : "LLM is disabled. Fast deterministic mode: rule-based classification, direct memory storage, zero latency."}
              </p>
            </div>

            <button
              type="button"
              onClick={handleToggleLlm}
              className={cn(
                "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                useLlm ? "bg-foreground" : "bg-border"
              )}
            >
              <span
                className={cn(
                  "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-background shadow-lg ring-0 transition duration-200 ease-in-out",
                  useLlm ? "translate-x-5" : "translate-x-0"
                )}
              />
            </button>
          </div>

          {/* MCP Model Parameters: Embedding, Classification, Fallback */}
          <div className="p-4 rounded-xl bg-surface-hover/40 border border-border space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-border/40">
              <Sliders className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs font-semibold text-foreground">MCP Model Parameters</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Active Embedding Model */}
              <div className="space-y-1">
                <label className="text-[10px] font-mono font-medium text-muted-foreground uppercase">
                  Embedding Model
                </label>
                <input
                  type="text"
                  value={embeddingModel}
                  onChange={(e) => setEmbeddingModel(e.target.value)}
                  placeholder="all-MiniLM-L6-v2"
                  className="w-full bg-surface-list border border-border rounded-lg px-2.5 py-1.5 text-xs font-mono text-foreground focus:ring-1 focus:ring-ring outline-none"
                />
                <span className="text-[10px] text-muted-foreground block font-mono">e.g. nomic-embed-text, bge-m3</span>
              </div>

              {/* Classification Model */}
              <div className="space-y-1">
                <label className="text-[10px] font-mono font-medium text-muted-foreground uppercase">
                  Classification Model
                </label>
                <input
                  type="text"
                  value={classificationModel}
                  onChange={(e) => setClassificationModel(e.target.value)}
                  placeholder="gpt-oss:120b-cloud"
                  className="w-full bg-surface-list border border-border rounded-lg px-2.5 py-1.5 text-xs font-mono text-foreground focus:ring-1 focus:ring-ring outline-none"
                />
                <span className="text-[10px] text-muted-foreground block font-mono">Used when LLM is enabled</span>
              </div>

              {/* Fallback Model */}
              <div className="space-y-1">
                <label className="text-[10px] font-mono font-medium text-muted-foreground uppercase">
                  Fallback Model
                </label>
                <input
                  type="text"
                  value={fallbackModel}
                  onChange={(e) => setFallbackModel(e.target.value)}
                  placeholder="all-MiniLM-L6-v2"
                  className="w-full bg-surface-list border border-border rounded-lg px-2.5 py-1.5 text-xs font-mono text-foreground focus:ring-1 focus:ring-ring outline-none"
                />
                <span className="text-[10px] text-muted-foreground block font-mono">Offline local fallback</span>
              </div>
            </div>
          </div>

          {/* Active MCP Core Tools Status Card */}
          <div className="p-4 rounded-xl bg-surface-hover/30 border border-border space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-foreground">Registered MCP Tools (7 Active Tools)</span>
              <span className="px-2 py-0.5 rounded bg-surface-selected font-mono text-[10px] font-bold text-foreground">
                Active &amp; Ready
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-4 md:grid-cols-7 gap-2 pt-1">
              {[
                { name: 'store', desc: 'Auto-categorizes & creates/appends' },
                { name: 'update', desc: 'Updates or merges note content' },
                { name: 'delete', desc: 'Deletes note from DB & vector' },
                { name: 'fetch', desc: 'Retrieves full note by ID/title' },
                { name: 'hybrid_fetch', desc: '50/30/20 weighted RAG search' },
                { name: 'list_memories', desc: 'Lists memory summaries & filter' },
                { name: 'get_categories', desc: 'Lists 11 categories & note counts' },
              ].map((t) => (
                <div key={t.name} className="p-2 rounded-lg bg-surface-list border border-border/60 space-y-0.5">
                  <span className="font-mono font-bold text-[11px] text-foreground block">⚡ {t.name}</span>
                  <span className="text-[10px] text-muted-foreground block leading-tight">{t.desc}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-surface-hover/60 border border-border space-y-4">

            <div>
              <label className="text-[11px] text-muted-foreground block mb-1.5 font-medium">
                Active Chat Model (Ollama Local & OpenAI Remote):
              </label>
              <select
                value={`${selectedProvider}::${selectedModel}`}
                onChange={(e) => {
                  const [prov, mod] = e.target.value.split('::');
                  setSelectedProvider(prov);
                  setSelectedModel(mod);
                }}
                className="w-full bg-surface-list border border-border rounded-lg px-3 py-2 text-xs font-mono outline-none focus:ring-1 focus:ring-ring text-foreground"
              >
                {ollamaData?.all_models && ollamaData.all_models.length > 0 && (
                  <optgroup label="🦙 Ollama Local Models">
                    {ollamaData.all_models.map((m) => (
                      <option key={`ollama::${m}`} value={`ollama::${m}`}>
                        [Ollama] {m}
                      </option>
                    ))}
                  </optgroup>
                )}

                {openaiData?.all_models && openaiData.all_models.length > 0 && (
                  <optgroup label="🌐 OpenAI Compatible Remote Models">
                    {openaiData.all_models.map((m) => (
                      <option key={`openai::${m}`} value={`openai::${m}`}>
                        [OpenAI] {m}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            </div>

            {/* Test Model Connection */}
            <div className="flex items-center justify-between pt-3 border-t border-border/60">
              <div className="text-[11px] text-muted-foreground font-mono truncate max-w-sm">
                {testStatus ? (
                  <span className={cn(testStatus.startsWith('Connected') ? 'text-emerald-500 font-semibold' : 'text-rose-500')}>
                    {testStatus}
                  </span>
                ) : (
                  <span>Active: <strong>{selectedModel || 'Default'}</strong> ({selectedProvider === 'ollama' ? 'Ollama Local' : 'OpenAI Remote'})</span>
                )}
              </div>

              <button
                type="button"
                onClick={handleTestChat}
                disabled={testLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-foreground text-background text-xs font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 shadow-xs shrink-0"
              >
                {testLoading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Server className="w-3.5 h-3.5" />
                )}
                <span>Test Connection</span>
              </button>
            </div>
          </div>

          {/* Discovered Models Side-by-Side Unified View */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Ollama Local Models */}
            <div className="p-3.5 rounded-xl bg-surface-hover/60 border border-border space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 font-bold text-foreground">
                  <Cpu className="w-4 h-4 text-foreground" />
                  <span>Ollama Local ({ollamaData?.total_count || 0})</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">localhost:11434</span>
              </div>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {(ollamaData?.all_models || []).length > 0 ? (
                  ollamaData!.all_models.map((m) => (
                    <div
                      key={m}
                      onClick={() => {
                        setSelectedProvider('ollama');
                        setSelectedModel(m);
                      }}
                      className={cn(
                        "px-2.5 py-1 rounded bg-surface-list font-mono text-[11px] border cursor-pointer hover:border-foreground transition-all flex items-center justify-between",
                        selectedProvider === 'ollama' && selectedModel === m ? "border-foreground font-bold shadow-xs" : "border-border/50 text-foreground"
                      )}
                    >
                      <span className="truncate">{m}</span>
                      {selectedProvider === 'ollama' && selectedModel === m && <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />}
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground italic text-[11px]">No Ollama models found</p>
                )}
              </div>
            </div>

            {/* OpenAI Remote Models */}
            <div className="p-3.5 rounded-xl bg-surface-hover/60 border border-border space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 font-bold text-foreground">
                  <Sparkles className="w-4 h-4 text-foreground" />
                  <span>OpenAI Remote ({openaiData?.total_count || 0})</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">Remote API</span>
              </div>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {(openaiData?.all_models || []).length > 0 ? (
                  openaiData!.all_models.map((m) => (
                    <div
                      key={m}
                      onClick={() => {
                        setSelectedProvider('openai');
                        setSelectedModel(m);
                      }}
                      className={cn(
                        "px-2.5 py-1 rounded bg-surface-list font-mono text-[11px] border cursor-pointer hover:border-foreground transition-all flex items-center justify-between",
                        selectedProvider === 'openai' && selectedModel === m ? "border-foreground font-bold shadow-xs" : "border-border/50 text-foreground"
                      )}
                    >
                      <span className="truncate">{m}</span>
                      {selectedProvider === 'openai' && selectedModel === m && <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />}
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground italic text-[11px]">No remote models found</p>
                )}
              </div>
            </div>
          </div>
        </section>


        {/* Section 4: Keyboard Shortcuts Customization & Presets */}
        <section className="space-y-3">
          <div className="flex items-center justify-between border-b border-border/60 pb-2">
            <div className="flex items-center gap-2">
              <Keyboard className="w-4 h-4 text-foreground" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                Keyboard Shortcuts & Keybindings
              </h3>
            </div>
            <div className="flex items-center gap-1 bg-surface-hover p-0.5 rounded-lg border border-border">
              {(['standard', 'vim', 'compact'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setShortcutPreset(mode)}
                  className={cn(
                    'px-2.5 py-0.5 rounded capitalize text-[11px] font-medium transition-colors',
                    shortcutPreset === mode
                      ? 'bg-card text-foreground font-semibold shadow-xs'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          <div className="divide-y divide-border/60 border border-border rounded-xl bg-surface-hover/30 overflow-hidden">
            {[
              { action: 'Save Note Immediately', key: '⌘ S', code: 'Cmd/Ctrl + S', enabled: true },
              { action: 'Create New Note', key: '⌘ N', code: 'Cmd/Ctrl + N', enabled: true },
              { action: 'Delete / Trash Active Note', key: '⌘ ⌫', code: 'Cmd/Ctrl + Backspace', enabled: true },
              { action: 'Pin / Unpin Active Note', key: '⌘ ⇧ P', code: 'Cmd/Ctrl + Shift + P', enabled: true },
              { action: 'Favorite / Star Active Note', key: '⌘ ⇧ S', code: 'Cmd/Ctrl + Shift + S', enabled: true },
              { action: 'Global Hybrid Search', key: '⌘ K', code: 'Cmd/Ctrl + K', enabled: true },
              { action: 'Open Full Settings View', key: '⌘ ,', code: 'Cmd/Ctrl + ,', enabled: true },
              { action: 'Toggle AI Companion Drawer', key: '⌘ ⇧ A', code: 'Cmd/Ctrl + Shift + A', enabled: true },
              { action: 'Exit View / Back to Notes', key: 'Esc', code: 'Escape', enabled: true },
            ].map((item, idx) => (
              <div key={idx} className="px-4 py-2.5 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground">{item.action}</span>
                  <span className="text-[11px] text-muted-foreground font-mono">({item.code})</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-0.5 rounded bg-surface-selected border border-border font-mono text-[11px] font-bold">
                    {item.key}
                  </kbd>
                  <span className="text-[10px] text-emerald-500 font-mono font-semibold">Active</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 5: Storage Health & Reconciliation */}
        <section className="space-y-3">
          <div className="flex items-center justify-between border-b border-border/60 pb-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-foreground" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                Storage Integrity & Health
              </h3>
            </div>
            <button
              onClick={handleRunAuditFix}
              disabled={fixLoading}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-foreground text-background text-[11px] font-semibold hover:opacity-90 disabled:opacity-50"
            >
              {fixLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
              <span>Auto-Fix Storage</span>
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-surface-hover/60 border border-border">
              <span className="text-[10px] text-muted-foreground uppercase font-mono block">Markdown Files</span>
              <span className="text-lg font-bold font-mono">{auditData?.total_files || 0}</span>
            </div>
            <div className="p-3 rounded-xl bg-surface-hover/60 border border-border">
              <span className="text-[10px] text-muted-foreground uppercase font-mono block">SQLite Records</span>
              <span className="text-lg font-bold font-mono">{auditData?.total_db_records || 0}</span>
            </div>
            <div className="p-3 rounded-xl bg-surface-hover/60 border border-border">
              <span className="text-[10px] text-muted-foreground uppercase font-mono block">Vector Chunks</span>
              <span className="text-lg font-bold font-mono">{auditData?.total_vector_chunks || 0}</span>
            </div>
            <div className="p-3 rounded-xl bg-surface-hover/60 border border-border">
              <span className="text-[10px] text-muted-foreground uppercase font-mono block">Orphan Status</span>
              <span className={cn("text-lg font-bold font-mono", (auditData?.orphan_files_count || 0) === 0 ? "text-emerald-500" : "text-amber-500")}>
                {(auditData?.orphan_files_count || 0) === 0 ? 'Healthy' : `${auditData?.orphan_files_count} Issues`}
              </span>
            </div>
          </div>
        </section>

        {/* Section 6: Backups & Architecture Info */}
        <section className="space-y-3">
          <div className="flex items-center justify-between border-b border-border/60 pb-2">
            <div className="flex items-center gap-2">
              <HardDriveDownload className="w-4 h-4 text-foreground" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                Backup & Snapshots
              </h3>
            </div>
            <button
              onClick={handleCreateBackup}
              disabled={backupLoading}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-hover border border-border text-[11px] font-semibold hover:text-foreground"
            >
              {backupLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <HardDriveDownload className="w-3 h-3" />}
              <span>Create Backup Snapshot</span>
            </button>
          </div>

          {backupMsg && (
            <p className={cn("text-xs font-mono", backupMsg.includes('success') ? 'text-emerald-500' : 'text-rose-500')}>
              {backupMsg}
            </p>
          )}

          <div className="p-4 rounded-xl bg-surface-hover/40 border border-border/80 text-[11px] text-muted-foreground font-mono space-y-1.5">
            <div className="flex items-center gap-1.5 text-foreground font-bold mb-1">
              <Terminal className="w-3.5 h-3.5" />
              <span>Backend Architecture & Specifications</span>
            </div>
            <p>• FastAPI Local Service: <code>http://localhost:6999</code></p>
            <p>• SQLite Master Database: <code>data/memorize.db</code></p>
            <p>• ChromaDB Vector Engine: <code>data/chroma_db</code> (persistent)</p>
            <p>• Automated Tool Invocation: <code>create_memory, search_memories, read_memory, delete_memory</code></p>
          </div>
        </section>
      </div>
    </div>
  );
};
