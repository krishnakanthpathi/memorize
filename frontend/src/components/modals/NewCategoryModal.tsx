import React, { useState } from 'react';
import { FolderPlus, X } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { useNotesStore } from '@/store/useNotesStore';

export const NewCategoryModal: React.FC = () => {
  const { activeModal, setActiveModal, createNewNote, setSelectedCategory } = useNotesStore();
  const isOpen = activeModal === 'new-category';

  const [categoryName, setCategoryName] = useState('');

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!categoryName.trim()) return;

    const cat = categoryName.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
    setSelectedCategory(cat);
    createNewNote(cat);
    setCategoryName('');
    setActiveModal(null);
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && setActiveModal(null)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-sm bg-card text-card-foreground border border-border rounded-xl shadow-2xl z-50 p-5 overflow-hidden animate-in fade-in zoom-in-95">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FolderPlus className="w-4 h-4 text-foreground" />
              <h3 className="text-sm font-bold">New Category</h3>
            </div>
            <Dialog.Close asChild>
              <button className="p-1 rounded-md text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>

          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="text-xs text-muted-foreground block mb-1.5 font-medium">
                Category Name:
              </label>
              <input
                type="text"
                autoFocus
                placeholder="e.g. projects, research, ideas..."
                value={categoryName}
                onChange={(e) => setCategoryName(e.target.value)}
                className="w-full bg-surface-hover border border-border px-3 py-2 rounded-lg text-xs outline-none focus:ring-1 focus:ring-ring text-foreground font-mono"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="px-3 py-1.5 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground hover:bg-surface-hover"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!categoryName.trim()}
                className="px-3 py-1.5 rounded-lg bg-foreground text-background text-xs font-semibold hover:opacity-90 disabled:opacity-40"
              >
                Create Category
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
