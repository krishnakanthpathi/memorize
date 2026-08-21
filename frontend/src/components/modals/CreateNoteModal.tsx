import React, { useState, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Plus, X, Folder, Tag, FileText } from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';

export const CreateNoteModal: React.FC = () => {
  const {
    activeModal,
    setActiveModal,
    categories,
    selectedCategory,
    createNewNote,
  } = useNotesStore();

  const isOpen = activeModal === 'new-note';

  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('personal');
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);

  useEffect(() => {
    if (isOpen) {
      setTitle('');
      setCategory(
        selectedCategory && selectedCategory !== 'all' ? selectedCategory : 'personal'
      );
      setTagInput('');
      setTags([]);
    }
  }, [isOpen, selectedCategory]);

  if (!isOpen) return null;

  const handleAddTag = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const cleanTag = tagInput.trim().replace(/^#/, '');
      if (cleanTag && !tags.includes(cleanTag)) {
        setTags([...tags, cleanTag]);
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    const finalTitle = title.trim() || 'Untitled Note';
    const cleanTag = tagInput.trim().replace(/^#/, '');
    const finalTags = cleanTag && !tags.includes(cleanTag) ? [...tags, cleanTag] : tags;

    createNewNote(category, finalTitle, finalTags);
    setActiveModal(null);
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && setActiveModal(null)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-background/80 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-card border border-border rounded-xl shadow-2xl p-6 z-50 animate-in zoom-in-95 duration-150 focus:outline-none">
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-border">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-foreground" />
              <div>
                <Dialog.Title className="text-base font-bold text-foreground">
                  Create New Note
                </Dialog.Title>
                <Dialog.Description className="text-xs text-muted-foreground">
                  Specify note title and category
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
          <form onSubmit={handleCreate} className="py-4 space-y-4 text-xs">
            {/* Note Title Input */}
            <div className="space-y-1.5">
              <label className="font-semibold text-muted-foreground">Note Title</label>
              <input
                type="text"
                placeholder="e.g. Architecture Overview, API Spec, Meeting Notes..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-surface-hover border border-border text-sm text-foreground font-semibold outline-none focus:ring-1 focus:ring-ring"
                autoFocus
              />
            </div>

            {/* Category Selector */}
            <div className="space-y-1.5">
              <label className="font-semibold text-muted-foreground flex items-center gap-1.5">
                <Folder className="w-3.5 h-3.5" />
                <span>Category</span>
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-surface-hover border border-border text-xs text-foreground font-medium outline-none focus:ring-1 focus:ring-ring capitalize cursor-pointer"
              >
                {categories.map((cat) => (
                  <option key={cat.category} value={cat.category} className="capitalize">
                    {cat.category} ({cat.count})
                  </option>
                ))}
              </select>
            </div>

            {/* Optional Tags */}
            <div className="space-y-1.5">
              <label className="font-semibold text-muted-foreground flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5" />
                <span>Tags (Optional, press Enter to add)</span>
              </label>
              <div className="flex flex-wrap gap-1.5 p-2 rounded-lg bg-surface-hover border border-border min-h-[38px] items-center">
                {tags.map((t) => (
                  <span
                    key={t}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-card text-foreground font-mono text-[11px] border border-border"
                  >
                    <span>#{t}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(t)}
                      className="text-muted-foreground hover:text-foreground cursor-pointer"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                <input
                  type="text"
                  placeholder={tags.length === 0 ? "Type tag and press Enter..." : "Add more..."}
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleAddTag}
                  className="flex-1 bg-transparent border-none outline-none text-xs text-foreground font-mono min-w-[120px]"
                />
              </div>
            </div>

            {/* Footer Buttons */}
            <div className="pt-3 flex items-center justify-end gap-2 border-t border-border">
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="px-3.5 py-1.5 rounded-lg border border-border hover:bg-surface-hover text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-foreground text-background font-semibold text-xs hover:opacity-90 transition-opacity cursor-pointer shadow-xs"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Note</span>
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
