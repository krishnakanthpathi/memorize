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
  Copy,
  Check,
  Combine,
  CheckSquare,
  Square,
  Wand2,
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
    requestDeleteBatch,
    requestEmptyTrash,
    restoreNote,
    restoreBatchNotes,
    togglePin,
    toggleFavorite,
    setSearchQuery,
    setActiveModal,
    selectedNoteIds,
    toggleNoteSelection,
    selectAllNotes,
    clearNoteSelection,
    openMergeModal,
    organizeNote,
  } = useNotesStore();

  const [sortBy, setSortBy] = useState<SortOption>('updated');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopyId = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

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

  const areAllFilteredSelected = filteredNotes.length > 0 && filteredNotes.every((n) => selectedNoteIds.includes(n.id));

  const handleToggleSelectAll = () => {
    if (areAllFilteredSelected) {
      clearNoteSelection();
    } else {
      selectAllNotes(filteredNotes.map((n) => n.id));
    }
  };

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
            <Sparkles className="w-3.5 h-3.5 text-foreground" />
          </button>
        </div>


        {/* View title, sort menu, empty trash button and new note button */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {filteredNotes.length > 0 && (
              <button
                onClick={handleToggleSelectAll}
                title={areAllFilteredSelected ? "Deselect all notes" : "Select all notes"}
                className="p-1 rounded hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              >
                {areAllFilteredSelected ? (
                  <CheckSquare className="w-3.5 h-3.5 text-foreground fill-surface-selected" />
                ) : (
                  <Square className="w-3.5 h-3.5 opacity-60 hover:opacity-100" />
                )}
              </button>
            )}
            <div className="flex items-baseline gap-1.5">
              <span className="font-semibold text-xs tracking-tight capitalize">
                {viewTitle}
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">
                ({filteredNotes.length})
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {/* Empty Trash Button (when viewing trash) */}
            {activeView === 'trash' && trashNotes.length > 0 && (
              <button
                onClick={() => requestEmptyTrash()}
                title="Empty all notes permanently from Trash"
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-semibold text-destructive hover:bg-destructive/10 border border-destructive/20 transition-colors cursor-pointer shadow-2xs"
              >
                <Trash2 className="w-3 h-3" />
                <span>Empty Trash</span>
              </button>
            )}

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
                onClick={() => setActiveModal('new-note')}
                title="Create New Note (⌘N)"
                className="p-1.5 rounded-md bg-foreground text-background hover:opacity-90 transition-opacity shadow-xs cursor-pointer"
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
            const isChecked = selectedNoteIds.includes(note.id);
            const snippet = cleanMarkdownSnippet(note.content || note.snippet || '');

            return (
              <ContextMenu.Root key={note.id}>
                <ContextMenu.Trigger asChild>
                  <div
                    onClick={(e) => {
                      if (e.shiftKey || e.metaKey || e.ctrlKey) {
                        e.preventDefault();
                        toggleNoteSelection(note.id);
                      } else {
                        selectNote(note.id);
                      }
                    }}
                    className={cn(
                      'p-3 cursor-pointer transition-all relative border-l-2 group select-none',
                      isSelected
                        ? 'bg-surface-selected border-foreground shadow-xs'
                        : isChecked
                        ? 'bg-surface-hover/80 border-primary/50'
                        : 'border-transparent hover:bg-surface-hover'
                    )}
                  >
                    {/* Header: Title + relative date + pin + selection checkbox */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 truncate">
                        {/* Multi-select Checkbox */}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleNoteSelection(note.id);
                          }}
                          className={cn(
                            'p-0.5 rounded transition-all text-muted-foreground hover:text-foreground',
                            isChecked || selectedNoteIds.length > 0 ? 'opacity-100' : 'opacity-0 group-hover:opacity-60'
                          )}
                        >
                          {isChecked ? (
                            <CheckSquare className="w-3.5 h-3.5 text-foreground fill-surface-selected" />
                          ) : (
                            <Square className="w-3.5 h-3.5 opacity-60" />
                          )}
                        </button>

                        <h4
                          className={cn(
                            'font-semibold text-xs tracking-tight truncate leading-tight',
                            isSelected ? 'text-foreground' : 'text-foreground/90'
                          )}
                        >
                          {note.title || 'Untitled Note'}
                        </h4>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        {note.isPinned && activeView !== 'trash' && (
                          <Pin className="w-3 h-3 text-muted-foreground fill-current" />
                        )}
                        {note.isFavorite && activeView !== 'trash' && (
                          <Star className="w-3 h-3 text-foreground fill-foreground" />
                        )}
                        <span className="text-[10px] text-muted-foreground/70 font-mono">
                          {formatDateRelative(note.updatedAt || note.createdAt)}
                        </span>
                      </div>
                    </div>

                    {/* Preview Snippet */}
                    <p className="text-[11px] text-muted-foreground/80 line-clamp-2 mt-1 leading-snug">
                      {snippet || <span className="italic opacity-50">No additional text</span>}
                    </p>

                    {/* Footer: Category Pill + Tags Chips */}
                    <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-badge text-muted-foreground text-[10px] font-medium border border-border/40">
                        <Folder className="w-2.5 h-2.5" />
                        <span>{note.category || 'personal'}</span>
                      </span>

                      {Array.isArray(note.tags) &&
                        note.tags.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-surface-badge text-muted-foreground/90 text-[10px] border border-border/40"
                          >
                            <Tag className="w-2 h-2" />
                            <span>{tag.replace(/^#/, '')}</span>
                          </span>
                        ))}
                      {Array.isArray(note.tags) && note.tags.length > 3 && (
                        <span className="text-[9px] text-muted-foreground font-mono">
                          +{note.tags.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                </ContextMenu.Trigger>

                {/* Right-click Context Menu */}
                <ContextMenu.Portal>
                  <ContextMenu.Content className="z-50 min-w-[190px] bg-popover text-popover-foreground rounded-lg p-1.5 border border-border shadow-xl text-xs animate-in fade-in zoom-in-95 space-y-0.5">
                    {activeView !== 'trash' ? (
                      <>
                        <ContextMenu.Item
                          onClick={(e) => handleCopyId(e, note.id)}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2"
                        >
                          {copiedId === note.id ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-foreground" />
                              <span className="text-foreground font-medium">Copied Memory ID!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5 text-muted-foreground" />
                              <span>Copy Memory ID</span>
                            </>
                          )}
                        </ContextMenu.Item>

                        <ContextMenu.Separator className="h-px bg-border my-1" />

                        {/* AI Organize & Polish */}
                        <ContextMenu.Item
                          onClick={() => {
                            selectNote(note.id);
                            organizeNote(note.id);
                          }}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2 font-medium text-foreground"
                        >
                          <Wand2 className="w-3.5 h-3.5 text-foreground" />
                          <span>AI Organize & Polish</span>
                        </ContextMenu.Item>


                        {/* Merge Actions */}
                        <ContextMenu.Item
                          onClick={() => openMergeModal(selectedNoteIds.includes(note.id) && selectedNoteIds.length > 1 ? selectedNoteIds : [note.id])}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2 font-medium text-foreground"
                        >
                          <Combine className="w-3.5 h-3.5" />
                          <span>
                            {selectedNoteIds.includes(note.id) && selectedNoteIds.length > 1
                              ? `Merge ${selectedNoteIds.length} Selected Notes...`
                              : 'Merge with Related Notes...'}
                          </span>
                        </ContextMenu.Item>

                        <ContextMenu.Item
                          onClick={() => toggleNoteSelection(note.id)}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2 text-muted-foreground hover:text-foreground"
                        >
                          {isChecked ? (
                            <>
                              <CheckSquare className="w-3.5 h-3.5" />
                              <span>Unselect Note</span>
                            </>
                          ) : (
                            <>
                              <Square className="w-3.5 h-3.5" />
                              <span>Select for Multi-Action</span>
                            </>
                          )}
                        </ContextMenu.Item>

                        <ContextMenu.Separator className="h-px bg-border my-1" />

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

                        {selectedNoteIds.includes(note.id) && selectedNoteIds.length > 1 ? (
                          <ContextMenu.Item
                            onClick={() => requestDeleteBatch(selectedNoteIds, false)}
                            className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-destructive/10 text-destructive flex items-center gap-2 font-semibold"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Move {selectedNoteIds.length} Selected to Trash</span>
                          </ContextMenu.Item>
                        ) : (
                          <ContextMenu.Item
                            onClick={() => requestDeleteNote(note.id, false)}
                            className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-destructive/10 text-destructive flex items-center gap-2"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Move to Trash</span>
                          </ContextMenu.Item>
                        )}
                      </>
                    ) : (
                      <>
                        <ContextMenu.Item
                          onClick={(e) => handleCopyId(e, note.id)}
                          className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2"
                        >
                          {copiedId === note.id ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-foreground" />
                              <span className="text-foreground font-medium">Copied Memory ID!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5 text-muted-foreground" />
                              <span>Copy Memory ID</span>
                            </>
                          )}
                        </ContextMenu.Item>

                        <ContextMenu.Separator className="h-px bg-border my-1" />

                        {selectedNoteIds.includes(note.id) && selectedNoteIds.length > 1 ? (
                          <>
                            <ContextMenu.Item
                              onClick={() => restoreBatchNotes(selectedNoteIds)}
                              className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2 font-medium"
                            >
                              <RotateCcw className="w-3.5 h-3.5" />
                              <span>Restore {selectedNoteIds.length} Selected Notes</span>
                            </ContextMenu.Item>

                            <ContextMenu.Item
                              onClick={() => requestDeleteBatch(selectedNoteIds, true)}
                              className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover text-foreground flex items-center gap-2 font-semibold"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              <span>Delete {selectedNoteIds.length} Permanently</span>
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
                              className="px-2.5 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover text-foreground flex items-center gap-2 font-semibold"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              <span>Delete Permanently</span>
                            </ContextMenu.Item>
                          </>
                        )}
                      </>
                    )}
                  </ContextMenu.Content>
                </ContextMenu.Portal>
              </ContextMenu.Root>
            );
          })
        )}
      </div>

      {/* Floating Multi-Selection Action Bar */}
      {selectedNoteIds.length > 0 && (
        <div className="p-2.5 bg-surface-sidebar border-t border-border flex items-center justify-between animate-in slide-in-from-bottom-2 select-none shrink-0 shadow-lg gap-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground truncate">
            <Combine className="w-4 h-4 text-foreground shrink-0" />
            <span className="truncate">{selectedNoteIds.length} {activeView === 'trash' ? 'trashed' : ''} note{selectedNoteIds.length > 1 ? 's' : ''} selected</span>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={() => clearNoteSelection()}
              className="px-2 py-1 rounded text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
            >
              Clear
            </button>

            {activeView !== 'trash' ? (
              <>
                <button
                  onClick={() => openMergeModal()}
                  disabled={selectedNoteIds.length < 2}
                  title={selectedNoteIds.length < 2 ? "Select at least 2 notes to merge" : "Merge selected notes"}
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-foreground text-background text-xs font-bold hover:opacity-90 transition-opacity disabled:opacity-50 shadow-xs cursor-pointer"
                >
                  <Sparkles className="w-3.5 h-3.5 text-background" />
                  <span>Merge ({selectedNoteIds.length})</span>
                </button>

                <button
                  onClick={() => requestDeleteBatch(selectedNoteIds, false)}
                  title="Move selected notes to Trash"
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-foreground bg-surface-hover hover:bg-surface-hover/80 border border-border text-xs font-semibold transition-colors cursor-pointer shadow-xs"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Move to Trash ({selectedNoteIds.length})</span>
                </button>
              </>
            ) : (

              <>
                <button
                  onClick={() => restoreBatchNotes(selectedNoteIds)}
                  title="Restore selected notes to Active Notes"
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-foreground text-background text-xs font-bold hover:opacity-90 transition-opacity shadow-xs cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Restore ({selectedNoteIds.length})</span>
                </button>

                <button
                  onClick={() => requestDeleteBatch(selectedNoteIds, true)}
                  title="Permanently delete selected notes"
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-destructive text-destructive-foreground text-xs font-bold hover:opacity-90 transition-opacity shadow-xs cursor-pointer"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete ({selectedNoteIds.length})</span>
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
