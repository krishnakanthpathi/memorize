import React, { useState, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Pencil, X, Sparkles, Loader2, Check } from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';

export const RenameNoteModal: React.FC = () => {
  const {
    activeModal,
    setActiveModal,
    activeNoteId,
    notes,
    updateActiveNote,
    generateNoteTitle,
    isGeneratingTitle,
  } = useNotesStore();

  const isOpen = activeModal === 'rename-note';
  const activeNote = notes.find((n) => n.id === activeNoteId);

  const [titleInput, setTitleInput] = useState('');

  useEffect(() => {
    if (activeNote && isOpen) {
      setTitleInput(activeNote.title || '');
    }
  }, [activeNote, isOpen]);

  if (!activeNote) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!titleInput.trim()) return;
    updateActiveNote({ title: titleInput.trim() }, true);
    setActiveModal(null);
  };

  const handleGenerateTitle = async () => {
    if (!activeNote.content?.trim()) return;
    try {
      const generated = await generateNoteTitle(activeNote.id, activeNote.content);
      if (generated) {
        setTitleInput(generated);
      }
    } catch (err) {
      console.error('Failed to generate title in modal:', err);
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
              <Pencil className="w-5 h-5 text-foreground" />
              <div>
                <Dialog.Title className="text-base font-bold text-foreground">
                  Rename Note
                </Dialog.Title>
                <Dialog.Description className="text-xs text-muted-foreground">
                  Category: <span className="font-semibold text-foreground capitalize">{activeNote.category || 'personal'}</span>
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

          {/* Form */}
          <form onSubmit={handleSave} className="py-4 space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-muted-foreground">
                  Note Title
                </label>
                <button
                  type="button"
                  onClick={handleGenerateTitle}
                  disabled={isGeneratingTitle || !activeNote.content?.trim()}
                  className="flex items-center gap-1 text-xs font-medium text-foreground hover:underline disabled:opacity-50 cursor-pointer"
                >
                  {isGeneratingTitle ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5" />
                  )}
                  <span>Generate with AI</span>
                </button>
              </div>
              <input
                type="text"
                placeholder="Enter note title..."
                value={titleInput}
                onChange={(e) => setTitleInput(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-surface-hover border border-border text-sm text-foreground font-semibold outline-none focus:ring-1 focus:ring-ring"
                autoFocus
              />
            </div>

            {/* Footer Buttons */}
            <div className="pt-2 flex items-center justify-end gap-2 border-t border-border">
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="px-3.5 py-1.5 rounded-lg border border-border hover:bg-surface-hover text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!titleInput.trim()}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-foreground text-background font-semibold text-xs hover:opacity-90 disabled:opacity-40 transition-opacity cursor-pointer shadow-xs"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Save Title</span>
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
