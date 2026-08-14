import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Send,
  X,
  Sparkles,
  Loader2,
  FileText,
  RotateCcw,
  Wrench,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';
import { api } from '@/services/api';
import { ChatMessage } from '@/types';
import { cn } from '@/lib/utils';

export const CompanionChatDrawer: React.FC = () => {
  const {
    activeModal,
    setActiveModal,
    selectNote,
    selectedModel,
    selectedProvider,
    setSelectedModel,
    setSelectedProvider,
    fetchNotes,
    fetchCategories,
  } = useNotesStore();

  const isOpen = activeModal === 'chat';
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hello! I am your AI Memory Companion. You can ask me questions about your notes, or ask me to create, search, or manage memories directly (e.g. 'Remember that I started learning Rust today').",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [openaiModels, setOpenaiModels] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadAllDrawerModels = async () => {
    try {
      const [ollamaRes, openaiRes] = await Promise.all([
        api.getModels('ollama').catch(() => null),
        api.getModels('openai').catch(() => null),
      ]);
      setOllamaModels(ollamaRes?.all_models || []);
      setOpenaiModels(openaiRes?.all_models || []);

      if (!selectedModel) {
        if (ollamaRes?.all_models && ollamaRes.all_models.length > 0) {
          setSelectedModel(ollamaRes.all_models[0]);
          setSelectedProvider('ollama');
        } else if (openaiRes?.all_models && openaiRes.all_models.length > 0) {
          setSelectedModel(openaiRes.all_models[0]);
          setSelectedProvider('openai');
        }
      }
    } catch (e) {
      console.error('Failed to load drawer models:', e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadAllDrawerModels();
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.sendChatMessage(userText, selectedModel || undefined, selectedProvider || undefined);
      const botMsg: ChatMessage = {
        id: `bot_${Date.now()}`,
        role: 'assistant',
        content: res.reply,
        toolExecuted: res.tool_executed,
        memoriesUsed: res.memories_used,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: selectedModel,
      };
      setMessages((prev) => [...prev, botMsg]);

      // If a tool modified memories (create, delete, purge), refresh UI data
      if (res.tool_executed && ['create_memory', 'store_memory', 'delete_memory', 'clear_all_memories'].includes(res.tool_executed.tool)) {
        await fetchNotes();
        await fetchCategories();
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error communicating with ${selectedModel || 'LLM'}: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Chat history cleared. How can I assist you with your knowledge base today?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  // Close when Escape key is pressed
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setActiveModal(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, setActiveModal]);

  if (!isOpen) return null;

  return (
    <div
      onClick={() => setActiveModal(null)}
      className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs animate-in fade-in"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md h-full bg-card text-card-foreground border-l border-border shadow-2xl flex flex-col animate-in slide-in-from-right duration-200"
      >
        {/* Header */}
        <div className="h-14 px-4 border-b border-border flex items-center justify-between bg-surface-sidebar select-none">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-foreground" />
            <div>
              <h3 className="text-xs font-bold leading-tight">AI Companion & Tools</h3>
              <p className="text-[10px] text-muted-foreground font-mono">
                RAG Context & Automated Tool Invocation
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={handleClear}
              title="Clear chat"
              className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setActiveModal(null)}
              className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Unified Merged Model Selector Bar */}
        <div className="px-4 py-2 bg-surface-hover/60 border-b border-border text-xs flex items-center justify-between gap-2">
          <span className="text-[11px] text-muted-foreground font-mono shrink-0">Active Model:</span>
          <select
            value={`${selectedProvider}::${selectedModel}`}
            onChange={(e) => {
              const [prov, mod] = e.target.value.split('::');
              setSelectedProvider(prov);
              setSelectedModel(mod);
            }}
            className="bg-surface-selected border border-border/80 rounded px-2 py-1 text-[11px] font-mono outline-none focus:ring-1 focus:ring-ring text-foreground flex-1 truncate"
          >
            {ollamaModels.length > 0 && (
              <optgroup label="🦙 Ollama Local Models">
                {ollamaModels.map((m) => (
                  <option key={`ollama::${m}`} value={`ollama::${m}`}>
                    [Ollama] {m}
                  </option>
                ))}
              </optgroup>
            )}
            {openaiModels.length > 0 && (
              <optgroup label="🌐 OpenAI Remote Models">
                {openaiModels.map((m) => (
                  <option key={`openai::${m}`} value={`openai::${m}`}>
                    [OpenAI] {m}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                'flex flex-col',
                msg.role === 'user' ? 'items-end' : 'items-start'
              )}
            >
              <div className="flex items-center gap-1.5 mb-1 px-1 text-[10px] text-muted-foreground font-mono">
                {msg.role === 'assistant' ? (
                  <>
                    <Sparkles className="w-3 h-3 text-foreground" />
                    <span>AI Assistant ({selectedModel || 'active'})</span>
                  </>
                ) : (
                  <span>You</span>
                )}
                <span>• {msg.timestamp}</span>
              </div>

              <div
                className={cn(
                  'rounded-xl p-3.5 max-w-[88%] leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-foreground text-background font-medium'
                    : 'bg-surface-hover/80 text-foreground border border-border shadow-xs'
                )}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>

                {/* Tool Execution Tag badge */}
                {msg.toolExecuted && (
                  <div className="mt-2.5 pt-2 border-t border-border/40 flex items-center gap-1.5 text-[11px] font-mono text-emerald-500">
                    <Wrench className="w-3 h-3 shrink-0" />
                    <span>
                      Executed: <strong>{msg.toolExecuted.tool}</strong>
                    </span>
                  </div>
                )}

                {/* Memories RAG Used List */}
                {msg.memoriesUsed && msg.memoriesUsed.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-border/40 space-y-1">
                    <span className="text-[10px] text-muted-foreground font-mono flex items-center gap-1">
                      <Layers className="w-3 h-3" /> Context Memories Retrieved:
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {msg.memoriesUsed.map((mem) => (
                        <button
                          key={mem.id}
                          onClick={() => selectNote(mem.id)}
                          className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-selected hover:bg-surface-hover text-[10px] font-mono text-foreground border border-border transition-colors"
                        >
                          <FileText className="w-2.5 h-2.5" />
                          <span>{mem.title}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-muted-foreground p-2">
              <Loader2 className="w-4 h-4 animate-spin text-foreground" />
              <span className="text-xs font-mono">
                Consulting memories & generating response...
              </span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Footer */}
        <form onSubmit={handleSend} className="p-3 border-t border-border bg-surface-sidebar">
          <div className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about memories or tell me to remember something..."
              disabled={loading}
              className="w-full bg-surface-hover border border-border rounded-xl pl-3.5 pr-10 py-2.5 text-xs outline-none focus:ring-1 focus:ring-ring text-foreground placeholder:text-muted-foreground"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="absolute right-1.5 p-1.5 rounded-lg bg-foreground text-background hover:opacity-90 disabled:opacity-30 transition-opacity"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
