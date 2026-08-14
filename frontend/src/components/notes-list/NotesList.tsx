import React, { useMemo, useState } from 'react';
import {
  Search,
  SquarePen,
  Pin,
  Star,
  Trash2,
  RotateCcw,
  ArrowUpDown,
  History,
  Tag,
  Folder,
  Sparkles,
  X,
} from 'lucide-react';
import * as ContextMenu from '@radix-ui/react-context-menu';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useNotesStore } from '@/store/useNotesStore';
import { Note } from '@/types';
import { cn, formatDateRelative, cleanMarkdownSnippet } from '@/lib/utils';

type SortOption = 'updated' | 'created' | 'title';

export const NotesList: React.FC = () => {
  const {
    notes,
    trashNotes,
    activeNoteId,
    activeView,
    selectedCategory,
    selectedTag,
    searchQuery,
    selectNote,
    createNewNote,
    requestDeleteNote,
    restoreNote,
    togglePin,
    toggleFavorite,
    setSearchQuery,
    setActiveModal,
  } = useNotesStore();

  const [sortBy, setSortBy] = useState<SortOption>('updated');

  // Filter notes based on activeView, category, tag, and search query
  const filteredNotes = useMemo(() => {
    let source = activeView === 'trash' ? trashNotes : notes;

    // View filter
    if (activeView === 'pinned') {
      source = source.filter((n) => n.isPinned);
    } else if (activeView === 'favorites') {
      source = source.filter((n) => n.isFavorite);
    }

    // Category filter
    if (selectedCategory) {
      source = source.filter(
        (n) => (n.category || '').toLowerCase() === selectedCategory.toLowerCase()
      );
    }

    // Tag filter
    if (selectedTag) {
      source = source.filter((n) =>
        Array.isArray(n.tags) &&
        n.tags.some(
          (t) => t.trim().replace(/^#/, '').toLowerCase() === selectedTag.toLowerCase()
        )
      );
    }

    // Search query filter (instant search)
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      source = source.filter(
        (n) =>
          n.title.toLowerCase().includes(q) ||
          n.content.toLowerCase().includes(q) ||
          (Array.isArray(n.tags) && n.tags.some((t) => t.toLowerCase().includes(q)))
      );
    }

    // Sort
    return [...source].sort((a, b) => {
      // Pinned items always come first if not viewing trash
      if (activeView !== 'trash') {
        if (a.isPinned && !b.isPinned) return -1;
        if (!a.isPinned && b.isPinned) return 1;
      }

      if (sortBy === 'title') {
        return a.title.localeCompare(b.title);
      }
      if (sortBy === 'created') {
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      }
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
    });
  }, [
    notes,
    trashNotes,
    activeView,
    selectedCategory,
    selectedTag,
    searchQuery,
    sortBy,
  ]);

  const viewTitle = useMemo(() => {
    if (activeView === 'trash') return 'Trash';
    if (activeView === 'pinned') return 'Pinned Notes';
    if (activeView === 'favorites') return 'Favorites';
    if (selectedCategory) return `Category: ${selectedCategory}`;
    if (selectedTag) return `Tag: #${selectedTag}`;
    return 'All Notes';
  }, [activeView, selectedCategory, selectedTag]);

  return (
    <div className="h-full w-full flex flex-col bg-surface-list border-r border-border select-none text-foreground">
      {/* Top Header & Search */}
      <div className="p-3 border-b border-border space-y-2.5">
        {/* Search input with Hybrid shortcut */}
        <div className="relative flex items-center">
          <Search className="w-3.5 h-3.5 absolute left-2.5 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            placeholder="Search notes or content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-surface-hover pl-8 pr-16 py-1.5 rounded-md text-xs border border-border/70 focus:outline-none focus:ring-1 focus:ring-ring transition-all placeholder:text-muted-foreground/70"
          />
          {searchQuery ? (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-8 p-1 text-muted-foreground hover:text-foreground"
            >
              <X className="w-3 h-3" />
            </button>
          ) : null}
          <button
            onClick={() => setActiveModal('search')}
            title="Open Deep Hybrid AI Vector Search"
            className="absolute right-1.5 p-1 rounded hover:bg-surface-selected text-muted-foreground hover:text-foreground transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* View title, sort menu, and new note button */}
        <div className="flex items-center justify-between">
          <div className="flex items-baseline gap-1.5">
            <span className="font-semibold text-xs tracking-tight capitalize">
              {viewTitle}
            </span>
            <span className="text-[10px] text-muted-foreground font-mono">
              ({filteredNotes.length})
            </span>
          </div>

          <div className="flex items-center gap-1">
            {/* Sort Menu */}
            <DropdownMenu.Root>
              <DropdownMenu.Trigger asChild>
                <button
                  title="Sort Notes"
                  className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
                >
                  <ArrowUpDown className="w-3.5 h-3.5" />
                </button>
              </DropdownMenu.Trigger>

              <DropdownMenu.Portal>
                <DropdownMenu.Content
                  align="end"
                  className="z-50 min-w-[140px] bg-popover text-popover-foreground rounded-md p-1 border border-border shadow-lg text-xs animate-in fade-in zoom-in-95"
                >
                  <DropdownMenu.Item
                    onClick={() => setSortBy('updated')}
                    className={cn(
                      'px-2 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center justify-between',
                      sortBy === 'updated' && 'font-semibold'
                    )}
                  >
                    <span>Date Modified</span>
                    {sortBy === 'updated' && <span className="text-xs">✓</span>}
                  </DropdownMenu.Item>
                  <DropdownMenu.Item
                    onClick={() => setSortBy('created')}
                    className={cn(
                      'px-2 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center justify-between',
                      sortBy === 'created' && 'font-semibold'
                    )}
                  >
                    <span>Date Created</span>
                    {sortBy === 'created' && <span className="text-xs">✓</span>}
                  </DropdownMenu.Item>
                  <DropdownMenu.Item
                    onClick={() => setSortBy('title')}
                    className={cn(
                      'px-2 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center justify-between',
                      sortBy === 'title' && 'font-semibold'
                    )}
                  >
                    <span>Title (A-Z)</span>
                    {sortBy === 'title' && <span className="text-xs">✓</span>}
                  </DropdownMenu.Item>
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>

            {/* New note trigger */}
            {activeView !== 'trash' && (
              <button
                onClick={() => createNewNote(selectedCategory || undefined)}
                title="Create New Note (⌘N)"
                className="p-1.5 rounded-md bg-foreground text-background hover:opacity-90 transition-opacity shadow-xs"
              >
                <SquarePen className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Note Item Cards ScrollArea */}
      <div className="flex-1 overflow-y-auto divide-y divide-border/40">
        {filteredNotes.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center text-muted-foreground">
            <SquarePen className="w-8 h-8 stroke-1 mb-2 opacity-40" />
            <p className="text-xs font-medium">No notes found</p>
            <p className="text-[11px] opacity-70 mt-0.5">
              {activeView === 'trash'
                ? 'Trash is empty'
                : 'Click the pen icon above to create your first note.'}
            </p>
          </div>
        ) : (
          filteredNotes.map((note) => {
            const isSelected = activeNoteId === note.id;
            const snippet = cleanMarkdownSnippet(note.content || note.snippet || '');

            return (
              <ContextMenu.Root key={note.id}>
                <ContextMenu.Trigger asChild>
                  <div
                    onClick={() => selectNote(note.id)}
                    className={cn(
                      'p-3 cursor-pointer transition-all relative border-l-2',
                      isSelected
                        ? 'bg-surface-selected border-foreground shadow-xs'
                        : 'border-transparent hover:bg-surface-hover'
                    )}
                  >
                    {/* Header: Title + relative date + pin */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5 truncate">
                        {note.isPinned && (
                          <Pin className="w-3 h-3 text-foreground shrink-0 fill-current" />
                        )}
                        {note.isFavorite && (
                          <Star className="w-3 h-3 text-amber-500 shrink-0 fill-amber-500" />
                        )}
                        <h4
                          className={cn(
                            'text-xs font-bold truncate leading-snug',
                            isSelected ? 'text-foreground' : 'text-foreground/90'
                          )}
                        >
                          {note.title || 'Untitled Note'}
                        </h4>
                      </div>
                      <span className="text-[10px] text-muted-foreground shrink-0 font-mono">
                        {formatDateRelative(note.updatedAt)}
                      </span>
                    </div>

                    {/* Clean markdown snippet preview */}
                    <p className="text-[11px] text-muted-foreground line-clamp-1 mt-1 font-normal">
                      {snippet || <span className="italic opacity-60">No additional text</span>}
                    </p>

                    {/* Badges footer (Category + Tags) */}
                    <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                      <span className="inline-flex items-center gap-0.5 text-[9px] font-mono px-1.5 py-0.5 rounded bg-muted/60 text-muted-foreground capitalize">
                        <Folder className="w-2.5 h-2.5 opacity-70" />
                        {note.category || 'personal'}
                      </span>

                      {Array.isArray(note.tags) &&
                        note.tags.slice(0, 2).map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center gap-0.5 text-[9px] font-mono px-1 py-0.2 rounded bg-surface-hover text-muted-foreground"
                          >
                            #{tag.replace(/^#/, '')}
                          </span>
                        ))}
                      {Array.isArray(note.tags) && note.tags.length > 2 && (
                        <span className="text-[9px] text-muted-foreground font-mono">
                          +{note.tags.length - 2}
                        </span>
                      )}
                    </div>
                  </div>
                </ContextMenu.Trigger>

                {/* Right Click Context Menu */}
                <ContextMenu.Portal>
                  <ContextMenu.Content className="z-50 min-w-[170px] bg-popover text-popover-foreground rounded-md p-1 border border-border shadow-xl text-xs animate-in fade-in zoom-in-95">
                    {activeView !== 'trash' ? (
                      <>
                        <ContextMenu.Item
                          onClick={() => togglePin(note.id)}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2"
                        >
                          <Pin className="w-3.5 h-3.5" />
                          <span>{note.isPinned ? 'Unpin Note' : 'Pin to Top'}</span>
                        </ContextMenu.Item>

                        <ContextMenu.Item
                          onClick={() => toggleFavorite(note.id)}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2"
                        >
                          <Star className="w-3.5 h-3.5" />
                          <span>{note.isFavorite ? 'Remove Favorite' : 'Mark Favorite'}</span>
                        </ContextMenu.Item>

                        <ContextMenu.Item
                          onClick={() => {
                            selectNote(note.id);
                            setActiveModal('versions');
                          }}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2"
                        >
                          <History className="w-3.5 h-3.5" />
                          <span>Version History</span>
                        </ContextMenu.Item>

                        <ContextMenu.Separator className="h-px bg-border my-1" />

                        <ContextMenu.Item
                          onClick={() => requestDeleteNote(note.id, false)}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-destructive/10 text-destructive flex items-center gap-2"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>Move to Trash</span>
                        </ContextMenu.Item>
                      </>
                    ) : (
                      <>
                        <ContextMenu.Item
                          onClick={() => restoreNote(note.id)}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          <span>Restore Note</span>
                        </ContextMenu.Item>

                        <ContextMenu.Item
                          onClick={() => requestDeleteNote(note.id, true)}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-destructive/10 text-destructive flex items-center gap-2 font-semibold"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>Delete Permanently</span>
                        </ContextMenu.Item>
                      </>
                    )}
                  </ContextMenu.Content>
                </ContextMenu.Portal>
              </ContextMenu.Root>
            );
          })
        )}
      </div>
    </div>
  );
};
