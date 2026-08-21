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
  RefreshCw,
  ArrowLeft,
  Database,
  FileCode,
  Keyboard,
  BookOpen,
  Sliders,
  Save,
  Check,
  Copy,
  Layers,
  Code2,
} from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';
import { api } from '@/services/api';
import { ModelsResponse, AuditSummary, CodeTheme, AppIconType } from '@/types';
import { cn } from '@/lib/utils';
import { PromptsViewer } from './PromptsViewer';

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

  // MCP Copied indicator
  const [mcpCopied, setMcpCopied] = useState<string | null>(null);
  const copyMcpConfig = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setMcpCopied(id);
    setTimeout(() => setMcpCopied(null), 2000);
  };

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
      setSaveStatus('Configuration & Preferences Saved Successfully!');
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
      setBackupMsg('Backup created successfully in data/backups!');
    } catch (err: any) {
      setBackupMsg(`Backup failed: ${err.message}`);
    } finally {
      setBackupLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-background text-foreground overflow-hidden select-none animate-in fade-in duration-150">
      {/* Top Navigation Header */}
      <header className="h-14 px-6 border-b border-border flex items-center justify-between gap-4 shrink-0 bg-surface-sidebar">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-surface-hover border border-border/80 text-foreground">
            <Settings className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold leading-tight">Settings & Engine Control</h2>
            <p className="text-[11px] text-muted-foreground font-mono">
              Appearance, Unified LLM Hub, Prompts Viewer, and Storage Dashboard
            </p>
          </div>
        </div>

        {/* Action Controls: Save + Docs + Back to Notes */}
        <div className="flex items-center gap-2">
          {/* Save Button */}
          <button
            onClick={handleSaveSettings}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-foreground text-background text-xs font-semibold hover:opacity-90 transition-all shadow-xs cursor-pointer"
          >
            {saveStatus ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
            <span>{saveStatus ? 'Saved!' : 'Save Settings'}</span>
          </button>

          <button
            onClick={() => setActiveView('docs')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-hover border border-border/80 text-xs font-semibold text-foreground hover:bg-surface-selected transition-colors cursor-pointer"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Documentation</span>
          </button>

          <button
            onClick={() => setActiveView('all')}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-hover border border-border/80 text-xs font-semibold hover:bg-surface-selected transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Notes</span>
            <kbd className="px-1.5 py-0.5 rounded bg-surface-selected font-mono text-[10px] border border-border/60">Esc</kbd>
          </button>
        </div>
      </header>

      {/* Save Notification Banner */}
      {saveStatus && (
        <div className="bg-surface-hover border-b border-border px-6 py-2 flex items-center justify-between text-xs text-foreground font-medium animate-in fade-in shrink-0">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{saveStatus}</span>
          </div>
          <span className="text-[11px] font-mono opacity-80">All preferences synchronized</span>
        </div>
      )}

      {/* Main Settings Content: Balanced Multi-Column Responsive Grid */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto w-full space-y-6 text-xs">
        
        {/* =========================================================================
            GRID ROW 1: Appearance Modes & Code Syntax Highlighting (2-Column Grid)
            ========================================================================= */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Card 1: Theme & Brand Icon */}
          <div className="p-5 rounded-2xl bg-card border border-border shadow-xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center gap-2 pb-2.5 border-b border-border/60">
                <Palette className="w-4 h-4 text-foreground" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                  Monochrome Appearance & Icons
                </h3>
              </div>

              {/* 3-Way Monochrome Theme Selector */}
              <div className="grid grid-cols-3 gap-2.5 pt-3">
                <div
                  onClick={() => setTheme('light')}
                  className={cn(
                    'p-3 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-1.5',
                    theme === 'light'
                      ? 'border-foreground bg-white text-zinc-900 shadow-md font-bold ring-1 ring-foreground/20'
                      : 'border-border bg-surface-hover/70 text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Sun className="w-4 h-4 text-foreground" />
                  <div>
                    <span className="block text-xs font-semibold">Light</span>
                    <span className="text-[9px] opacity-70">Pure White</span>
                  </div>
                </div>


                <div
                  onClick={() => setTheme('dark')}
                  className={cn(
                    'p-3 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-1.5',
                    theme === 'dark'
                      ? 'border-foreground bg-zinc-900 text-white shadow-md font-bold ring-1 ring-zinc-700'
                      : 'border-border bg-surface-hover/70 text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Moon className="w-4 h-4 text-zinc-300" />
                  <div>
                    <span className="block text-xs font-semibold">Dark</span>
                    <span className="text-[9px] opacity-70">Slate Zinc</span>
                  </div>
                </div>

                <div
                  onClick={() => setTheme('black')}
                  className={cn(
                    'p-3 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-1.5',
                    theme === 'black'
                      ? 'border-zinc-500 bg-black text-white shadow-md font-bold ring-1 ring-zinc-700'
                      : 'border-border bg-surface-hover/70 text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Zap className="w-4 h-4 text-white" />
                  <div>
                    <span className="block text-xs font-semibold">OLED</span>
                    <span className="text-[9px] opacity-70">Pitch Black</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Sidebar Brand Monogram/Icon Selector */}
            <div className="pt-2 border-t border-border/50">
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block mb-2 flex items-center gap-1.5 font-mono">
                <Sliders className="w-3 h-3 text-foreground" />
                Sidebar Brand Icon:
              </label>
              <div className="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
                {[
                  { id: 'monogram' as const, label: 'Monogram', icon: () => <span className="font-bold text-xs">M</span> },
                  { id: 'brain' as const, label: 'Brain', icon: () => <Brain className="w-3.5 h-3.5" /> },
                  { id: 'terminal' as const, label: 'Terminal', icon: () => <Terminal className="w-3.5 h-3.5" /> },
                  { id: 'book' as const, label: 'Notebook', icon: () => <BookOpen className="w-3.5 h-3.5" /> },
                  { id: 'zap' as const, label: 'Zap', icon: () => <Zap className="w-3.5 h-3.5" /> },
                  { id: 'database' as const, label: 'Vault', icon: () => <Database className="w-3.5 h-3.5" /> },
                  { id: 'sparkles' as const, label: 'Sparkles', icon: () => <Sparkles className="w-3.5 h-3.5" /> },
                ].map((ic) => {
                  const IconComponent = ic.icon;
                  const isSelected = appIcon === ic.id;
                  return (
                    <div
                      key={ic.id}
                      onClick={() => setAppIcon(ic.id)}
                      className={cn(
                        'p-2 rounded-lg border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-1',
                        isSelected
                          ? 'border-foreground bg-surface-selected text-foreground font-bold shadow-2xs ring-1 ring-foreground/20'
                          : 'border-border bg-surface-hover/50 text-muted-foreground hover:text-foreground hover:bg-surface-hover'
                      )}
                    >
                      <div className="w-6 h-6 rounded-md bg-foreground text-background flex items-center justify-center">
                        <IconComponent />
                      </div>
                      <span className="text-[9px] truncate">{ic.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Card 2: Code Syntax Themes */}
          <div className="p-5 rounded-2xl bg-card border border-border shadow-xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between pb-2.5 border-b border-border/60">
                <div className="flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-foreground" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                    Code Block Syntax Themes
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">
                  Active: {codeTheme.toUpperCase()}
                </span>
              </div>

              {/* 8 Themes Selector */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3">
                {[
                  { id: 'monokai' as const, name: 'Monokai', accent: 'bg-[#f92672]' },
                  { id: 'monokai-fire' as const, name: 'Fire', accent: 'bg-[#ff3366]' },
                  { id: 'monokai-solenoid' as const, name: 'Solenoid', accent: 'bg-[#bad761]' },
                  { id: 'vscode-dark' as const, name: 'VS Code', accent: 'bg-[#569cd6]' },
                  { id: 'github-dark' as const, name: 'GitHub', accent: 'bg-[#ff7b72]' },
                  { id: 'dracula' as const, name: 'Dracula', accent: 'bg-[#bd93f9]' },
                  { id: 'tokyo-night' as const, name: 'Tokyo', accent: 'bg-[#bb9af7]' },
                  { id: 'nord' as const, name: 'Nord', accent: 'bg-[#88c0d0]' },
                ].map((ct) => (
                  <div
                    key={ct.id}
                    onClick={() => setCodeTheme(ct.id)}
                    className={cn(
                      'p-2.5 rounded-lg border cursor-pointer transition-all flex items-center justify-between gap-1.5',
                      codeTheme === ct.id
                        ? 'border-foreground bg-surface-selected text-foreground font-bold shadow-2xs ring-1 ring-foreground/20'
                        : 'border-border bg-surface-hover/50 text-muted-foreground hover:text-foreground hover:bg-surface-hover'
                    )}
                  >
                    <span className="text-[11px] truncate font-medium">{ct.name}</span>
                    <div className={cn('w-2 h-2 rounded-full shrink-0', ct.accent)} />
                  </div>
                ))}
              </div>
            </div>

            {/* Live Syntax Preview */}
            <div className={cn('p-3 rounded-xl border border-border/70 transition-colors', `code-theme-${codeTheme}`)}>
              <div className="flex items-center justify-between mb-1.5 text-[9px] font-mono text-muted-foreground">
                <span>PREVIEW (Python & Rust)</span>
                <span>theme: {codeTheme}</span>
              </div>
              <pre className="p-2.5 rounded-lg font-mono text-[11px] overflow-x-auto leading-relaxed border border-border/40 space-y-0.5">
                <div><span className="token comment"># Hybrid Vector + Text Recall</span></div>
                <div><span className="token keyword">async def</span> <span className="token function">search</span>(query: <span className="token class-name">str</span>) -&gt; <span className="token class-name">List</span>[Memory]:</div>
                <div>    <span className="token keyword">return</span> <span className="token keyword">await</span> engine.<span className="token function">hybrid_fetch</span>(query, top_k=<span className="token number">5</span>)</div>
              </pre>
            </div>
          </div>
        </div>

        {/* =========================================================================
            GRID ROW 2: LLM Engine & Provider Hub + Discovered Models (2-Column Grid)
           ========================================================================= */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Card 3: LLM Engine & Provider Controls */}
          <div className="p-5 rounded-2xl bg-card border border-border shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-2.5 border-b border-border/60">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-foreground" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                  LLM AI Engine & Provider Hub
                </h3>
              </div>
              <button
                onClick={loadAllModels}
                className="text-[10px] font-mono text-muted-foreground hover:text-foreground underline"
              >
                Re-scan Models
              </button>
            </div>

            {/* Master LLM Augmentation Switch */}
            <div className="p-3.5 rounded-xl border border-border bg-surface-hover/50 flex items-center justify-between gap-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-xs text-foreground">LLM Augmentation Mode</span>
                  <span
                    className={cn(
                      'px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase',
                      useLlm
                        ? 'bg-surface-selected text-foreground border border-border'
                        : 'bg-muted text-muted-foreground border border-border'
                    )}
                  >
                    {useLlm ? 'Enabled' : 'Offline / Fast'}
                  </span>
                </div>
                <p className="text-[10px] text-muted-foreground">
                  {useLlm
                    ? 'AI active for smart context merging, auto-classification, and note restructuring.'
                    : 'Deterministic fast mode: rule-based tagging, direct storage, zero API latency.'}
                </p>
              </div>

              <button
                type="button"
                onClick={handleToggleLlm}
                className={cn(
                  'relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                  useLlm ? 'bg-foreground' : 'bg-border'
                )}
              >
                <span
                  className={cn(
                    'pointer-events-none inline-block h-4 w-4 transform rounded-full bg-background shadow-md ring-0 transition duration-200 ease-in-out',
                    useLlm ? 'translate-x-5' : 'translate-x-0'
                  )}
                />
              </button>
            </div>

            {/* Active Model Selector */}
            <div className="space-y-1.5">
              <label className="text-[10px] text-muted-foreground block font-medium uppercase font-mono">
                Active Provider & Model:
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

            {/* Connection Tester */}
            <div className="flex items-center justify-between pt-2 border-t border-border/50">
              <div className="text-[10px] text-muted-foreground font-mono truncate max-w-[240px]">
                {testStatus ? (
                  <span className="text-foreground font-semibold">
                    {testStatus}
                  </span>
                ) : (
                  <span>Active: <strong>{selectedModel || 'Default'}</strong> ({selectedProvider === 'ollama' ? 'Ollama' : 'OpenAI'})</span>
                )}

              </div>

              <button
                type="button"
                onClick={handleTestChat}
                disabled={testLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-foreground text-background text-xs font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 shadow-xs shrink-0 cursor-pointer"
              >
                {testLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Server className="w-3.5 h-3.5" />}
                <span>Test Connection</span>
              </button>
            </div>
          </div>

          {/* Card 4: Discovered Models Inventory Side-by-Side Dual-Pane */}
          <div className="p-5 rounded-2xl bg-card border border-border shadow-xs space-y-3.5">
            <div className="flex items-center justify-between pb-2.5 border-b border-border/60">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-foreground" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                  Discovered Models Inventory
                </h3>
              </div>
              <span className="text-[10px] font-mono text-muted-foreground">
                {(ollamaData?.total_count || 0) + (openaiData?.total_count || 0)} Models Available
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              {/* Ollama Local Models */}
              <div className="p-3 rounded-xl bg-surface-hover/40 border border-border space-y-2">
                <div className="flex items-center justify-between text-[11px] font-bold text-foreground">
                  <div className="flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5" />
                    <span>Ollama ({ollamaData?.total_count || 0})</span>
                  </div>
                  <span className="text-[9px] font-mono text-muted-foreground font-normal">Local</span>
                </div>
                <div className="space-y-1 max-h-36 overflow-y-auto pr-1">
                  {(ollamaData?.all_models || []).length > 0 ? (
                    ollamaData!.all_models.map((m) => (
                      <div
                        key={m}
                        onClick={() => {
                          setSelectedProvider('ollama');
                          setSelectedModel(m);
                        }}
                        className={cn(
                          'px-2 py-1 rounded bg-surface-list font-mono text-[10px] border cursor-pointer hover:border-foreground transition-all flex items-center justify-between',
                          selectedProvider === 'ollama' && selectedModel === m ? 'border-foreground font-bold shadow-2xs' : 'border-border/50 text-foreground'
                        )}
                      >
                        <span className="truncate">{m}</span>
                        {selectedProvider === 'ollama' && selectedModel === m && <CheckCircle2 className="w-3 h-3 text-foreground shrink-0" />}
                      </div>
                    ))
                  ) : (
                    <p className="text-muted-foreground italic text-[10px]">No Ollama models found</p>
                  )}
                </div>
              </div>

              {/* OpenAI Remote Models */}
              <div className="p-3 rounded-xl bg-surface-hover/40 border border-border space-y-2">
                <div className="flex items-center justify-between text-[11px] font-bold text-foreground">
                  <div className="flex items-center gap-1.5">
                    <Brain className="w-3.5 h-3.5" />
                    <span>OpenAI ({openaiData?.total_count || 0})</span>
                  </div>
                  <span className="text-[9px] font-mono text-muted-foreground font-normal">Remote API</span>
                </div>
                <div className="space-y-1 max-h-36 overflow-y-auto pr-1">
                  {(openaiData?.all_models || []).length > 0 ? (
                    openaiData!.all_models.map((m) => (
                      <div
                        key={m}
                        onClick={() => {
                          setSelectedProvider('openai');
                          setSelectedModel(m);
                        }}
                        className={cn(
                          'px-2 py-1 rounded bg-surface-list font-mono text-[10px] border cursor-pointer hover:border-foreground transition-all flex items-center justify-between',
                          selectedProvider === 'openai' && selectedModel === m ? 'border-foreground font-bold shadow-2xs' : 'border-border/50 text-foreground'
                        )}
                      >
                        <span className="truncate">{m}</span>
                        {selectedProvider === 'openai' && selectedModel === m && <CheckCircle2 className="w-3 h-3 text-foreground shrink-0" />}
                      </div>
                    ))
                  ) : (
                    <p className="text-muted-foreground italic text-[10px]">No remote models found</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* =========================================================================
            GRID ROW 3: Dedicated Prompts Viewer (Full-Width Card)
           ========================================================================= */}
        <div className="p-5 rounded-2xl bg-card border border-border shadow-xs">
          <PromptsViewer />
        </div>

        {/* =========================================================================
            GRID ROW 4: Storage Health & Snapshots + MCP Tool Suite (2-Column Grid)
           ========================================================================= */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Card 5: Storage Integrity & Snapshots */}
          <div className="p-5 rounded-2xl bg-card border border-border shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-2.5 border-b border-border/60">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-foreground" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                  Storage Integrity & Snapshots
                </h3>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={handleRunAuditFix}
                  disabled={fixLoading}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-foreground text-background text-[10px] font-semibold hover:opacity-90 disabled:opacity-50 cursor-pointer shadow-2xs"
                >
                  {fixLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                  <span>Auto-Fix</span>
                </button>
                <button
                  onClick={handleCreateBackup}
                  disabled={backupLoading}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-surface-hover border border-border text-[10px] font-semibold hover:text-foreground cursor-pointer"
                >
                  {backupLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <HardDriveDownload className="w-3 h-3" />}
                  <span>Backup</span>
                </button>
              </div>
            </div>

            {backupMsg && (
              <p className={cn('text-[11px] font-mono', backupMsg.includes('success') ? 'text-foreground font-semibold' : 'text-rose-500')}>
                {backupMsg}
              </p>
            )}

            {/* 4 Stat Metric Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
              <div className="p-2.5 rounded-xl bg-surface-hover/60 border border-border">
                <span className="text-[9px] text-muted-foreground uppercase font-mono block">Files</span>
                <span className="text-base font-bold font-mono">{auditData?.total_files || 0}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-surface-hover/60 border border-border">
                <span className="text-[9px] text-muted-foreground uppercase font-mono block">SQLite</span>
                <span className="text-base font-bold font-mono">{auditData?.total_db_records || 0}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-surface-hover/60 border border-border">
                <span className="text-[9px] text-muted-foreground uppercase font-mono block">Vectors</span>
                <span className="text-base font-bold font-mono">{auditData?.total_vector_chunks || 0}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-surface-hover/60 border border-border">
                <span className="text-[9px] text-muted-foreground uppercase font-mono block">Status</span>
                <span className="text-base font-bold font-mono text-foreground">
                  {(auditData?.orphan_files_count || 0) === 0 ? 'Healthy' : `${auditData?.orphan_files_count} Issues`}
                </span>
              </div>
            </div>

            {/* System Specs Box */}
            <div className="p-3 rounded-xl bg-surface-hover/30 border border-border/70 text-[10px] text-muted-foreground font-mono space-y-1">
              <div className="flex items-center gap-1.5 text-foreground font-semibold">
                <Terminal className="w-3 h-3" />
                <span>Backend Specifications</span>
              </div>
              <p>• FastAPI Service: <code>http://localhost:6999</code></p>
              <p>• Database: <code>data/memorize.db</code></p>
              <p>• Vector Engine: <code>data/chroma_db</code> (persisted)</p>
            </div>
          </div>

          {/* Card 6: MCP Architecture & Parameters */}
          <div className="p-5 rounded-2xl bg-card border border-border shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-2.5 border-b border-border/60">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-foreground" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                  Universal MCP Server Suite
                </h3>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="px-2 py-0.5 rounded bg-surface-hover text-foreground border border-border font-mono text-[9px] font-bold">
                  Active (Port 7777)
                </span>
                <span className="px-2 py-0.5 rounded bg-surface-selected font-mono text-[9px] font-bold text-foreground">
                  12 Tools Active
                </span>
              </div>
            </div>

            {/* Quick Copy MCP Client Configurations */}
            <div className="p-3 rounded-xl bg-surface-hover/30 border border-border space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                1-Click MCP Client Configurations
              </span>
              <div className="flex flex-wrap items-center gap-1.5">
                <button
                  onClick={() =>
                    copyMcpConfig(
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
                      'claude'
                    )
                  }
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-surface-list hover:bg-surface-selected border border-border text-[10px] font-medium text-foreground cursor-pointer transition-colors"
                >
                  {mcpCopied === 'claude' ? <Check className="w-3 h-3 text-foreground" /> : <Copy className="w-3 h-3" />}
                  {mcpCopied === 'claude' ? 'Copied Claude Config' : 'Claude Desktop JSON'}
                </button>

                <button
                  onClick={() =>
                    copyMcpConfig(
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
                      'cursor'
                    )
                  }
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-surface-list hover:bg-surface-selected border border-border text-[10px] font-medium text-foreground cursor-pointer transition-colors"
                >
                  {mcpCopied === 'cursor' ? <Check className="w-3 h-3 text-foreground" /> : <Copy className="w-3 h-3" />}
                  {mcpCopied === 'cursor' ? 'Copied Cursor Config' : 'Cursor / Antigravity JSON'}
                </button>

                <button
                  onClick={() => copyMcpConfig('http://localhost:7777/sse', 'sse')}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-surface-list hover:bg-surface-selected border border-border text-[10px] font-medium text-foreground cursor-pointer transition-colors"
                >
                  {mcpCopied === 'sse' ? <Check className="w-3 h-3 text-foreground" /> : <Copy className="w-3 h-3" />}
                  {mcpCopied === 'sse' ? 'Copied SSE URL' : 'SSE URL (:7777/sse)'}
                </button>

              </div>
            </div>

            {/* MCP Model Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <div className="space-y-1">
                <label className="text-[9px] font-mono font-medium text-muted-foreground uppercase">
                  Embedding
                </label>
                <input
                  type="text"
                  value={embeddingModel}
                  onChange={(e) => setEmbeddingModel(e.target.value)}
                  placeholder="all-MiniLM-L6-v2"
                  className="w-full bg-surface-list border border-border rounded-lg px-2 py-1 text-[11px] font-mono text-foreground focus:ring-1 focus:ring-ring outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-mono font-medium text-muted-foreground uppercase">
                  Classification
                </label>
                <input
                  type="text"
                  value={classificationModel}
                  onChange={(e) => setClassificationModel(e.target.value)}
                  placeholder="gpt-oss:120b-cloud"
                  className="w-full bg-surface-list border border-border rounded-lg px-2 py-1 text-[11px] font-mono text-foreground focus:ring-1 focus:ring-ring outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-mono font-medium text-muted-foreground uppercase">
                  Fallback
                </label>
                <input
                  type="text"
                  value={fallbackModel}
                  onChange={(e) => setFallbackModel(e.target.value)}
                  placeholder="all-MiniLM-L6-v2"
                  className="w-full bg-surface-list border border-border rounded-lg px-2 py-1 text-[11px] font-mono text-foreground focus:ring-1 focus:ring-ring outline-none"
                />
              </div>
            </div>

            {/* 12 MCP Tool Badges */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 pt-1">
              {[
                { name: 'store', desc: 'Auto-categorizes & creates note' },
                { name: 'update', desc: 'Merges & smart-updates' },
                { name: 'delete', desc: 'Purges note from DB & vector' },
                { name: 'fetch', desc: 'Retrieves full note by ID' },
                { name: 'hybrid_fetch', desc: '50/30/20 weighted RAG' },
                { name: 'list_memories', desc: 'Lists memory summaries' },
                { name: 'get_categories', desc: '11 categories & note counts' },
                { name: 'merge_memories', desc: 'Consolidates multiple notes' },
                { name: 'find_correlated', desc: 'Discovers related memories' },
                { name: 'organize_memory', desc: 'AI polish with snapshots' },
                { name: 'generate_title', desc: 'Generates high-signal titles' },
                { name: 'organize_selection', desc: 'Transforms selected text' },
              ].map((t) => (
                <div key={t.name} className="p-2 rounded-lg bg-surface-list border border-border/60">
                  <span className="font-mono font-bold text-[10px] text-foreground block">⚡ {t.name}</span>
                  <span className="text-[9px] text-muted-foreground block truncate">{t.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* =========================================================================
            GRID ROW 5: Keyboard Shortcuts Reference (Full-Width Card)
           ========================================================================= */}
        <div className="p-5 rounded-2xl bg-card border border-border shadow-xs space-y-3.5">
          <div className="flex items-center justify-between pb-2.5 border-b border-border/60">
            <div className="flex items-center gap-2">
              <Keyboard className="w-4 h-4 text-foreground" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
                Keyboard Shortcuts Reference & Presets
              </h3>
            </div>
            <div className="flex items-center gap-1 bg-surface-hover p-0.5 rounded-lg border border-border">
              {(['standard', 'vim', 'compact'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setShortcutPreset(mode)}
                  className={cn(
                    'px-2.5 py-0.5 rounded capitalize text-[10px] font-medium transition-colors cursor-pointer',
                    shortcutPreset === mode
                      ? 'bg-card text-foreground font-semibold shadow-2xs'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {[
              { action: 'Save Note Immediately', key: '⌘ S', code: 'Cmd/Ctrl + S' },
              { action: 'Create New Note', key: '⌘ N', code: 'Cmd/Ctrl + N' },
              { action: 'Delete / Trash Active Note', key: '⌘ ⌫', code: 'Cmd/Ctrl + Backspace' },
              { action: 'Pin / Unpin Active Note', key: '⌘ ⇧ P', code: 'Cmd/Ctrl + Shift + P' },
              { action: 'Favorite / Star Active Note', key: '⌘ ⇧ S', code: 'Cmd/Ctrl + Shift + S' },
              { action: 'Global Hybrid Search', key: '⌘ K', code: 'Cmd/Ctrl + K' },
              { action: 'Open Full Settings View', key: '⌘ ,', code: 'Cmd/Ctrl + ,' },
              { action: 'Zen Focus Distraction-Free', key: '⌘ ⇧ Z', code: 'Cmd/Ctrl + Shift + Z' },
              { action: 'Exit View / Back to Notes', key: 'Esc', code: 'Escape' },
            ].map((item, idx) => (
              <div
                key={idx}
                className="px-3 py-2 rounded-lg bg-surface-hover/40 border border-border/70 flex items-center justify-between text-[11px]"
              >
                <div className="truncate mr-2">
                  <span className="font-semibold text-foreground block truncate">{item.action}</span>
                  <span className="text-[10px] text-muted-foreground font-mono">{item.code}</span>
                </div>
                <kbd className="px-2 py-0.5 rounded bg-surface-selected border border-border font-mono text-[10px] font-bold shrink-0">
                  {item.key}
                </kbd>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
