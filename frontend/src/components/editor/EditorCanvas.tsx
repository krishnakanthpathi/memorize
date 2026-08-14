import React, { useMemo, useState, useRef, useEffect } from 'react';
import {
  PanelLeft,
  Download,
  Trash2,
  History,
  Bot,
  Plus,
  X,
  Folder,
  FileText,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Eye,
  Columns,
  Save,
  Loader2,
} from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useNotesStore } from '@/store/useNotesStore';
import { MilkdownEditor } from './MilkdownEditor';
import { cn } from '@/lib/utils';

type EditorViewMode = 'markdown' | 'rich' | 'split';

export const EditorCanvas: React.FC = () => {
  const {
    notes,
    trashNotes,
    activeNoteId,
    activeView,
    categories,
    isSaving,
    lastSavedAt,
    sidebarCollapsed,
    toggleSidebar,
    updateActiveNote,
    saveCurrentNoteRemote,
    requestDeleteNote,
    restoreNote,
    exportActiveNote,
    setActiveModal,
    createNewNote,
    codeTheme,
  } = useNotesStore();

  const [tagInput, setTagInput] = useState('');
  const [showTagInput, setShowTagInput] = useState(false);
  const [viewMode, setViewMode] = useState<EditorViewMode>('markdown'); // Default as Markdown Viewer
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const splitTextareaRef = useRef<HTMLTextAreaElement>(null);

  // Find active note in regular notes OR trash notes
  const activeNote = useMemo(() => {
    if (!activeNoteId) return null;
    const fromNotes = notes.find((n) => n.id === activeNoteId);
    if (fromNotes) return fromNotes;
    const fromTrash = trashNotes.find((n) => n.id === activeNoteId);
    if (fromTrash) return fromTrash;
    return null;
  }, [notes, trashNotes, activeNoteId]);

  const isTrashed = useMemo(() => {
    if (!activeNote) return false;
    return !!(
      activeNote.isDeleted ||
      activeView === 'trash' ||
      trashNotes.some((n) => n.id === activeNote.id)
    );
  }, [activeNote, activeView, trashNotes]);

  // Automatically resize textareas to fit content so only one single scrollbar exists
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.max(450, textareaRef.current.scrollHeight)}px`;
    }
    if (splitTextareaRef.current) {
      splitTextareaRef.current.style.height = 'auto';
      splitTextareaRef.current.style.height = `${Math.max(450, splitTextareaRef.current.scrollHeight)}px`;
    }
  }, [activeNote?.content, viewMode]);

  // ⌘S or Ctrl+S for instant manual save
  useEffect(() => {
    const handleSaveKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        if (!isTrashed && activeNote) {
          saveCurrentNoteRemote();
        }
      }
    };
    window.addEventListener('keydown', handleSaveKeyDown);
    return () => window.removeEventListener('keydown', handleSaveKeyDown);
  }, [isTrashed, activeNote, saveCurrentNoteRemote]);

  // Word, lines, and character counts
  const stats = useMemo(() => {
    if (!activeNote) return { words: 0, chars: 0, lines: 1 };
    const text = (activeNote.title + ' ' + activeNote.content).trim();
    const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
    const chars = (activeNote.content || '').length;
    const lines = (activeNote.content || '').split('\n').length || 1;
    return { words, chars, lines };
  }, [activeNote]);

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isTrashed) return;
    updateActiveNote({ title: e.target.value });
  };

  const handleContentChange = (markdown: string) => {
    if (isTrashed) return;
    updateActiveNote({ content: markdown });
  };

  const handleTextareaKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const val = target.value;
      const updated = val.substring(0, start) + '  ' + val.substring(end);
      handleContentChange(updated);
      setTimeout(() => {
        target.selectionStart = target.selectionEnd = start + 2;
      }, 0);
    }
  };

  const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (isTrashed) return;
    if (e.key === 'Enter' && tagInput.trim() && activeNote) {
      e.preventDefault();
      const cleanTag = tagInput.trim().replace(/^#/, '');
      const currentTags = Array.isArray(activeNote.tags) ? activeNote.tags : [];
      if (!currentTags.includes(cleanTag)) {
        updateActiveNote({ tags: [...currentTags, cleanTag] });
      }
      setTagInput('');
      setShowTagInput(false);
    } else if (e.key === 'Escape') {
      setShowTagInput(false);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    if (isTrashed || !activeNote) return;
    const currentTags = Array.isArray(activeNote.tags) ? activeNote.tags : [];
    updateActiveNote({
      tags: currentTags.filter((t) => t !== tagToRemove),
    });
  };

  const handleCategoryChange = (category: string) => {
    if (isTrashed || !activeNote) return;
    updateActiveNote({ category, folderId: category });
  };

  if (!activeNote) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center bg-surface-editor text-muted-foreground p-8 text-center select-none">
        <div className="w-16 h-16 rounded-2xl bg-surface-hover flex items-center justify-center mb-4 border border-border">
          <FileText className="w-8 h-8 opacity-40" />
        </div>
        <h3 className="text-base font-semibold text-foreground mb-1">
          {activeView === 'trash' ? 'No Trashed Note Selected' : 'No Note Selected'}
        </h3>
        <p className="text-xs max-w-sm mb-5 text-muted-foreground">
          {activeView === 'trash'
            ? 'Select a deleted note from the list to preview or restore it.'
            : 'Select an existing note from the sidebar or create a fresh markdown note to start writing.'}
        </p>
        {activeView !== 'trash' && (
          <button
            onClick={() => createNewNote()}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-foreground text-background text-xs font-semibold hover:opacity-90 transition-opacity shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create Note</span>
          </button>
        )}
      </div>
    );
  }

  // Line numbers for raw markdown editor
  const lineCount = (activeNote.content || '').split('\n').length || 1;
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1);

  return (
    <div className="h-full w-full flex flex-col bg-surface-editor overflow-hidden text-foreground">
      {/* Trashed Notice Banner */}
      {isTrashed && (
        <div className="bg-destructive/10 border-b border-destructive/20 px-6 py-2.5 flex items-center justify-between text-xs text-destructive shrink-0">
          <div className="flex items-center gap-2 font-medium">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>This note is in Trash. Restore it to make edits.</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => restoreNote(activeNote.id)}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-foreground text-background font-semibold text-[11px] hover:opacity-90 transition-opacity"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Restore Note</span>
            </button>
            <button
              onClick={() => requestDeleteNote(activeNote.id, true)}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-destructive text-destructive-foreground font-semibold text-[11px] hover:opacity-90 transition-opacity"
            >
              <Trash2 className="w-3 h-3" />
              <span>Delete Permanently</span>
            </button>
          </div>
        </div>
      )}

      {/* Top Bar / Header Action Row */}
      <header className="h-14 px-4 border-b border-border flex items-center justify-between gap-4 shrink-0 bg-surface-editor select-none">
        {/* Left: Sidebar toggle + Breadcrumbs */}
        <div className="flex items-center gap-3 truncate">
          <button
            onClick={toggleSidebar}
            title={sidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
          >
            <PanelLeft className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-1.5 text-xs text-muted-foreground truncate">
            <Folder className="w-3.5 h-3.5 shrink-0" />
            {!isTrashed ? (
              <DropdownMenu.Root>
                <DropdownMenu.Trigger asChild>
                  <button className="hover:text-foreground font-medium capitalize truncate underline decoration-dotted decoration-border underline-offset-2">
                    {activeNote.category || 'personal'}
                  </button>
                </DropdownMenu.Trigger>
                <DropdownMenu.Portal>
                  <DropdownMenu.Content
                    align="start"
                    className="z-50 min-w-[140px] bg-popover text-popover-foreground rounded-md p-1 border border-border shadow-lg text-xs"
                  >
                    <div className="px-2 py-1 text-[10px] text-muted-foreground uppercase font-semibold">
                      Move Category
                    </div>
                    {categories.map((cat) => (
                      <DropdownMenu.Item
                        key={cat.category}
                        onClick={() => handleCategoryChange(cat.category)}
                        className={cn(
                          'px-2 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover capitalize flex items-center justify-between',
                          cat.category === activeNote.category && 'font-bold'
                        )}
                      >
                        <span>{cat.category}</span>
                        {cat.category === activeNote.category && (
                          <CheckCircle2 className="w-3 h-3" />
                        )}
                      </DropdownMenu.Item>
                    ))}
                    <DropdownMenu.Separator className="h-px bg-border my-1" />
                    <DropdownMenu.Item
                      onClick={() => setActiveModal('new-category')}
                      className="px-2 py-1.5 rounded cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-1.5 text-muted-foreground hover:text-foreground"
                    >
                      <Plus className="w-3 h-3" />
                      <span>New Category...</span>
                    </DropdownMenu.Item>
                  </DropdownMenu.Content>
                </DropdownMenu.Portal>
              </DropdownMenu.Root>
            ) : (
              <span className="capitalize">{activeNote.category || 'personal'}</span>
            )}
            <span>/</span>
            <span className="text-foreground font-semibold truncate max-w-[180px]">
              {activeNote.title || 'Untitled Note'}
            </span>
          </div>
        </div>

        {/* Center: Viewer Mode Switcher (Markdown / Normal / Split) */}
        <div className="hidden sm:flex items-center bg-surface-hover p-0.5 rounded-lg border border-border/80">
          <button
            onClick={() => setViewMode('markdown')}
            title="Markdown Source Viewer"
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all',
              viewMode === 'markdown'
                ? 'bg-card text-foreground shadow-xs font-semibold'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Markdown</span>
          </button>

          <button
            onClick={() => setViewMode('rich')}
            title="Normal / WYSIWYG Editor"
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all',
              viewMode === 'rich'
                ? 'bg-card text-foreground shadow-xs font-semibold'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Normal</span>
          </button>

          <button
            onClick={() => setViewMode('split')}
            title="Split Markdown & Preview"
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all',
              viewMode === 'split'
                ? 'bg-card text-foreground shadow-xs font-semibold'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Columns className="w-3.5 h-3.5" />
            <span>Split</span>
          </button>
        </div>

        {/* Right: Actions (Save, AI, Versions, Export, Delete) */}
        <div className="flex items-center gap-1.5 shrink-0">
          {!isTrashed && (
            <>
              {/* Manual Save Button */}
              <button
                onClick={() => saveCurrentNoteRemote()}
                disabled={isSaving}
                title="Save Note (⌘S / Ctrl+S)"
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shadow-xs select-none mr-1',
                  isSaving
                    ? 'bg-muted text-muted-foreground cursor-wait'
                    : 'bg-foreground text-background hover:opacity-90 active:scale-95'
                )}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    <span>Save</span>
                  </>
                )}
              </button>

              {/* AI Companion Chat Trigger */}
              <button
                onClick={() => setActiveModal('chat')}
                title="Ask AI Companion about this Note"
                className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <Bot className="w-4 h-4" />
              </button>

              {/* Version History Modal Trigger */}
              <button
                onClick={() => setActiveModal('versions')}
                title="Version History & Revert"
                className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <History className="w-4 h-4" />
              </button>

              {/* Export Markdown */}
              <button
                onClick={exportActiveNote}
                title="Export as Markdown (.md)"
                className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <Download className="w-4 h-4" />
              </button>

              {/* Delete */}
              <button
                onClick={() => requestDeleteNote(activeNote.id, false)}
                title="Move Note to Trash"
                className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </>
          )}

          {isTrashed && (
            <button
              onClick={() => restoreNote(activeNote.id)}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-foreground text-background font-semibold text-xs hover:opacity-90"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Restore</span>
            </button>
          )}
        </div>
      </header>

      {/* Editor Main Canvas Body */}
      <div className="flex-1 overflow-y-auto px-6 sm:px-12 py-8 max-w-5xl mx-auto w-full flex flex-col">
        {/* Note Title Input */}
        <input
          type="text"
          value={activeNote.title}
          onChange={handleTitleChange}
          readOnly={isTrashed}
          placeholder="Note Title"
          className={cn(
            'w-full bg-transparent text-3xl font-bold tracking-tight text-foreground placeholder:text-muted-foreground/40 border-none outline-none pb-2 focus:ring-0 leading-tight',
            isTrashed && 'opacity-80 cursor-default'
          )}
        />

        {/* Tags & Metadata bar */}
        <div className="flex items-center flex-wrap gap-2 pt-2 pb-6 border-b border-border/50 text-xs">
          {/* Tags list */}
          {Array.isArray(activeNote.tags) &&
            activeNote.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-surface-hover text-foreground font-mono text-[11px] border border-border/60"
              >
                <span>#{tag}</span>
                {!isTrashed && (
                  <button
                    onClick={() => handleRemoveTag(tag)}
                    className="text-muted-foreground hover:text-foreground p-0.5"
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                )}
              </span>
            ))}

          {/* Add Tag input */}
          {!isTrashed && (
            showTagInput ? (
              <div className="inline-flex items-center gap-1">
                <input
                  type="text"
                  autoFocus
                  placeholder="tag name..."
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleAddTag}
                  onBlur={() => {
                    if (!tagInput.trim()) setShowTagInput(false);
                  }}
                  className="bg-surface-hover border border-border px-2 py-0.5 rounded text-[11px] font-mono outline-none focus:ring-1 focus:ring-ring w-24"
                />
                <span className="text-[10px] text-muted-foreground">↵ to add</span>
              </div>
            ) : (
              <button
                onClick={() => setShowTagInput(true)}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] text-muted-foreground hover:text-foreground hover:bg-surface-hover border border-dashed border-border transition-colors font-mono"
              >
                <Plus className="w-3 h-3" />
                <span>Add Tag</span>
              </button>
            )
          )}
        </div>

        {/* View Content Area based on viewMode */}
        <div className={cn("flex-1 pt-6 pb-12 flex flex-col", `code-theme-${codeTheme}`)}>
          {/* MODE 1: MARKDOWN VIEWER / SOURCE (Default) */}
          {viewMode === 'markdown' && (
            <div className="flex-1 flex gap-2 min-h-[450px]">
              {/* Line Numbers Gutter */}
              <div className="markdown-line-numbers select-none">
                {lineNumbers.map((num) => (
                  <div key={num}>{num}</div>
                ))}
              </div>

              {/* Monospace Markdown Textarea */}
              <textarea
                ref={textareaRef}
                value={activeNote.content || ''}
                onChange={(e) => handleContentChange(e.target.value)}
                onKeyDown={handleTextareaKeyDown}
                readOnly={isTrashed}
                placeholder="Write markdown here (# Heading, - List, ```code)..."
                className="markdown-textarea flex-1 w-full min-h-[450px] resize-none outline-none border-none focus:ring-0 p-0 overflow-hidden"
                spellCheck={false}
              />
            </div>
          )}

          {/* MODE 2: NORMAL (MILKDOWN WYSIWYG) */}
          {viewMode === 'rich' && (
            <div className="pt-2 prose dark:prose-invert max-w-none text-foreground">
              <MilkdownEditor
                key={activeNote.id}
                noteId={activeNote.id}
                initialContent={activeNote.content}
                readOnly={isTrashed}
                onChange={handleContentChange}
              />
            </div>
          )}

          {/* MODE 3: SPLIT VIEW (Source on Left, Rendered on Right) */}
          {viewMode === 'split' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 min-h-[450px]">
              {/* Left: Raw Markdown Editor */}
              <div className="flex gap-2 p-3 bg-surface-hover/40 rounded-xl border border-border/70 overflow-hidden">
                <div className="markdown-line-numbers select-none">
                  {lineNumbers.map((num) => (
                    <div key={num}>{num}</div>
                  ))}
                </div>
                <textarea
                  ref={splitTextareaRef}
                  value={activeNote.content || ''}
                  onChange={(e) => handleContentChange(e.target.value)}
                  onKeyDown={handleTextareaKeyDown}
                  readOnly={isTrashed}
                  placeholder="Markdown source..."
                  className="markdown-textarea flex-1 w-full min-h-[400px] resize-none outline-none border-none focus:ring-0 p-0 overflow-hidden"
                  spellCheck={false}
                />
              </div>

              {/* Right: WYSIWYG Rendered Preview */}
              <div className="p-4 bg-surface-hover/20 rounded-xl border border-border/70 overflow-y-auto prose dark:prose-invert max-w-none text-foreground">
                <MilkdownEditor
                  key={`split_${activeNote.id}`}
                  noteId={`split_${activeNote.id}`}
                  initialContent={activeNote.content}
                  readOnly={true}
                  onChange={() => {}}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Status Bar: Sync Status + Words, Lines, Characters counts */}
      <footer className="h-8 px-4 border-t border-border bg-surface-sidebar flex items-center justify-between text-[11px] font-mono text-muted-foreground select-none shrink-0">
        {/* Left: Sync Status */}
        <div className="flex items-center gap-2">
          {!isTrashed ? (
            <>
              <div className="flex items-center gap-1.5">
                <span
                  className={cn(
                    'w-1.5 h-1.5 rounded-full',
                    isSaving ? 'bg-amber-400 animate-ping' : 'bg-emerald-500'
                  )}
                />
                <span className="font-medium text-foreground">
                  {isSaving ? 'Saving...' : 'Saved'}
                </span>
              </div>
              {lastSavedAt && (
                <>
                  <span>•</span>
                  <span>at {lastSavedAt}</span>
                </>
              )}
            </>
          ) : (
            <span className="text-destructive font-semibold">Note is in Trash (Read-Only)</span>
          )}
        </div>

        {/* Right: Document Metrics */}
        <div className="flex items-center gap-3">
          <span>{stats.words} words</span>
          <span>•</span>
          <span>{stats.lines} lines</span>
          <span>•</span>
          <span>{stats.chars} chars</span>
        </div>
      </footer>
    </div>
  );
};
