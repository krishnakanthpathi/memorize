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
} from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { useNotesStore } from '@/store/useNotesStore';
import { api } from '@/services/api';
import { ModelsResponse } from '@/types';
import { cn } from '@/lib/utils';

export const SettingsModal: React.FC = () => {
  const {
    activeModal,
    setActiveModal,
    theme,
    setTheme,
    selectedModel,
    selectedProvider,
    setSelectedModel,
    setSelectedProvider,
  } = useNotesStore();

  const isOpen = activeModal === 'settings' || activeModal === 'models';
  const [modelsData, setModelsData] = useState<ModelsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [testStatus, setTestStatus] = useState<string | null>(null);
  const [testLoading, setTestLoading] = useState(false);

  const loadModels = async (prov = selectedProvider) => {
    setLoading(true);
    try {
      const data = await api.getModels(prov);
      setModelsData(data);
      const available = data.all_models || [];
      if (!selectedModel || !available.includes(selectedModel)) {
        const defaultMod = data.current_default || (data.fast_models && data.fast_models[0]) || available[0] || '';
        if (defaultMod) {
          setSelectedModel(defaultMod);
        }
      }
    } catch (err) {
      console.error('Failed to load models:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadModels(selectedProvider);
      setTestStatus(null);
    }
  }, [isOpen, selectedProvider]);

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

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && setActiveModal(null)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl bg-card text-card-foreground border border-border rounded-xl shadow-2xl z-50 p-0 overflow-hidden flex flex-col h-[80vh] animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="h-14 px-6 border-b border-border flex items-center justify-between bg-surface-sidebar select-none">
            <div className="flex items-center gap-2.5">
              <Settings className="w-5 h-5 text-foreground" />
              <div>
                <h3 className="text-sm font-bold leading-tight">Preferences & Model Engine</h3>
                <p className="text-[10px] text-muted-foreground font-mono">
                  Configure appearance, isolated LLM providers, and tools integration
                </p>
              </div>
            </div>

            <Dialog.Close asChild>
              <button className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors">
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs">
            {/* Theme Configuration */}
            <div>
              <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block mb-2.5 flex items-center gap-1.5">
                <Palette className="w-3.5 h-3.5 text-foreground" />
                Monochrome Appearance Modes
              </label>

              <div className="grid grid-cols-3 gap-3">
                <div
                  onClick={() => setTheme('light')}
                  className={cn(
                    'p-3.5 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2',
                    theme === 'light'
                      ? 'border-foreground bg-white text-zinc-900 shadow-md font-bold'
                      : 'border-border bg-surface-hover text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Sun className="w-5 h-5 text-amber-600" />
                  <div>
                    <span className="block text-xs">Light Mode</span>
                    <span className="text-[10px] opacity-70">Crisp White</span>
                  </div>
                </div>

                <div
                  onClick={() => setTheme('dark')}
                  className={cn(
                    'p-3.5 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2',
                    theme === 'dark'
                      ? 'border-foreground bg-zinc-900 text-white shadow-md font-bold'
                      : 'border-border bg-surface-hover text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Moon className="w-5 h-5 text-zinc-300" />
                  <div>
                    <span className="block text-xs">Dark Mode</span>
                    <span className="text-[10px] opacity-70">Slate Zinc (Default)</span>
                  </div>
                </div>

                <div
                  onClick={() => setTheme('black')}
                  className={cn(
                    'p-3.5 rounded-xl border cursor-pointer transition-all flex flex-col items-center justify-center text-center gap-2',
                    theme === 'black'
                      ? 'border-zinc-500 bg-black text-white shadow-md font-bold'
                      : 'border-border bg-surface-hover text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Zap className="w-5 h-5 text-white" />
                  <div>
                    <span className="block text-xs">Pitch Black</span>
                    <span className="text-[10px] opacity-70">OLED Monochrome</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Provider & Model Selection */}
            <div className="space-y-3 pt-2 border-t border-border">
              <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-foreground" />
                Active LLM Provider & Model
              </label>

              <div className="p-4 rounded-xl bg-surface-hover/50 border border-border space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Provider Selector */}
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1.5 font-medium">
                      LLM Provider:
                    </label>
                    <select
                      value={selectedProvider}
                      onChange={(e) => {
                        const newProv = e.target.value;
                        setSelectedProvider(newProv);
                        loadModels(newProv);
                      }}
                      className="w-full bg-surface-list border border-border rounded-lg px-3 py-2 text-xs font-mono outline-none focus:ring-1 focus:ring-ring text-foreground"
                    >
                      <option value="ollama">Ollama (Local • http://localhost:11434)</option>
                      <option value="openai">OpenAI Compatible (Remote API / Bedrock)</option>
                    </select>
                  </div>

                  {/* Model Selector */}
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1.5 font-medium">
                      Active Model ({selectedProvider === 'ollama' ? 'Ollama' : 'OpenAI'}):
                    </label>
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full bg-surface-list border border-border rounded-lg px-3 py-2 text-xs font-mono outline-none focus:ring-1 focus:ring-ring text-foreground"
                    >
                      <option value="">Default Provider Model</option>
                      {modelsData?.fast_models && modelsData.fast_models.length > 0 && (
                        <optgroup label="⚡ Fast Tier Models">
                          {modelsData.fast_models.map((m) => (
                            <option key={m} value={m}>
                              ⚡ {m}
                            </option>
                          ))}
                        </optgroup>
                      )}
                      {modelsData?.reasoning_models && modelsData.reasoning_models.length > 0 && (
                        <optgroup label="🧠 Reasoning Tier Models">
                          {modelsData.reasoning_models.map((m) => (
                            <option key={m} value={m}>
                              🧠 {m}
                            </option>
                          ))}
                        </optgroup>
                      )}
                      {modelsData?.all_models &&
                        modelsData.all_models.map((m) => {
                          const inFast = modelsData.fast_models?.includes(m);
                          const inReasoning = modelsData.reasoning_models?.includes(m);
                          if (inFast || inReasoning) return null;
                          return (
                            <option key={m} value={m}>
                              • {m}
                            </option>
                          );
                        })}
                    </select>
                  </div>
                </div>

                {/* Test Connection */}
                <div className="flex items-center justify-between pt-2 border-t border-border/60">
                  <div className="text-[11px] text-muted-foreground font-mono truncate max-w-xs">
                    {testStatus ? (
                      <span className={cn(testStatus.startsWith('Connected') ? 'text-emerald-500 font-semibold' : 'text-rose-500')}>
                        {testStatus}
                      </span>
                    ) : (
                      <span>Active: {selectedModel || 'Default Model'} ({selectedProvider === 'ollama' ? 'Ollama' : 'OpenAI'})</span>
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
            </div>

            {/* Discovered Models Inventory */}
            <div className="space-y-3 pt-2 border-t border-border">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-foreground" />
                  {selectedProvider === 'ollama' ? 'Ollama' : 'OpenAI Remote'} Models ({modelsData?.total_count || 0} Available)
                </label>
                <button
                  onClick={() => loadModels(selectedProvider)}
                  className="text-[11px] text-muted-foreground hover:text-foreground underline"
                >
                  Re-scan
                </button>
              </div>

              {loading ? (
                <div className="py-8 text-center text-muted-foreground">
                  <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                  <span>Loading available models...</span>
                </div>
              ) : modelsData ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {/* Fast Models */}
                  <div className="p-3 rounded-lg bg-surface-hover/60 border border-border">
                    <div className="flex items-center gap-1.5 font-bold mb-2 text-foreground">
                      <Zap className="w-3.5 h-3.5 text-foreground" />
                      <span>Fast Tier Models ({modelsData.fast_models?.length || 0})</span>
                    </div>
                    <div className="space-y-1 max-h-36 overflow-y-auto">
                      {(modelsData.fast_models || []).length > 0 ? (
                        modelsData.fast_models.map((m) => (
                          <div
                            key={m}
                            onClick={() => setSelectedModel(m)}
                            className={cn(
                              "px-2 py-1 rounded bg-surface-list font-mono text-[11px] border cursor-pointer hover:border-foreground transition-all flex items-center justify-between",
                              selectedModel === m ? "border-foreground font-bold shadow-xs" : "border-border/50 text-foreground"
                            )}
                          >
                            <span className="truncate">{m}</span>
                            {selectedModel === m && <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />}
                          </div>
                        ))
                      ) : (
                        <p className="text-muted-foreground italic text-[11px]">
                          No fast models detected
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Reasoning Models */}
                  <div className="p-3 rounded-lg bg-surface-hover/60 border border-border">
                    <div className="flex items-center gap-1.5 font-bold mb-2 text-foreground">
                      <Brain className="w-3.5 h-3.5 text-foreground" />
                      <span>Reasoning Tier Models ({modelsData.reasoning_models?.length || 0})</span>
                    </div>
                    <div className="space-y-1 max-h-36 overflow-y-auto">
                      {(modelsData.reasoning_models || []).length > 0 ? (
                        modelsData.reasoning_models.map((m) => (
                          <div
                            key={m}
                            onClick={() => setSelectedModel(m)}
                            className={cn(
                              "px-2 py-1 rounded bg-surface-list font-mono text-[11px] border cursor-pointer hover:border-foreground transition-all flex items-center justify-between",
                              selectedModel === m ? "border-foreground font-bold shadow-xs" : "border-border/50 text-foreground"
                            )}
                          >
                            <span className="truncate">{m}</span>
                            {selectedModel === m && <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />}
                          </div>
                        ))
                      ) : (
                        <p className="text-muted-foreground italic text-[11px]">
                          No reasoning models detected
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>

            {/* System Info */}
            <div className="pt-2 border-t border-border">
              <div className="p-3 rounded-lg bg-surface-hover/40 border border-border text-[11px] text-muted-foreground font-mono space-y-1">
                <div className="flex items-center gap-1.5 text-foreground font-bold">
                  <Terminal className="w-3.5 h-3.5" />
                  <span>Architecture & Tool Integrations</span>
                </div>
                <p>• Backend: FastAPI Local Service (port 6999)</p>
                <p>• Storage: SQLite database + ChromaDB vector embeddings</p>
                <p>• Tool Calls: create_memory, search_memories, read_memory, delete_memory</p>
              </div>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
