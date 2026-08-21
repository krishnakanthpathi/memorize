import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Tag, X, Plus, Sparkles, Loader2 } from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';

export const ManageTagsModal: React.FC = () => {
  const {
    activeModal,
    setActiveModal,
    activeNoteId,
    notes,
    updateActiveNote,
    autoTagActiveNote,
    isAutoTagging,
  } = useNotesStore();

  const [tagInput, setTagInput] = useState('');
  const [autoTagMsg, setAutoTagMsg] = useState<string | null>(null);

  const isOpen = activeModal === 'tags';
  const activeNote = notes.find((n) => n.id === activeNoteId);

  if (!activeNote) return null;

  const currentTags = Array.isArray(activeNote.tags) ? activeNote.tags : [];

  const handleAddTag = (e: React.FormEvent) => {
    e.preventDefault();
    if (!tagInput.trim()) return;
    const cleanTag = tagInput.trim().replace(/^#/, '');
    if (!currentTags.includes(cleanTag)) {
      updateActiveNote({ tags: [...currentTags, cleanTag] });
    }
    setTagInput('');
  };

  const handleRemoveTag = (tagToRemove: string) => {
    updateActiveNote({
      tags: currentTags.filter((t) => t !== tagToRemove),
    });
  };

  const handleAutoTag = async () => {
    if (!activeNote.content?.trim()) return;
    setAutoTagMsg(null);
    try {
      const res = await autoTagActiveNote(activeNote.id, activeNote.content, activeNote.title);
      if (res && res.tags) {
        setAutoTagMsg(`Auto-tagged ${res.tags.length} item${res.tags.length !== 1 ? 's' : ''}!`);
        setTimeout(() => setAutoTagMsg(null), 3000);
      }
    } catch {
      setAutoTagMsg('Auto-tagging failed');
      setTimeout(() => setAutoTagMsg(null), 3000);
    }
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && setActiveModal(null)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-background/80 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-card border border-border rounded-xl shadow-2xl p-6 z-50 animate-in zoom-in-95 duration-150 focus:outline-none">
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-border">
            <div className="flex items-center gap-2">
              <Tag className="w-5 h-5 text-foreground" />
              <div>
                <Dialog.Title className="text-base font-bold text-foreground">
                  Manage Note Tags
                </Dialog.Title>
                <Dialog.Description className="text-xs text-muted-foreground truncate max-w-[280px]">
                  {activeNote.title || 'Untitled Note'}
                </Dialog.Description>
              </div>
            </div>
            <button
              onClick={() => setActiveModal(null)}
              className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body */}
          <div className="py-4 space-y-4">
            {/* Active Tags list */}
            <div>
              <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground mb-2">
                <span>Active Tags ({currentTags.length})</span>
                <button
                  type="button"
                  onClick={handleAutoTag}
                  disabled={isAutoTagging || !activeNote.content?.trim()}
                  className="flex items-center gap-1 text-xs font-medium text-foreground hover:underline disabled:opacity-50 cursor-pointer"
                >
                  {isAutoTagging ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5" />
                  )}
                  <span>Auto-tag with AI</span>
                </button>
              </div>

              {autoTagMsg && (
                <div className="mb-2 text-xs font-mono text-foreground bg-surface-hover border border-border px-2.5 py-1 rounded-md animate-in fade-in">
                  ✓ {autoTagMsg}
                </div>
              )}

              <div className="flex flex-wrap gap-1.5 min-h-[48px] max-h-[160px] overflow-y-auto p-2 rounded-lg bg-surface-hover/60 border border-border">
                {currentTags.length > 0 ? (
                  currentTags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-card text-foreground font-mono text-xs border border-border shadow-2xs"
                    >
                      <span>#{tag}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        title="Remove tag"
                        className="text-muted-foreground hover:text-foreground p-0.5 rounded cursor-pointer"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-muted-foreground italic m-auto">
                    No tags assigned to this note
                  </span>
                )}
              </div>
            </div>

            {/* Add Tag Input Form */}
            <form onSubmit={handleAddTag} className="space-y-2">
              <label className="text-xs font-semibold text-muted-foreground">Add Custom Tag</label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="e.g. fastmcp, ocr, architecture..."
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg bg-surface-hover border border-border text-xs text-foreground font-mono outline-none focus:ring-1 focus:ring-ring"
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={!tagInput.trim()}
                  className="flex items-center gap-1 px-3 py-2 rounded-lg bg-foreground text-background font-semibold text-xs hover:opacity-90 disabled:opacity-40 transition-opacity cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add</span>
                </button>
              </div>
            </form>
          </div>

          {/* Footer */}
          <div className="pt-3 border-t border-border flex items-center justify-end">
            <button
              onClick={() => setActiveModal(null)}
              className="px-4 py-1.5 rounded-lg bg-foreground text-background font-semibold text-xs hover:opacity-90 transition-opacity cursor-pointer"
            >
              Done
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
