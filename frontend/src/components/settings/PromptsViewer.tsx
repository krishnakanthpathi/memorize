import React, { useState, useEffect, useMemo } from 'react';
import {
  Sparkles,
  Search,
  Copy,
  Check,
  Brain,
  Layers,
  FileEdit,
  Tag,
  FileText,
  Code2,
  Info,
  Hash,
  Terminal,
} from 'lucide-react';
import { PromptsMap, PromptItem } from '@/types';
import { api } from '@/services/api';
import { cn } from '@/lib/utils';

interface PromptMeta {
  category: 'merge' | 'organize' | 'metadata' | 'classify' | 'summary';
  categoryLabel: string;
  badge: string;
  badgeColor: string;
  icon: React.ElementType;
  variables: string[];
}

const PROMPT_METADATA_MAP: Record<string, PromptMeta> = {
  smart_merge: {
    category: 'merge',
    categoryLabel: 'Memory Merging',
    badge: 'Smart Merge',
    badgeColor: 'text-foreground bg-surface-hover border-border',
    icon: Layers,
    variables: ['existing_content', 'new_content', 'instructions'],
  },
  multi_merge: {
    category: 'merge',
    categoryLabel: 'Memory Merging',
    badge: 'Multi-Document',
    badgeColor: 'text-foreground bg-surface-hover border-border',
    icon: Brain,
    variables: ['source_notes', 'target_title', 'custom_instructions'],
  },
  organize: {
    category: 'organize',
    categoryLabel: 'Document Editing',
    badge: 'Restructure & Polish',
    badgeColor: 'text-foreground bg-surface-hover border-border',
    icon: FileEdit,
    variables: ['content', 'instruction', 'generate_title'],
  },
  generate_title: {
    category: 'metadata',
    categoryLabel: 'Metadata & Titles',
    badge: 'Title Architect',
    badgeColor: 'text-foreground bg-surface-hover border-border',
    icon: Hash,
    variables: ['content', 'current_title', 'instruction'],
  },
  organize_selection: {
    category: 'organize',
    categoryLabel: 'Document Editing',
    badge: 'Selection Transform',
    badgeColor: 'text-foreground bg-surface-hover border-border',
    icon: FileText,
    variables: ['selected_text', 'mode', 'full_context'],
  },
  auto_classify: {
    category: 'classify',
    categoryLabel: 'Classification',
    badge: 'JSON Tagging',
    badgeColor: 'text-foreground bg-surface-hover border-border',
    icon: Tag,
    variables: ['content', 'allowed_categories'],
  },
  summary: {
    category: 'summary',
    categoryLabel: 'Summaries',
    badge: 'Executive Summary',
    badgeColor: 'text-foreground bg-surface-hover border-border',
    icon: Terminal,
    variables: ['text', 'max_sentences'],
  },
};

export const PromptsViewer: React.FC = () => {
  const [prompts, setPrompts] = useState<PromptsMap>({});
  const [selectedKey, setSelectedKey] = useState<string>('smart_merge');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [copied, setCopied] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const fetchPrompts = async () => {
      setLoading(true);
      try {
        const data = await api.getPrompts();
        if (isMounted && data) {
          setPrompts(data);
          const keys = Object.keys(data);
          if (keys.length > 0 && !keys.includes(selectedKey)) {
            setSelectedKey(keys[0]);
          }
        }
      } catch (e) {
        console.error('Failed to load prompts:', e);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchPrompts();
    return () => {
      isMounted = false;
    };
  }, []);

  const categories = [
    { id: 'all', label: 'All Directives' },
    { id: 'merge', label: 'Memory Merging' },
    { id: 'organize', label: 'Document Editing' },
    { id: 'metadata', label: 'Metadata & Titles' },
    { id: 'classify', label: 'Classification' },
  ];

  const filteredKeys = useMemo(() => {
    return Object.keys(prompts).filter((key) => {
      const p = prompts[key];
      const meta = PROMPT_METADATA_MAP[key];
      const matchesSearch =
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.template.toLowerCase().includes(searchQuery.toLowerCase()) ||
        key.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesCat =
        selectedCategory === 'all' ||
        (meta && meta.category === selectedCategory);

      return matchesSearch && matchesCat;
    });
  }, [prompts, searchQuery, selectedCategory]);

  const activePrompt: PromptItem | undefined = prompts[selectedKey] || (filteredKeys.length > 0 ? prompts[filteredKeys[0]] : undefined);
  const activeMeta = PROMPT_METADATA_MAP[selectedKey] || {
    category: 'merge',
    categoryLabel: 'Directive',
    badge: 'AI Directive',
    badgeColor: 'text-foreground/80 bg-surface-hover border-border',
    icon: Sparkles,
    variables: ['context', 'instruction'],
  };

  const handleCopy = () => {
    if (!activePrompt) return;
    navigator.clipboard.writeText(activePrompt.template);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const linesCount = useMemo(() => {
    if (!activePrompt?.template) return 0;
    return activePrompt.template.split('\n').length;
  }, [activePrompt]);

  const wordsCount = useMemo(() => {
    if (!activePrompt?.template) return 0;
    return activePrompt.template.trim().split(/\s+/).filter(Boolean).length;
  }, [activePrompt]);

  const estTokens = useMemo(() => {
    if (!activePrompt?.template) return 0;
    return Math.ceil(activePrompt.template.length / 4);
  }, [activePrompt]);

  return (
    <div className="space-y-4">
      {/* Header with Search and Category Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-border/60">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-surface-selected border border-border/80 text-foreground">
            <Code2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-foreground">
              AI System Prompts & Instruction Templates
            </h3>
            <p className="text-[10px] text-muted-foreground font-mono">
              Live prompt directives utilized for RAG merging, note organization, classification, and metadata extraction
            </p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative min-w-[200px] sm:w-64">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search prompt templates..."
            className="w-full bg-surface-list border border-border rounded-lg pl-8 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/70 outline-none focus:ring-1 focus:ring-ring font-mono"
          />
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
        {categories.map((c) => (
          <button
            key={c.id}
            onClick={() => setSelectedCategory(c.id)}
            className={cn(
              'px-2.5 py-1 rounded-md text-[11px] font-medium transition-all shrink-0 cursor-pointer',
              selectedCategory === c.id
                ? 'bg-foreground text-background font-semibold shadow-xs'
                : 'bg-surface-hover/70 text-muted-foreground hover:text-foreground hover:bg-surface-hover'
            )}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Main Dual-Pane Viewer */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3.5 items-start">
        {/* Left Column: Prompts List */}
        <div className="md:col-span-4 space-y-1.5 max-h-[380px] overflow-y-auto pr-1">
          {loading ? (
            <div className="p-4 rounded-lg bg-surface-hover/40 border border-border text-center text-xs text-muted-foreground">
              Loading prompt directives...
            </div>
          ) : filteredKeys.length === 0 ? (
            <div className="p-4 rounded-lg bg-surface-hover/40 border border-border text-center text-xs text-muted-foreground">
              No matching prompt directives found
            </div>
          ) : (
            filteredKeys.map((key) => {
              const p = prompts[key];
              const meta = PROMPT_METADATA_MAP[key];
              const IconComp = meta?.icon || Sparkles;
              const isSelected = (activePrompt && activePrompt.name === p.name) || selectedKey === key;

              return (
                <div
                  key={key}
                  onClick={() => setSelectedKey(key)}
                  className={cn(
                    'p-2.5 rounded-lg border cursor-pointer transition-all flex flex-col gap-1',
                    isSelected
                      ? 'border-foreground bg-surface-selected text-foreground font-semibold shadow-xs ring-1 ring-foreground/20'
                      : 'border-border/60 bg-surface-hover/40 text-muted-foreground hover:text-foreground hover:bg-surface-hover'
                  )}
                >
                  <div className="flex items-center justify-between gap-1.5">
                    <div className="flex items-center gap-1.5 truncate">
                      <IconComp className={cn('w-3.5 h-3.5 shrink-0', isSelected ? 'text-foreground' : 'text-muted-foreground')} />
                      <span className="text-xs truncate font-medium">{p.name}</span>
                    </div>
                    {meta?.badge && (
                      <span
                        className={cn(
                          'text-[9px] font-mono px-1.5 py-0.2 rounded border shrink-0',
                          meta.badgeColor
                        )}
                      >
                        {meta.badge}
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-muted-foreground line-clamp-1 opacity-80">
                    {p.description}
                  </p>
                </div>
              );
            })
          )}
        </div>

        {/* Right Column: Prompt Detail & Code View */}
        <div className="md:col-span-8 p-4 rounded-xl bg-surface-hover/50 border border-border space-y-3">
          {activePrompt ? (
            <>
              {/* Directive Header & Copy Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-border/60">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-xs font-bold text-foreground">{activePrompt.name}</h4>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-list border border-border text-muted-foreground">
                      key: {selectedKey}
                    </span>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    {activePrompt.description}
                  </p>
                </div>

                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-list border border-border/80 text-foreground text-xs font-semibold hover:bg-surface-selected transition-all shrink-0 cursor-pointer shadow-2xs"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-foreground" />
                      <span className="text-foreground">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Template</span>
                    </>
                  )}
                </button>
              </div>

              {/* Variable Placeholders Badges */}
              {activeMeta.variables && activeMeta.variables.length > 0 && (
                <div className="flex items-center gap-1.5 flex-wrap text-[10px]">
                  <span className="text-muted-foreground font-mono font-medium flex items-center gap-1">
                    <Info className="w-3 h-3" />
                    Input Parameters:
                  </span>
                  {activeMeta.variables.map((v) => (
                    <span
                      key={v}
                      className="px-2 py-0.5 rounded-full bg-surface-list border border-border/70 font-mono text-muted-foreground"
                    >
                      {`{${v}}`}
                    </span>
                  ))}
                </div>
              )}

              {/* Template Code Viewer */}
              <div className="relative rounded-lg bg-surface-list border border-border/80 overflow-hidden">
                <div className="flex items-center justify-between px-3 py-1.5 bg-surface-hover/80 border-b border-border/60 text-[10px] font-mono text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-foreground/70" />
                    <span>SYSTEM INSTRUCTION DIRECTIVE</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span>{linesCount} lines</span>
                    <span>{wordsCount} words</span>
                    <span className="text-foreground font-bold">~{estTokens} tokens</span>
                  </div>
                </div>

                <pre className="p-3.5 max-h-64 overflow-y-auto font-mono text-[11px] text-foreground leading-relaxed whitespace-pre-wrap select-text">
                  {activePrompt.template}
                </pre>
              </div>
            </>
          ) : (
            <div className="py-12 text-center text-xs text-muted-foreground">
              Select a prompt directive to view its template
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
