import React, { useMemo, useState, useRef, useEffect } from 'react';
import {
  PanelLeft,
  Download,
  Trash2,
  History,
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
  Copy,
  Check,
  Sparkles,
  Wand2,
  AlignLeft,
  ListOrdered,
  Expand,
  Shrink,
  Minimize,
  Tag,
  Image as ImageIcon,
  Menu,
  Star,
  Pin,
} from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useNotesStore } from '@/store/useNotesStore';
import { MilkdownEditor } from './MilkdownEditor';
import { ImageLightboxModal } from './ImageLightboxModal';
import { TaskProgressWidget } from '@/components/common/TaskProgressWidget';
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
    isOrganizingNote,
    isGeneratingTitle,
    isTransformingSelection,
    isAutoTagging,
    isUploadingMedia,
    lastSavedAt,
    sidebarCollapsed,
    toggleSidebar,
    updateActiveNote,
    saveCurrentNoteRemote,
    organizeNote,
    generateNoteTitle,
    transformSelectedText,
    requestDeleteNote,
    requestEmptyTrash,
    restoreNote,
    exportActiveNote,
    setActiveModal,
    createNewNote,
    codeTheme,
    isFocusMode,
    toggleFocusMode,
    setIsFocusMode,
    autoTagActiveNote,
    setActiveLightboxImage,
    uploadAndInsertMedia,
    togglePin,
    toggleFavorite,
  } = useNotesStore();


  const [tagInput, setTagInput] = useState('');
  const [showTagInput, setShowTagInput] = useState(false);
  const [autoTagMsg, setAutoTagMsg] = useState<string | null>(null);
  const [customAiPrompt, setCustomAiPrompt] = useState('');
  const [showCustomPromptInput, setShowCustomPromptInput] = useState(false);
  const [copiedId, setCopiedId] = useState(false);
  const [viewMode, setViewMode] = useState<EditorViewMode>('rich'); // Default as Rich WYSIWYG Viewer
  const [externalEditCounter, setExternalEditCounter] = useState<number>(0);
  const [uploadStatusMsg, setUploadStatusMsg] = useState<string | null>(null);


  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const splitTextareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleProcessAndInsertImage = async (file: File | Blob) => {
    try {
      setUploadStatusMsg('Uploading image & extracting text with GLM-OCR...');
      let targetNote = activeNote;
      if (!targetNote) {
        targetNote = await createNewNote(undefined, (file as File).name?.replace(/\.[^/.]+$/, '') || 'Image Note');
      }
      const res = await uploadAndInsertMedia(file, (file as File).name || 'image.png', targetNote?.id);
      let insertion = `\n\n![${res.filename}](${res.url})\n`;
      if (res.ocrText && res.ocrText.trim()) {
        insertion += `\n## Extracted Content (GLM-OCR)\n${res.ocrText}\n\n`;
      }
      const currentContent = targetNote?.content || '';
      handleContentChange(currentContent + insertion);
      setExternalEditCounter((c) => c + 1);
      setUploadStatusMsg('Image attached & GLM-OCR processed successfully!');
      setTimeout(() => setUploadStatusMsg(null), 4000);
    } catch (err: any) {
      console.error('Failed to upload and OCR image:', err);
      setUploadStatusMsg(`Failed to attach image: ${err?.message || 'Upload error'}`);
      setTimeout(() => setUploadStatusMsg(null), 5000);
    }
  };


  const handleImageFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      await handleProcessAndInsertImage(file);
      e.target.value = '';
    }
  };

  const handleImagePaste = async (e: React.ClipboardEvent) => {
    if (isTrashed || !activeNote) return;
    if (e.clipboardData.files && e.clipboardData.files.length > 0) {
      const file = e.clipboardData.files[0];
      if (file.type.startsWith('image/')) {
        e.preventDefault();
        await handleProcessAndInsertImage(file);
      }
    }
  };

  const handleImageDrop = async (e: React.DragEvent) => {
    if (isTrashed || !activeNote) return;
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('image/')) {
        e.preventDefault();
        await handleProcessAndInsertImage(file);
      }
    }
  };

  const handleContainerClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.tagName === 'IMG') {
      const img = target as HTMLImageElement;
      const src = img.getAttribute('src');
      if (src) {
        setActiveLightboxImage({
          url: src,
          filename: img.getAttribute('alt') || 'image.png',
        });
      }
    }
  };

  // Selected Paragraph / Text Floating AI Organizer State
  interface TextSelectionState {
    text: string;
    start: number;
    end: number;
    targetEl: HTMLTextAreaElement | null;
    top: number;
    left: number;
    visible: boolean;
  }
  const [selectionState, setSelectionState] = useState<TextSelectionState | null>(null);
  const [selectionPrompt, setSelectionPrompt] = useState('');
  const [showSelectionPromptInput, setShowSelectionPromptInput] = useState(false);
  const [selectionActionSuccess, setSelectionActionSuccess] = useState<string | null>(null);
  const selectionToolbarRef = useRef<HTMLDivElement>(null);

  // Find active note in regular notes OR trash notes based on active view
  const activeNote = useMemo(() => {
    if (!activeNoteId) return null;
    if (activeView === 'trash') {
      return trashNotes.find((n) => n.id === activeNoteId) || null;
    }
    const fromNotes = notes.find((n) => n.id === activeNoteId);
    if (fromNotes) return fromNotes;
    return null;
  }, [notes, trashNotes, activeNoteId, activeView]);

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

  // Word, lines, character counts, and reading time
  const stats = useMemo(() => {
    if (!activeNote) return { words: 0, chars: 0, lines: 1, readTimeMinutes: 1 };
    const text = (activeNote.title + ' ' + activeNote.content).trim();
    const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
    const chars = (activeNote.content || '').length;
    const lines = (activeNote.content || '').split('\n').length || 1;
    const readTimeMinutes = Math.max(1, Math.ceil(words / 200));
    return { words, chars, lines, readTimeMinutes };
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

  // Handle text selection in raw markdown textareas
  const handleTextareaSelect = (e: React.SyntheticEvent<HTMLTextAreaElement>) => {
    if (isTrashed || isTransformingSelection) return;
    const target = e.currentTarget;
    const start = target.selectionStart;
    const end = target.selectionEnd;

    if (start !== end && start >= 0 && end > start) {
      const selected = target.value.substring(start, end);
      if (selected.trim().length >= 2) {
        const rect = target.getBoundingClientRect();
        const textBefore = target.value.substring(0, start);
        const lineIndex = textBefore.split('\n').length - 1;
        const approximateLineHeight = 22;
        const topOffset = rect.top + Math.min(rect.height - 70, Math.max(10, lineIndex * approximateLineHeight - 45));

        setSelectionState({
          text: selected,
          start,
          end,
          targetEl: target,
          top: Math.max(80, Math.min(window.innerHeight - 90, topOffset)),
          left: Math.max(20, Math.min(window.innerWidth - 480, rect.left + 40)),
          visible: true,
        });
        return;
      }
    }

    if (!showSelectionPromptInput && !isTransformingSelection) {
      setSelectionState(null);
    }
  };

  // Transform or generate title on selected text
  const handleTransformSelection = async (mode: string, customInstruction?: string) => {
    if (!selectionState || !activeNote) return;
    const { text, start, end, targetEl } = selectionState;

    if (mode === 'title') {
      const newTitle = await generateNoteTitle(activeNote.id, text, customInstruction);
      if (newTitle) {
        setSelectionActionSuccess('Note Title Updated!');
        setTimeout(() => {
          setSelectionActionSuccess(null);
          setSelectionState(null);
        }, 1800);
      }
      return;
    }

    const transformed = await transformSelectedText(text, customInstruction, mode, activeNote.content);
    if (transformed !== undefined) {
      const full = activeNote.content || '';
      const updated = full.substring(0, start) + transformed + full.substring(end);
      handleContentChange(updated);
      setSelectionActionSuccess('Transformed!');
      setTimeout(() => {
        setSelectionActionSuccess(null);
        setSelectionState(null);
        if (targetEl) {
          targetEl.focus();
          targetEl.selectionStart = start;
          targetEl.selectionEnd = start + transformed.length;
        }
      }, 1200);
    }
  };

  // Dismiss selection toolbar if clicking outside
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        selectionToolbarRef.current &&
        !selectionToolbarRef.current.contains(e.target as Node) &&
        textareaRef.current !== e.target &&
        splitTextareaRef.current !== e.target
      ) {
        if (!isTransformingSelection) {
          setSelectionState(null);
          setShowSelectionPromptInput(false);
        }
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [isTransformingSelection]);

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

  const handleAutoTag = async () => {
    if (isTrashed || !activeNote || !activeNote.content?.trim()) return;
    setAutoTagMsg(null);
    try {
      const res = await autoTagActiveNote(activeNote.id, activeNote.content, activeNote.title);
      if (res && res.tags) {
        setAutoTagMsg(`Auto-tagged ${res.tags.length} item${res.tags.length !== 1 ? 's' : ''}!`);
        setTimeout(() => setAutoTagMsg(null), 3500);
      }
    } catch (e) {
      console.error('Failed to auto-tag note with AI:', e);
    }
  };


  if (!activeNote) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center bg-surface-editor text-muted-foreground p-8 text-center select-none">
        <div className="w-16 h-16 rounded-2xl bg-surface-hover flex items-center justify-center mb-4 border border-border">
          {activeView === 'trash' ? (
            <Trash2 className="w-8 h-8 opacity-40 text-destructive" />
          ) : (
            <FileText className="w-8 h-8 opacity-40" />
          )}
        </div>
        <h3 className="text-base font-semibold text-foreground mb-1">
          {activeView === 'trash'
            ? trashNotes.length === 0
              ? 'Trash is Empty'
              : 'No Trashed Note Selected'
            : 'No Note Selected'}
        </h3>
        <p className="text-xs max-w-sm mb-5 text-muted-foreground">
          {activeView === 'trash'
            ? trashNotes.length === 0
              ? 'Notes you delete will appear here until permanently deleted.'
              : 'Select a deleted note from the list to preview or restore it.'
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
                  <button className="hover:text-foreground font-medium capitalize truncate underline decoration-dotted decoration-border underline-offset-2 cursor-pointer">
                    {activeNote.category || 'personal'}
                  </button>
                </DropdownMenu.Trigger>
                <DropdownMenu.Portal>
                  <DropdownMenu.Content
                    align="start"
                    className="z-50 min-w-[150px] bg-popover text-popover-foreground rounded-lg p-1 border border-border shadow-xl text-xs"
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
                          cat.category === activeNote.category && 'font-bold bg-surface-selected'
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
              <span className="capitalize font-medium">{activeNote.category || 'personal'}</span>
            )}
            <span>/</span>
            <span className="text-foreground font-semibold truncate max-w-[200px]">
              {activeNote.title || 'Untitled Note'}
            </span>
          </div>
        </div>

        {/* Center: Monochrome View Mode Switcher */}
        <div className="flex items-center bg-surface-hover p-0.5 rounded-lg border border-border/80">
          <button
            onClick={() => setViewMode('markdown')}
            title="Markdown Source"
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer',
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
            title="Normal / Rendered Editor"
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer',
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
            title="Split Source & Rendered Preview"
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer',
              viewMode === 'split'
                ? 'bg-card text-foreground shadow-xs font-semibold'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Columns className="w-3.5 h-3.5" />
            <span>Split</span>
          </button>
        </div>

        {/* Right: Attach Image + Consolidated Hamburger Menu */}
        <div className="flex items-center gap-1.5 shrink-0">
          {!isTrashed ? (
            <>
              {/* Hidden File Input for Image Upload */}
              <input
                type="file"
                ref={fileInputRef}
                accept="image/*"
                className="hidden"
                onChange={handleImageFileSelect}
              />

              {/* Attach Image Button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploadingMedia}
                title="Attach Image (GLM-OCR)"
                className={cn(
                  'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border border-border transition-colors cursor-pointer',
                  isUploadingMedia
                    ? 'bg-surface-selected text-foreground cursor-wait'
                    : 'bg-surface-hover hover:bg-surface-hover/80 text-foreground'
                )}
              >
                {isUploadingMedia ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span className="hidden sm:inline">Processing...</span>
                  </>
                ) : (
                  <>
                    <ImageIcon className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Attach Image</span>
                  </>
                )}
              </button>

              {/* Consolidated Hamburger Menu */}
              <DropdownMenu.Root>
                <DropdownMenu.Trigger asChild>
                  <button
                    title="Menu & Note Tools"
                    className="p-1.5 rounded-lg border border-border bg-surface-hover hover:bg-surface-hover/80 text-foreground transition-colors cursor-pointer"
                  >
                    <Menu className="w-4 h-4" />
                  </button>
                </DropdownMenu.Trigger>

                <DropdownMenu.Portal>
                  <DropdownMenu.Content
                    align="end"
                    className="z-50 min-w-[240px] bg-popover text-popover-foreground rounded-lg p-1.5 border border-border shadow-2xl text-xs space-y-1 animate-in fade-in zoom-in-95"
                  >
                    {/* Section 1: AI Actions */}
                    <div className="px-2 py-1 text-[10px] text-muted-foreground uppercase font-bold tracking-wider">
                      AI Actions
                    </div>

                    <DropdownMenu.Item
                      onClick={() => organizeNote(activeNote.id, undefined, true, true)}
                      disabled={isOrganizingNote}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2.5"
                    >
                      <Sparkles className="w-3.5 h-3.5 shrink-0" />
                      <div>
                        <span className="font-semibold block">Polish & Organize</span>
                        <span className="text-[10px] text-muted-foreground">Restructure and auto-title</span>
                      </div>
                    </DropdownMenu.Item>

                    <DropdownMenu.Item
                      onClick={() => generateNoteTitle(activeNote.id, activeNote.content)}
                      disabled={isGeneratingTitle}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2.5"
                    >
                      <FileText className="w-3.5 h-3.5 shrink-0" />
                      <div>
                        <span className="font-semibold block">Generate Title</span>
                        <span className="text-[10px] text-muted-foreground">Extract smart title from content</span>
                      </div>
                    </DropdownMenu.Item>

                    <DropdownMenu.Item
                      onClick={handleAutoTag}
                      disabled={isAutoTagging || !activeNote.content?.trim()}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2.5"
                    >
                      <Tag className="w-3.5 h-3.5 shrink-0" />
                      <div>
                        <span className="font-semibold block">Auto-Tag Note</span>
                        <span className="text-[10px] text-muted-foreground">Extract tags & auto-categorize</span>
                      </div>
                    </DropdownMenu.Item>

                    <DropdownMenu.Item
                      onClick={() => organizeNote(activeNote.id, "Summarize into concise executive key takeaways and actionable points")}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2.5"
                    >
                      <ListOrdered className="w-3.5 h-3.5 shrink-0" />
                      <div>
                        <span className="font-semibold block">Summarize Key Points</span>
                        <span className="text-[10px] text-muted-foreground">Extract core bullet insights</span>
                      </div>
                    </DropdownMenu.Item>

                    <DropdownMenu.Item
                      onClick={() => setShowCustomPromptInput(true)}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2.5"
                    >
                      <Wand2 className="w-3.5 h-3.5 shrink-0" />
                      <div>
                        <span className="font-semibold block">Custom AI Prompt...</span>
                        <span className="text-[10px] text-muted-foreground">Apply custom instructions</span>
                      </div>
                    </DropdownMenu.Item>

                    <DropdownMenu.Separator className="h-px bg-border my-1" />

                    {/* Section 2: Note Operations */}
                    <div className="px-2 py-1 text-[10px] text-muted-foreground uppercase font-bold tracking-wider">
                      Note Operations
                    </div>

                    <DropdownMenu.Item
                      onClick={() => saveCurrentNoteRemote()}
                      disabled={isSaving}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2.5">
                        <Save className="w-3.5 h-3.5 shrink-0" />
                        <span>Save Note</span>
                      </div>
                      <kbd className="text-[10px] font-mono text-muted-foreground">⌘S</kbd>
                    </DropdownMenu.Item>

                    <DropdownMenu.Item
                      onClick={() => setActiveModal('versions')}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2.5"
                    >
                      <History className="w-3.5 h-3.5 shrink-0" />
                      <span>Version History & Revert</span>
                    </DropdownMenu.Item>

                    <DropdownMenu.Item
                      onClick={exportActiveNote}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2.5"
                    >
                      <Download className="w-3.5 h-3.5 shrink-0" />
                      <span>Export as Markdown (.md)</span>
                    </DropdownMenu.Item>

                    <DropdownMenu.Item
                      onClick={() => togglePin(activeNote.id)}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2.5">
                        <Pin className="w-3.5 h-3.5 shrink-0" />
                        <span>{activeNote.isPinned ? 'Unpin Note' : 'Pin Note'}</span>
                      </div>
                      <kbd className="text-[10px] font-mono text-muted-foreground">⌘⇧P</kbd>
                    </DropdownMenu.Item>

                    <DropdownMenu.Item
                      onClick={() => toggleFavorite(activeNote.id)}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2.5">
                        <Star className="w-3.5 h-3.5 shrink-0" />
                        <span>{activeNote.isFavorite ? 'Remove from Favorites' : 'Add to Favorites'}</span>
                      </div>
                      <kbd className="text-[10px] font-mono text-muted-foreground">⌘⇧S</kbd>
                    </DropdownMenu.Item>

                    <DropdownMenu.Item
                      onClick={() => {
                        navigator.clipboard.writeText(activeNote.id);
                        setCopiedId(true);
                        setTimeout(() => setCopiedId(false), 2000);
                      }}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2.5"
                    >
                      <Copy className="w-3.5 h-3.5 shrink-0" />
                      <span>Copy Note ID</span>
                    </DropdownMenu.Item>

                    <DropdownMenu.Separator className="h-px bg-border my-1" />

                    {/* Section 3: View & Delete */}
                    <DropdownMenu.Item
                      onClick={toggleFocusMode}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2.5">
                        {isFocusMode ? <Shrink className="w-3.5 h-3.5 shrink-0" /> : <Expand className="w-3.5 h-3.5 shrink-0" />}
                        <span>{isFocusMode ? 'Exit Zen Focus' : 'Zen Focus Mode'}</span>
                      </div>
                      <kbd className="text-[10px] font-mono text-muted-foreground">⌘⇧Z</kbd>
                    </DropdownMenu.Item>

                    <DropdownMenu.Item
                      onClick={() => requestDeleteNote(activeNote.id, false)}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center gap-2.5 text-muted-foreground hover:text-foreground"
                    >
                      <Trash2 className="w-3.5 h-3.5 shrink-0" />
                      <span>Move to Trash</span>
                    </DropdownMenu.Item>
                  </DropdownMenu.Content>
                </DropdownMenu.Portal>
              </DropdownMenu.Root>
            </>
          ) : (
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => restoreNote(activeNote.id)}
                title="Restore this note to Active Notes"
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-foreground text-background font-semibold text-xs hover:opacity-90 transition-opacity cursor-pointer shadow-2xs"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Restore</span>
              </button>

              <button
                onClick={() => requestDeleteNote(activeNote.id, true)}
                title="Permanently delete this note"
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-foreground/10 text-foreground hover:bg-foreground/20 font-semibold text-xs transition-colors cursor-pointer border border-border"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Permanently</span>
              </button>

              {trashNotes.length > 1 && (
                <button
                  onClick={() => requestEmptyTrash()}
                  title="Empty all notes from Trash"
                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface-hover text-xs transition-colors cursor-pointer"
                >
                  <span>Empty Trash</span>
                </button>
              )}
            </div>
          )}
        </div>
      </header>


      {/* Custom AI Instruction Banner */}
      {showCustomPromptInput && (
        <div className="px-6 sm:px-12 py-2.5 bg-surface-sidebar border-b border-border flex items-center gap-2 animate-in slide-in-from-top-1 text-xs">
          <Sparkles className="w-4 h-4 text-foreground shrink-0" />
          <input
            type="text"
            value={customAiPrompt}
            onChange={(e) => setCustomAiPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && customAiPrompt.trim()) {
                organizeNote(activeNote.id, customAiPrompt.trim());
                setShowCustomPromptInput(false);
                setCustomAiPrompt('');
              }
            }}
            placeholder="e.g. Extract key formulas into a cheat-sheet, summarize for quick revision..."
            className="flex-1 px-3 py-1.5 rounded-md bg-surface-hover border border-border text-xs text-foreground outline-none focus:ring-1 focus:ring-ring"
            autoFocus
          />
          <button
            onClick={() => {
              if (customAiPrompt.trim()) {
                organizeNote(activeNote.id, customAiPrompt.trim());
                setShowCustomPromptInput(false);
                setCustomAiPrompt('');
              }
            }}
            disabled={isOrganizingNote || !customAiPrompt.trim()}
            className="px-3 py-1.5 rounded-md bg-foreground text-background font-semibold text-xs hover:opacity-90 disabled:opacity-50 cursor-pointer"
          >
            Apply
          </button>
          <button
            onClick={() => setShowCustomPromptInput(false)}
            className="p-1 rounded text-muted-foreground hover:text-foreground cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Zen Focus Mode Top Bar */}
      {isFocusMode && (
        <div className="px-6 sm:px-12 py-2 bg-card/95 backdrop-blur-md border-b border-border flex items-center justify-between text-xs animate-in slide-in-from-top-1 select-none shadow-xs">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 font-semibold text-foreground">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Zen Focus Mode</span>
            </span>
            <span className="text-muted-foreground/60">•</span>
            <span className="text-muted-foreground font-mono text-[11px]">
              {stats.words.toLocaleString()} words &nbsp;•&nbsp; {stats.chars.toLocaleString()} chars &nbsp;•&nbsp; ~{stats.readTimeMinutes} min read
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsFocusMode(false)}
              title="Exit Zen Focus Mode (Esc / ⌘⇧Z)"
              className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-surface-hover hover:bg-surface-hover/80 text-foreground border border-border transition-all active:scale-95 cursor-pointer"
            >
              <Shrink className="w-3.5 h-3.5" />
              <span>Exit Focus</span>
              <kbd className="ml-1 px-1 py-0.2 rounded text-[10px] bg-card border border-border/70 font-mono text-muted-foreground">Esc</kbd>
            </button>
          </div>
        </div>
      )}

      {/* Editor Main Canvas Body */}
      <div
        className={cn(
          "flex-1 overflow-y-auto py-8 w-full flex flex-col transition-all duration-200",
          isFocusMode
            ? "px-8 sm:px-16 lg:px-24 max-w-7xl mx-auto"
            : "px-6 sm:px-12 max-w-5xl mx-auto"
        )}
      >
        {/* Note Title Input */}
        <div className="flex items-center justify-between gap-3 group relative pb-2">
          <input
            type="text"
            value={activeNote.title}
            onChange={handleTitleChange}
            readOnly={isTrashed}
            placeholder="Note Title"
            className={cn(
              'flex-1 bg-transparent font-bold tracking-tight text-foreground placeholder:text-muted-foreground/40 border-none outline-none focus:ring-0 leading-tight transition-all',
              isFocusMode ? 'text-4xl sm:text-5xl font-extrabold pb-1' : 'text-3xl',
              isTrashed && 'opacity-80 cursor-default'
            )}
          />
        </div>

        {/* Tags & Metadata bar */}
        <div className="flex items-center flex-wrap gap-2 pt-2 pb-6 border-b border-border/50 text-xs">
          {/* Memory ID Chip with Copy Action */}
          <button
            onClick={() => {
              if (activeNote?.id) {
                navigator.clipboard.writeText(activeNote.id);
                setCopiedId(true);
                setTimeout(() => setCopiedId(false), 2000);
              }
            }}
            title="Click to copy Memory ID"
            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-surface-hover hover:bg-surface-hover/80 text-muted-foreground hover:text-foreground font-mono text-[11px] border border-border/60 transition-colors cursor-pointer"
          >
            {copiedId ? (
              <>
                <Check className="w-3 h-3 text-foreground" />
                <span className="text-foreground font-medium">Copied ID!</span>
              </>
            ) : (
              <>
                <span className="opacity-60">ID:</span>
                <span className="font-semibold text-foreground/80">{activeNote.id}</span>
                <Copy className="w-2.5 h-2.5 opacity-60" />
              </>
            )}
          </button>

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
                    className="text-muted-foreground hover:text-foreground p-0.5 cursor-pointer"
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
              <div className="inline-flex items-center gap-1.5">
                <button
                  onClick={() => setShowTagInput(true)}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] text-muted-foreground hover:text-foreground hover:bg-surface-hover border border-dashed border-border transition-colors font-mono cursor-pointer"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add Tag</span>
                </button>

                {autoTagMsg && (
                  <span className="text-[11px] font-mono text-foreground font-medium px-2 py-0.5 rounded-md bg-surface-hover border border-border animate-in fade-in">
                    ✓ {autoTagMsg}
                  </span>
                )}

                {uploadStatusMsg && (
                  <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded-md bg-surface-hover border border-border text-foreground animate-in fade-in flex items-center gap-1.5">
                    {uploadStatusMsg.includes('Uploading') && <Loader2 className="w-3 h-3 animate-spin text-foreground" />}
                    <span>{uploadStatusMsg}</span>
                  </span>
                )}
              </div>
            )
          )}


        </div>

        {/* View Content Area based on viewMode */}
        <div
          onClick={handleContainerClick}
          onDrop={handleImageDrop}
          onDragOver={(e) => e.preventDefault()}
          className={cn("flex-1 pt-6 pb-12 flex flex-col relative", `code-theme-${codeTheme}`)}
        >
          {/* MODE 1: MARKDOWN VIEWER / SOURCE (Default) */}
          {viewMode === 'markdown' && (
            <div className={cn("flex-1 flex gap-3 min-h-[500px]", isFocusMode && "min-h-[650px]")}>
              {/* Line Numbers Gutter */}
              <div
                className={cn(
                  "markdown-line-numbers select-none transition-all",
                  isFocusMode ? "text-[13px] sm:text-[14px] !leading-[1.85rem]" : "text-[13px] !leading-[1.625rem]"
                )}
              >
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
                onSelect={handleTextareaSelect}
                onMouseUp={handleTextareaSelect}
                onKeyUp={handleTextareaSelect}
                onPaste={handleImagePaste}
                onDrop={handleImageDrop}
                readOnly={isTrashed}
                placeholder="Write markdown here (# Heading, - List, ```code, paste/drop images)..."
                className={cn(
                  "markdown-textarea flex-1 w-full min-h-[500px] resize-none outline-none border-none focus:ring-0 p-0 overflow-hidden transition-all",
                  isFocusMode
                    ? "text-[14px] sm:text-[15px] lg:text-[16px] !leading-[1.85rem] tracking-wide"
                    : "text-[13px] !leading-[1.625rem]"
                )}
                spellCheck={false}
              />
            </div>
          )}

          {/* MODE 2: NORMAL (MILKDOWN WYSIWYG) */}
          {viewMode === 'rich' && (
            <div className={cn("pt-2 max-w-none text-foreground transition-all", isFocusMode ? "prose prose-lg dark:prose-invert max-w-none text-base sm:text-lg leading-relaxed" : "prose dark:prose-invert max-w-none")}>
              <MilkdownEditor
                key={`${activeNote.id}_${externalEditCounter}`}
                noteId={`${activeNote.id}_${externalEditCounter}`}
                initialContent={activeNote.content}
                readOnly={isTrashed}
                onChange={handleContentChange}
              />
            </div>
          )}

          {/* MODE 3: SPLIT VIEW (Source on Left, Rendered on Right) */}
          {viewMode === 'split' && (
            <div className={cn("grid grid-cols-1 md:grid-cols-2 gap-6 min-h-[450px] transition-all", isFocusMode ? "gap-8 min-h-[650px]" : "min-h-[450px]")}>
              {/* Left: Raw Markdown Editor */}
              <div className={cn("flex gap-2 p-3 bg-surface-hover/40 rounded-xl border border-border/70 overflow-hidden", isFocusMode && "p-4")}>
                <div
                  className={cn(
                    "markdown-line-numbers select-none",
                    isFocusMode ? "text-[13px] sm:text-[14px] !leading-[1.85rem]" : "text-[13px] !leading-[1.625rem]"
                  )}
                >
                  {lineNumbers.map((num) => (
                    <div key={num}>{num}</div>
                  ))}
                </div>
                <textarea
                  ref={splitTextareaRef}
                  value={activeNote.content || ''}
                  onChange={(e) => handleContentChange(e.target.value)}
                  onKeyDown={handleTextareaKeyDown}
                  onSelect={handleTextareaSelect}
                  onMouseUp={handleTextareaSelect}
                  onKeyUp={handleTextareaSelect}
                  onPaste={handleImagePaste}
                  onDrop={handleImageDrop}
                  readOnly={isTrashed}
                  placeholder="Markdown source..."
                  className={cn(
                    "markdown-textarea flex-1 w-full min-h-[400px] resize-none outline-none border-none focus:ring-0 p-0 overflow-hidden",
                    isFocusMode
                      ? "text-[14px] sm:text-[15px] !leading-[1.85rem]"
                      : "text-[13px] !leading-[1.625rem]"
                  )}
                  spellCheck={false}
                />
              </div>

              {/* Right: WYSIWYG Rendered Preview */}
              <div className={cn("p-4 bg-surface-hover/20 rounded-xl border border-border/70 overflow-y-auto max-w-none text-foreground", isFocusMode ? "p-6 prose prose-lg dark:prose-invert max-w-none text-base" : "prose dark:prose-invert max-w-none")}>
                <MilkdownEditor
                  key={`split_${activeNote.id}_${externalEditCounter}`}
                  noteId={`split_${activeNote.id}_${externalEditCounter}`}
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
        {/* Left: Sync Status + Activity & Task Progress */}
        <div className="flex items-center gap-2.5">
          {!isTrashed ? (
            <>
              <div className="flex items-center gap-1.5">
                <span
                  className={cn(
                    'w-1.5 h-1.5 rounded-full',
                    isSaving ? 'bg-muted-foreground animate-ping' : 'bg-foreground'
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
              <span>•</span>
              <TaskProgressWidget />
            </>
          ) : (
            <span className="text-muted-foreground font-semibold">Note is in Trash (Read-Only)</span>
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

      {/* Floating Selected Paragraph / Text AI Organizer Toolbar */}
      {selectionState?.visible && !isTrashed && (
        <div
          ref={selectionToolbarRef}
          style={{
            top: `${selectionState.top}px`,
            left: `${selectionState.left}px`,
          }}
          className="fixed z-50 animate-in fade-in zoom-in-95 duration-150 shadow-2xl rounded-xl border border-border bg-card/95 backdrop-blur-md px-2 py-1.5 flex items-center gap-1.5 text-xs text-foreground ring-1 ring-border"
        >
          {isTransformingSelection ? (
            <div className="flex items-center gap-2 px-2.5 py-1 text-xs text-foreground font-medium select-none">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-foreground" />
              <span>Organizing selection with AI...</span>
            </div>
          ) : selectionActionSuccess ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-foreground font-semibold animate-in fade-in select-none">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{selectionActionSuccess}</span>
            </div>
          ) : showSelectionPromptInput ? (
            <div className="flex items-center gap-1.5 min-w-[280px]">
              <Sparkles className="w-3.5 h-3.5 text-foreground shrink-0" />
              <input
                type="text"
                value={selectionPrompt}
                onChange={(e) => setSelectionPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && selectionPrompt.trim()) {
                    handleTransformSelection('custom', selectionPrompt.trim());
                    setShowSelectionPromptInput(false);
                    setSelectionPrompt('');
                  } else if (e.key === 'Escape') {
                    setShowSelectionPromptInput(false);
                  }
                }}
                placeholder="Custom prompt for selection..."
                className="flex-1 px-2 py-1 rounded bg-surface-hover border border-border text-xs text-foreground outline-none focus:ring-1 focus:ring-ring"
                autoFocus
              />
              <button
                onClick={() => {
                  if (selectionPrompt.trim()) {
                    handleTransformSelection('custom', selectionPrompt.trim());
                    setShowSelectionPromptInput(false);
                    setSelectionPrompt('');
                  }
                }}
                disabled={!selectionPrompt.trim()}
                className="px-2.5 py-1 rounded bg-foreground text-background font-semibold text-[11px] hover:opacity-90 disabled:opacity-50 cursor-pointer"
              >
                Apply
              </button>
              <button
                onClick={() => setShowSelectionPromptInput(false)}
                className="p-1 rounded text-muted-foreground hover:text-foreground cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-1 text-[11px] font-semibold text-muted-foreground px-1 border-r border-border select-none">
                <Sparkles className="w-3 h-3 text-foreground" />
                <span>AI Selection</span>
              </div>

              <button
                onClick={() => handleTransformSelection('polish')}
                title="Polish and clean grammar, typography, and formatting"
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-surface-hover hover:bg-surface-hover/80 text-foreground transition-colors cursor-pointer"
              >
                <Wand2 className="w-3 h-3 text-foreground" />
                <span>Polish</span>
              </button>

              <button
                onClick={() => handleTransformSelection('summarize')}
                title="Summarize selection into concise key takeaway bullet points"
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-surface-hover hover:bg-surface-hover/80 text-foreground transition-colors cursor-pointer"
              >
                <ListOrdered className="w-3 h-3 text-foreground" />
                <span>Summarize</span>
              </button>

              <button
                onClick={() => handleTransformSelection('technical')}
                title="Format as technical documentation with clear headings, code syntax, and parameters"
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-surface-hover hover:bg-surface-hover/80 text-foreground transition-colors cursor-pointer"
              >
                <AlignLeft className="w-3 h-3 text-foreground" />
                <span>Tech Docs</span>
              </button>

              <button
                onClick={() => handleTransformSelection('title')}
                title="Generate and set note title from this selected paragraph"
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-surface-hover hover:bg-surface-hover/80 text-foreground transition-colors cursor-pointer"
              >
                <FileText className="w-3 h-3 text-foreground" />
                <span>Make Title</span>
              </button>

              <button
                onClick={() => setShowSelectionPromptInput(true)}
                title="Apply custom AI prompt to this selection"
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-surface-hover hover:bg-surface-hover/80 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              >
                <Sparkles className="w-3 h-3" />
                <span>Custom...</span>
              </button>

              <button
                onClick={() => setSelectionState(null)}
                title="Dismiss"
                className="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors ml-0.5 cursor-pointer"
              >
                <X className="w-3 h-3" />
              </button>
            </>
          )}
        </div>
      )}


      {/* Uncompressed Image & Local Ollama GLM-OCR Lightbox Modal */}
      <ImageLightboxModal />
    </div>
  );
};
