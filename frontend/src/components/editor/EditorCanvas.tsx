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
  ChevronDown,
  Pencil,
} from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useNotesStore } from '@/store/useNotesStore';
import { MilkdownEditor } from './MilkdownEditor';
import { ImageLightboxModal } from './ImageLightboxModal';
import { DocumentViewerModal } from './DocumentViewerModal';
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
    activeDocumentViewer,
    setActiveDocumentViewer,
    uploadAndInsertMedia,
    uploadAndProcessPdf,
    triggerMediaOcr,
    triggerDocumentOcr,
    cancelActiveMediaUpload,
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

  interface AttachedMediaPrompt {
    type: 'image' | 'pdf';
    filename: string;
    mediaId?: string;
    docIdentifier?: string;
    url?: string;
    pageCount?: number;
  }
  const [pendingOcrMedia, setPendingOcrMedia] = useState<AttachedMediaPrompt | null>(null);
  const [isExtractingText, setIsExtractingText] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const splitTextareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleProcessAndInsertFile = async (file: File | Blob) => {
    try {
      const fileNameStr = (file as File).name || 'file';
      const isPdf =
        file.type === 'application/pdf' ||
        fileNameStr.toLowerCase().endsWith('.pdf');

      let targetNote = activeNote;
      if (!targetNote) {
        targetNote = await createNewNote(
          undefined,
          fileNameStr.replace(/\.[^/.]+$/, '') || (isPdf ? 'Document Note' : 'Image Note')
        );
      }

      let insertion = '';
      if (isPdf) {
        setUploadStatusMsg('Attaching PDF & generating preview...');
        const res = await uploadAndProcessPdf(file, fileNameStr, targetNote?.id, false);
        insertion = `\n\n${res.markdown_insertion}\n`;
        setPendingOcrMedia({
          type: 'pdf',
          filename: fileNameStr,
          docIdentifier: res.document.id || res.document.filename,
          url: res.document.url,
          pageCount: res.document.page_count,
        });
        setUploadStatusMsg(null);
      } else {
        setUploadStatusMsg('Attaching image...');
        const res = await uploadAndInsertMedia(file, fileNameStr, targetNote?.id, false);
        insertion = `\n\n![${res.filename}](${res.url})\n`;
        setPendingOcrMedia({
          type: 'image',
          filename: res.filename,
          mediaId: res.mediaId,
          url: res.url,
        });
        setUploadStatusMsg(null);
      }

      const currentContent = targetNote?.content || '';
      handleContentChange(currentContent + insertion);
      setExternalEditCounter((c) => c + 1);
    } catch (err: any) {
      console.error('Failed to upload and process file:', err);
      setUploadStatusMsg(`Failed to attach file: ${err?.message || 'Upload error'}`);
      setTimeout(() => setUploadStatusMsg(null), 5000);
    }
  };

  const handleTriggerPendingOcr = async () => {
    if (!pendingOcrMedia || !activeNote) return;
    setIsExtractingText(true);
    try {
      let extracted = '';
      if (pendingOcrMedia.type === 'pdf') {
        extracted = await triggerDocumentOcr(pendingOcrMedia.docIdentifier || pendingOcrMedia.filename);
      } else if (pendingOcrMedia.mediaId) {
        extracted = await triggerMediaOcr(pendingOcrMedia.mediaId);
      }

      if (extracted && extracted.trim()) {
        const headerTitle = pendingOcrMedia.type === 'pdf' ? 'Extracted Document Content' : 'Extracted Content';
        const ocrBlock = `\n\n## ${headerTitle} (GLM-OCR)\n${extracted.trim()}\n`;
        const currentContent = activeNote.content || '';
        handleContentChange(currentContent + ocrBlock);
        setExternalEditCounter((c) => c + 1);
      }
      setPendingOcrMedia(null);
    } catch (err: any) {
      console.error('OCR extraction failed:', err);
    } finally {
      setIsExtractingText(false);
    }
  };



  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      await handleProcessAndInsertFile(file);
      e.target.value = '';
    }
  };

  const handlePaste = async (e: React.ClipboardEvent) => {
    if (isTrashed || !activeNote) return;
    if (e.clipboardData.files && e.clipboardData.files.length > 0) {
      const file = e.clipboardData.files[0];
      if (file.type.startsWith('image/') || file.type === 'application/pdf') {
        e.preventDefault();
        await handleProcessAndInsertFile(file);
      }
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    if (isTrashed || !activeNote) return;
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('image/') || file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        e.preventDefault();
        await handleProcessAndInsertFile(file);
      }
    }
  };

  const handleContainerClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;

    // 1. Click on an image element
    if (target.tagName === 'IMG') {
      const img = target as HTMLImageElement;
      const src = img.getAttribute('src') || '';
      const alt = img.getAttribute('alt') || '';
      const parentLink = img.closest('a');
      const href = parentLink?.getAttribute('href') || '';

      const isPdf =
        src.includes('_thumb.png') ||
        src.endsWith('.pdf') ||
        href.endsWith('.pdf') ||
        alt.includes('PDF Document') ||
        alt.toLowerCase().includes('.pdf');

      if (isPdf) {
        e.preventDefault();
        e.stopPropagation();
        const docUrl = href.endsWith('.pdf') ? href : src;
        const cleanName = alt.replace(/PDF Document:\s*/i, '').trim() || docUrl.split('/').pop() || 'document.pdf';
        setActiveDocumentViewer({
          url: docUrl,
          filename: cleanName,
        });
        return;
      }

      // Standard image
      e.preventDefault();
      e.stopPropagation();
      setActiveLightboxImage({
        url: src,
        filename: alt || 'image.png',
      });
      return;
    }

    // 2. Click on an anchor link
    const anchor = target.closest('a') as HTMLAnchorElement | null;
    if (anchor) {
      const href = anchor.getAttribute('href') || '';
      if (href.endsWith('.pdf') || (href.includes('/api/media/') && href.includes('.pdf'))) {
        e.preventDefault();
        e.stopPropagation();
        setActiveDocumentViewer({
          url: href,
          filename: anchor.innerText?.trim() || href.split('/').pop() || 'document.pdf',
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

  // ⌘S (Save), F2 (Rename Note), ⌘N / ⌃N / ⌥N / ⌘⇧N (New Note)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        if (!isTrashed && activeNote) {
          saveCurrentNoteRemote();
        }
      } else if (e.key === 'F2') {
        e.preventDefault();
        if (!isTrashed) {
          setActiveModal('rename-note');
        }
      } else {
        const isKeyN = e.key === 'n' || e.key === 'N' || e.code === 'KeyN' || e.key === '˜' || e.key === 'ñ';
        if ((e.metaKey || e.ctrlKey || e.altKey) && isKeyN) {
          e.preventDefault();
          e.stopPropagation();
          setActiveModal('new-note');
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [isTrashed, activeNote, saveCurrentNoteRemote, setActiveModal]);

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
        {/* Left: Sidebar toggle + Breadcrumbs (Category + Inline Editable Title + Tags Popover) */}
        <div className="flex items-center gap-2 truncate min-w-0">
          <button
            onClick={toggleSidebar}
            title={sidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors shrink-0"
          >
            <PanelLeft className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-1 text-xs text-muted-foreground truncate min-w-0">
            <Folder className="w-3.5 h-3.5 shrink-0 opacity-70" />
            {!isTrashed ? (
              <DropdownMenu.Root>
                <DropdownMenu.Trigger asChild>
                  <button className="hover:text-foreground font-medium capitalize truncate underline decoration-dotted decoration-border underline-offset-2 cursor-pointer shrink-0">
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
              <span className="capitalize font-medium shrink-0">{activeNote.category || 'personal'}</span>
            )}
            <span className="opacity-40">/</span>

            {/* Note Title display in breadcrumb (Clickable to open Rename Modal) */}
            {!isTrashed ? (
              <button
                onClick={() => setActiveModal('rename-note')}
                title="Click to rename note (F2)"
                className="text-foreground hover:bg-surface-hover font-semibold text-xs px-2 py-1 rounded-md inline-flex items-center gap-1.5 truncate max-w-[200px] sm:max-w-[280px] transition-colors cursor-pointer group"
              >
                <span className="truncate">{activeNote.title || 'Untitled Note'}</span>
                <Pencil className="w-3 h-3 text-muted-foreground/40 group-hover:text-foreground shrink-0 transition-colors" />
              </button>
            ) : (
              <span className="text-foreground font-semibold truncate max-w-[200px] sm:max-w-[280px] px-1.5 py-1">
                {activeNote.title || 'Untitled Note'}
              </span>
            )}
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

        {/* Right: Attach Image / Document + Consolidated Hamburger Menu */}
        <div className="flex items-center gap-1.5 shrink-0">
          {!isTrashed ? (
            <>
              {/* Hidden File Input for Image & PDF Upload */}
              <input
                type="file"
                ref={fileInputRef}
                accept="image/*,application/pdf,.pdf"
                className="hidden"
                onChange={handleFileSelect}
              />

              {/* Attach Media / PDF Button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploadingMedia}
                title="Attach Media / PDF Document (GLM-OCR)"
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
                    <span className="hidden sm:inline">Attach File</span>
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
                      onClick={() => setActiveModal('rename-note')}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2.5">
                        <Pencil className="w-3.5 h-3.5 shrink-0" />
                        <span>Rename Note (Edit Title)</span>
                      </div>
                      <kbd className="text-[10px] font-mono text-muted-foreground">F2</kbd>
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
                      onClick={() => setActiveModal('tags')}
                      className="px-2.5 py-1.5 rounded-md cursor-pointer outline-none hover:bg-surface-hover flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2.5">
                        <Tag className="w-3.5 h-3.5 shrink-0" />
                        <span>Manage Tags</span>
                      </div>
                      <span className="text-[10px] font-mono text-muted-foreground px-1.5 py-0.5 rounded bg-surface-hover border border-border/50">
                        {Array.isArray(activeNote.tags) ? activeNote.tags.length : 0}
                      </span>
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
          "flex-1 overflow-y-auto py-4 w-full flex flex-col transition-all duration-200",
          isFocusMode
            ? "px-8 sm:px-16 lg:px-24 max-w-7xl mx-auto"
            : "px-6 sm:px-12 max-w-5xl mx-auto"
        )}
      >
        {/* Status messages & Interactive OCR Prompt Banner */}
        {(autoTagMsg || uploadStatusMsg || pendingOcrMedia) && (
          <div className="space-y-2 pb-3 text-xs">
            {pendingOcrMedia && (
              <div className="flex items-center justify-between gap-3 px-3 py-2 rounded-xl bg-surface-hover/95 border border-primary/40 text-xs shadow-sm animate-in fade-in slide-in-from-top-1">
                <div className="flex items-center gap-2 truncate">
                  <Sparkles className="w-4 h-4 text-primary shrink-0 animate-pulse" />
                  <span className="font-semibold text-foreground truncate">
                    {pendingOcrMedia.type === 'pdf'
                      ? `Attached "${pendingOcrMedia.filename}" (${pendingOcrMedia.pageCount || 1} pages)`
                      : `Attached "${pendingOcrMedia.filename}"`}
                  </span>
                  <span className="text-muted-foreground hidden sm:inline">— Extract text with GLM-OCR?</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={handleTriggerPendingOcr}
                    disabled={isExtractingText}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 text-xs font-semibold cursor-pointer transition-all shadow-xs disabled:opacity-50"
                  >
                    {isExtractingText ? (
                      <>
                        <Loader2 className="w-3 h-3 animate-spin shrink-0" />
                        <span>Extracting...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3 h-3 shrink-0" />
                        <span>Extract Text (GLM-OCR)</span>
                      </>
                    )}
                  </button>

                  {pendingOcrMedia.type === 'pdf' && (
                    <button
                      onClick={() => {
                        setActiveDocumentViewer({
                          url: pendingOcrMedia.url,
                          filename: pendingOcrMedia.filename,
                          docId: pendingOcrMedia.docIdentifier,
                        });
                        setPendingOcrMedia(null);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-surface border border-border hover:bg-surface-hover text-xs text-foreground cursor-pointer transition-colors"
                      title="Open Document Lightbox"
                    >
                      View Pages
                    </button>
                  )}

                  <button
                    onClick={() => setPendingOcrMedia(null)}
                    className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface transition-colors cursor-pointer"
                    title="Dismiss"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2">
              {autoTagMsg && (
                <span className="text-[11px] font-mono text-foreground font-medium px-2 py-0.5 rounded-md bg-surface-hover border border-border animate-in fade-in">
                  ✓ {autoTagMsg}
                </span>
              )}
              {uploadStatusMsg && (
                <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded-md bg-surface-hover border border-border text-foreground animate-in fade-in flex items-center gap-2">
                  {isUploadingMedia && <Loader2 className="w-3 h-3 animate-spin text-foreground shrink-0" />}
                  <span>{uploadStatusMsg}</span>
                  {isUploadingMedia && (
                    <button
                      onClick={() => {
                        cancelActiveMediaUpload();
                        setUploadStatusMsg('Upload cancelled');
                        setTimeout(() => setUploadStatusMsg(null), 3000);
                      }}
                      className="ml-1 px-1.5 py-0.2 rounded bg-destructive/10 text-destructive hover:bg-destructive/20 text-[10px] font-sans font-semibold cursor-pointer transition-colors"
                      title="Cancel processing"
                    >
                      Cancel
                    </button>
                  )}
                </span>
              )}
            </div>
          </div>
        )}


        {/* View Content Area based on viewMode */}
        <div
          onClick={handleContainerClick}
          onDrop={handleDrop}
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
                onPaste={handlePaste}
                onDrop={handleDrop}
                readOnly={isTrashed}
                placeholder="Write markdown here (# Heading, - List, ```code, paste/drop images or PDF documents)..."

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
                  onPaste={handlePaste}
                  onDrop={handleDrop}

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

      {/* Multi-Page PDF Document & GLM-OCR Lightbox Modal */}
      <DocumentViewerModal />
    </div>
  );
};

