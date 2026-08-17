import React, { useEffect, useMemo, useState } from 'react';
import {
  Combine,
  X,
  Plus,
  Trash2,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  FileText,
  Tag,
  Folder,
  Layers,
  ArrowRight,
  RefreshCw,
  Search,
} from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import * as Tabs from '@radix-ui/react-tabs';
import { useNotesStore } from '@/store/useNotesStore';
import { api } from '@/services/api';
import { CorrelationItem, Note } from '@/types';
import { cn } from '@/lib/utils';

export const MergeMemoriesModal: React.FC = () => {
  const {
    activeModal,
    setActiveModal,
    notes,
    categories,
    selectedNoteIds,
    toggleNoteSelection,
    clearNoteSelection,
    fetchNotes,
    selectNote,
  } = useNotesStore();

  const isOpen = activeModal === 'merge';

  const [activeTab, setActiveTab] = useState<'selected' | 'suggested'>('selected');
  const [targetTitle, setTargetTitle] = useState('');
  const [targetCategory, setTargetCategory] = useState('personal');
  const [targetTags, setTargetTags] = useState<string[]>([]);
  const [newTagInput, setNewTagInput] = useState('');
  const [instruction, setInstruction] = useState('');
  const [useAi, setUseAi] = useState(true);
  const [deleteSources, setDeleteSources] = useState(true);

  const [isMerging, setIsMerging] = useState(false);
  const [mergeResult, setMergeResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  // Correlated recommendations state
  const [correlatedList, setCorrelatedList] = useState<CorrelationItem[]>([]);
  const [isLoadingCorrelated, setIsLoadingCorrelated] = useState(false);

  // Selected note objects
  const selectedNotes = useMemo(() => {
    return selectedNoteIds
      .map((id) => notes.find((n) => n.id === id))
      .filter(Boolean) as Note[];
  }, [selectedNoteIds, notes]);

  // Sync initial metadata when modal opens or selection changes
  useEffect(() => {
    if (isOpen && selectedNotes.length > 0 && !mergeResult) {
      const primary = selectedNotes[0];
      setTargetTitle(primary.title || 'Consolidated Note');
      setTargetCategory(primary.category || 'personal');
      
      const allTags = new Set<string>();
      selectedNotes.forEach((n) => {
        (n.tags || []).forEach((t) => allTags.add(t));
      });
      setTargetTags(Array.from(allTags));
      setErrorMsg('');

      // Fetch correlated memories for the primary note
      if (primary.id) {
        setIsLoadingCorrelated(true);
        api.getCorrelatedMemories(primary.id, 6)
          .then((items) => {
            // Exclude already selected
            const filtered = items.filter((c) => !selectedNoteIds.includes(c.id));
            setCorrelatedList(filtered);
          })
          .catch((err) => {
            console.error('Failed to load correlations:', err);
          })
          .finally(() => setIsLoadingCorrelated(false));
      }
    }
  }, [isOpen, selectedNoteIds.length]);

  const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && newTagInput.trim()) {
      e.preventDefault();
      const clean = newTagInput.trim().replace(/^#/, '');
      if (!targetTags.includes(clean)) {
        setTargetTags([...targetTags, clean]);
      }
      setNewTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTargetTags(targetTags.filter((t) => t !== tagToRemove));
  };

  const handleAddCorrelated = (item: CorrelationItem) => {
    if (!selectedNoteIds.includes(item.id)) {
      toggleNoteSelection(item.id);
      setCorrelatedList((prev) => prev.filter((c) => c.id !== item.id));
    }
  };

  const handleExecuteMerge = async () => {
    if (selectedNoteIds.length < 2) {
      setErrorMsg('Please select at least 2 notes to merge.');
      return;
    }

    setIsMerging(true);
    setErrorMsg('');
    try {
      const res = await api.mergeMemories({
        memory_ids: selectedNoteIds,
        target_title: targetTitle.trim() || undefined,
        target_category: targetCategory || undefined,
        target_tags: targetTags,
        delete_sources: deleteSources,
        instruction: instruction.trim() || undefined,
        use_ai: useAi,
      });

      setMergeResult(res);
      await fetchNotes();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to merge memories.');
    } finally {
      setIsMerging(false);
    }
  };

  const handleDone = () => {
    if (mergeResult?.merged_memory_id) {
      selectNote(mergeResult.merged_memory_id);
    }
    clearNoteSelection();
    setMergeResult(null);
    setActiveModal(null);
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && handleDone()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-4xl bg-card text-card-foreground border border-border rounded-2xl shadow-2xl z-50 p-0 overflow-hidden flex flex-col h-[85vh] animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="h-14 px-6 border-b border-border flex items-center justify-between bg-surface-sidebar select-none">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-foreground text-background flex items-center justify-center">
                <Combine className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                  <span>LLM Multi-Memory Merge</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground">
                    Context-Safe
                  </span>
                </h3>
                <p className="text-[10px] text-muted-foreground">
                  Synthesize and consolidate multiple correlated notes into a single cohesive document
                </p>
              </div>
            </div>

            <Dialog.Close asChild>
              <button
                onClick={handleDone}
                className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>

          {/* Success Banner */}
          {mergeResult && (
            <div className="px-6 py-2.5 bg-emerald-500/10 border-b border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center justify-between font-medium">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>
                  Successfully merged {mergeResult.merged_source_count} notes into "{mergeResult.title}"!
                </span>
              </div>
              <button
                onClick={handleDone}
                className="px-3 py-1 rounded-md bg-emerald-600 text-white font-semibold text-xs hover:bg-emerald-700 transition-colors shadow-xs"
              >
                Open Merged Note
              </button>
            </div>
          )}

          {/* Error Banner */}
          {errorMsg && (
            <div className="px-6 py-2 bg-destructive/10 border-b border-destructive/20 text-destructive text-xs flex items-center gap-2 font-medium">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* 2-Column Main Workspace */}
          <div className="flex-1 flex overflow-hidden">
            {/* Left Column: Source Notes & Correlation Recommendations */}
            <div className="w-80 border-r border-border flex flex-col bg-surface-list overflow-hidden">
              <Tabs.Root
                value={activeTab}
                onValueChange={(val) => setActiveTab(val as any)}
                className="flex-1 flex flex-col overflow-hidden"
              >
                <div className="p-2 border-b border-border bg-surface-sidebar flex items-center gap-1 select-none">
                  <Tabs.List className="grid grid-cols-2 w-full bg-surface-hover p-0.5 rounded-lg text-xs">
                    <Tabs.Trigger
                      value="selected"
                      className="px-2 py-1 rounded-md text-[11px] font-semibold data-[state=active]:bg-card data-[state=active]:text-foreground text-muted-foreground transition-all"
                    >
                      Selected ({selectedNotes.length})
                    </Tabs.Trigger>
                    <Tabs.Trigger
                      value="suggested"
                      className="px-2 py-1 rounded-md text-[11px] font-semibold data-[state=active]:bg-card data-[state=active]:text-foreground text-muted-foreground transition-all flex items-center justify-center gap-1"
                    >
                      <Sparkles className="w-3 h-3 text-violet-500" />
                      <span>Related ({correlatedList.length})</span>
                    </Tabs.Trigger>
                  </Tabs.List>
                </div>

                {/* Selected Notes Tab Content */}
                <Tabs.Content value="selected" className="flex-1 overflow-y-auto p-2 space-y-2 outline-none">
                  {selectedNotes.length === 0 ? (
                    <div className="p-8 text-center text-muted-foreground text-xs">
                      No notes selected. Click on notes in your list or add suggested notes from the Related tab.
                    </div>
                  ) : (
                    selectedNotes.map((note, index) => (
                      <div
                        key={note.id}
                        className="p-3 rounded-xl bg-card border border-border/80 text-xs space-y-1.5 shadow-xs relative group"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-1.5 truncate">
                            <span className="w-4 h-4 rounded-full bg-muted text-muted-foreground text-[10px] font-mono flex items-center justify-center shrink-0">
                              {index + 1}
                            </span>
                            <span className="font-bold text-foreground truncate">{note.title}</span>
                          </div>
                          {selectedNotes.length > 2 && (
                            <button
                              onClick={() => toggleNoteSelection(note.id)}
                              title="Remove from merge"
                              className="text-muted-foreground hover:text-destructive p-0.5 rounded transition-colors"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>

                        <div className="flex items-center gap-2 text-[10px] text-muted-foreground font-mono">
                          <span className="capitalize px-1.5 py-0.2 rounded bg-surface-hover">
                            {note.category}
                          </span>
                          <span>ID: {note.id.substring(0, 10)}...</span>
                        </div>

                        <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                          {note.snippet || note.content}
                        </p>
                      </div>
                    ))
                  )}
                </Tabs.Content>

                {/* Suggested Correlated Notes Tab Content */}
                <Tabs.Content value="suggested" className="flex-1 overflow-y-auto p-2 space-y-2 outline-none">
                  {isLoadingCorrelated ? (
                    <div className="py-12 text-center text-muted-foreground">
                      <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                      <span className="text-xs">Finding related notes...</span>
                    </div>
                  ) : correlatedList.length === 0 ? (
                    <div className="p-8 text-center text-muted-foreground text-xs">
                      No additional related memories found for this topic.
                    </div>
                  ) : (
                    correlatedList.map((item) => (
                      <div
                        key={item.id}
                        className="p-3 rounded-xl bg-card border border-border/80 text-xs space-y-1.5 shadow-xs"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-bold text-foreground truncate">{item.title}</span>
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold shrink-0">
                            {item.similarity_percent}% match
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                          <span className="capitalize px-1.5 py-0.2 rounded bg-surface-hover font-mono">
                            {item.category}
                          </span>
                          {item.shared_tags.length > 0 && (
                            <span className="text-[10px] text-muted-foreground">
                              Tags: #{item.shared_tags.join(', #')}
                            </span>
                          )}
                        </div>

                        <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                          {item.snippet}
                        </p>

                        <button
                          onClick={() => handleAddCorrelated(item)}
                          className="w-full mt-1 py-1 rounded bg-surface-hover hover:bg-surface-hover/80 text-foreground font-semibold text-[11px] flex items-center justify-center gap-1 border border-border/60 transition-colors"
                        >
                          <Plus className="w-3 h-3" />
                          <span>Add to Merge</span>
                        </button>
                      </div>
                    ))
                  )}
                </Tabs.Content>
              </Tabs.Root>
            </div>

            {/* Right Column: Settings & AI Synthesis */}
            <div className="flex-1 flex flex-col bg-surface-editor overflow-y-auto p-6 space-y-5">
              {mergeResult ? (
                /* Merge Result View */
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-base font-bold text-foreground">{mergeResult.title}</h4>
                      <p className="text-xs text-muted-foreground font-mono mt-0.5">
                        Category: {mergeResult.category} • Tags: #{mergeResult.tags.join(', #')}
                      </p>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-card border border-border">
                    <pre className="font-mono text-xs whitespace-pre-wrap leading-relaxed text-foreground/90 max-h-[50vh] overflow-y-auto">
                      {mergeResult.content_preview}
                    </pre>
                  </div>
                </div>
              ) : (
                /* Merge Configuration Form */
                <>
                  {/* Target Title */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-foreground">Merged Note Title</label>
                    <input
                      type="text"
                      value={targetTitle}
                      onChange={(e) => setTargetTitle(e.target.value)}
                      placeholder="e.g. Master Guide to Machine Learning OCR"
                      className="w-full px-3 py-2 rounded-lg bg-surface-hover border border-border text-xs text-foreground outline-none focus:ring-1 focus:ring-ring"
                    />
                  </div>

                  {/* Category & Tag Row */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Target Category */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-bold text-foreground">Target Category</label>
                      <select
                        value={targetCategory}
                        onChange={(e) => setTargetCategory(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg bg-surface-hover border border-border text-xs text-foreground outline-none focus:ring-1 focus:ring-ring capitalize"
                      >
                        {categories.map((c) => (
                          <option key={c.category} value={c.category}>
                            {c.category}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Target Tags */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-bold text-foreground">Consolidated Tags</label>
                      <div className="flex items-center gap-1">
                        <input
                          type="text"
                          value={newTagInput}
                          onChange={(e) => setNewTagInput(e.target.value)}
                          onKeyDown={handleAddTag}
                          placeholder="tag name..."
                          className="flex-1 px-3 py-2 rounded-lg bg-surface-hover border border-border text-xs text-foreground outline-none focus:ring-1 focus:ring-ring"
                        />
                        <button
                          onClick={() => {
                            if (newTagInput.trim()) {
                              const clean = newTagInput.trim().replace(/^#/, '');
                              if (!targetTags.includes(clean)) setTargetTags([...targetTags, clean]);
                              setNewTagInput('');
                            }
                          }}
                          className="px-3 py-2 rounded-lg bg-surface-hover hover:bg-surface-hover/80 text-xs font-semibold border border-border"
                        >
                          Add
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Tags Pill List */}
                  {targetTags.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {targetTags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-surface-hover text-foreground font-mono text-[11px] border border-border"
                        >
                          <span>#{tag}</span>
                          <button
                            onClick={() => handleRemoveTag(tag)}
                            className="text-muted-foreground hover:text-foreground"
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Optional Custom Instructions */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-foreground flex items-center justify-between">
                      <span>Custom LLM Merge Guidance (Optional)</span>
                      <span className="text-[10px] text-muted-foreground font-normal">
                        e.g., "Emphasize CLI commands and code snippets"
                      </span>
                    </label>
                    <textarea
                      value={instruction}
                      onChange={(e) => setInstruction(e.target.value)}
                      placeholder="Optional prompt guidance for how to organize and prioritize the merged information..."
                      rows={3}
                      className="w-full px-3 py-2 rounded-lg bg-surface-hover border border-border text-xs text-foreground outline-none focus:ring-1 focus:ring-ring resize-none"
                    />
                  </div>

                  {/* Options */}
                  <div className="space-y-2">
                    {/* AI Toggle */}
                    <div className="p-3.5 rounded-xl bg-surface-hover/50 border border-border/80 flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-violet-500" />
                          <span className="text-xs font-bold text-foreground">Synthesize with AI</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground">
                          {useAi
                            ? 'Intelligently combine and eliminate redundancies using AI synthesis'
                            : 'Fast deterministic merge (organizes notes under clean markdown headings without calling LLM)'}
                        </p>
                      </div>
                      <input
                        type="checkbox"
                        checked={useAi}
                        onChange={(e) => setUseAi(e.target.checked)}
                        className="w-4 h-4 rounded border-border text-foreground accent-foreground cursor-pointer"
                      />
                    </div>

                    {/* Clean Up Source Notes */}
                    <div className="p-3.5 rounded-xl bg-surface-hover/50 border border-border/80 flex items-center justify-between">
                      <div>
                        <span className="text-xs font-bold text-foreground">Clean Up Source Notes</span>
                        <p className="text-[11px] text-muted-foreground">
                          Delete original source notes after merging to prevent duplicate search results
                        </p>
                      </div>
                      <input
                        type="checkbox"
                        checked={deleteSources}
                        onChange={(e) => setDeleteSources(e.target.checked)}
                        className="w-4 h-4 rounded border-border text-foreground accent-foreground cursor-pointer"
                      />
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-2 flex items-center justify-end gap-3">
                    <button
                      onClick={handleDone}
                      className="px-4 py-2 rounded-lg bg-surface-hover hover:bg-surface-hover/80 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
                    >
                      Cancel
                    </button>

                    <button
                      onClick={handleExecuteMerge}
                      disabled={isMerging || selectedNotes.length < 2}
                      className="flex items-center gap-2 px-5 py-2 rounded-lg bg-foreground text-background text-xs font-bold hover:opacity-90 transition-opacity disabled:opacity-50 shadow-md cursor-pointer"
                    >
                      {isMerging ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>{useAi ? 'Synthesizing Notes with AI...' : 'Merging Notes...'}</span>
                        </>
                      ) : (
                        <>
                          {useAi ? <Sparkles className="w-4 h-4 text-violet-300 dark:text-violet-200" /> : <Combine className="w-4 h-4" />}
                          <span>{useAi ? `Merge ${selectedNotes.length} Notes with AI` : `Merge ${selectedNotes.length} Notes (Direct)`}</span>
                        </>
                      )}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
