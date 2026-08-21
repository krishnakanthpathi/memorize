import { create } from 'zustand';
import { api } from '@/services/api';
import { documentApi, DocumentUploadResponse } from '@/services/documentApi';
import { AppIconType, AsyncTask, CategoryStat, CodeTheme, Note, SystemView, ThemeMode, ToastNotification } from '@/types';


interface NotesState {
  // Theme & Appearance
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  codeTheme: CodeTheme;
  setCodeTheme: (theme: CodeTheme) => void;
  appIcon: AppIconType;
  setAppIcon: (icon: AppIconType) => void;

  // Notes data
  notes: Note[];
  trashNotes: Note[];
  activeNoteId: string | null;
  categories: CategoryStat[];
  activeView: SystemView;
  selectedCategory: string | null;
  selectedTag: string | null;
  searchQuery: string;

  // App UI State
  isLoading: boolean;
  isSaving: boolean;
  isOrganizingNote: boolean;
  isGeneratingTitle: boolean;
  isTransformingSelection: boolean;
  isAutoTagging: boolean;
  isUploadingMedia: boolean;
  isOnline: boolean;
  lastSavedAt: string | null;
  sidebarCollapsed: boolean;
  isFullScreen: boolean;
  isFocusMode: boolean;
  activeModal: 'search' | 'versions' | 'audit' | 'backup' | 'models' | 'settings' | 'new-category' | 'shortcuts' | 'merge' | 'tags' | 'rename-note' | 'new-note' | null;
  activeLightboxImage: { url: string; filename: string; mediaId?: string; ocrText?: string } | null;
  setActiveLightboxImage: (img: { url: string; filename: string; mediaId?: string; ocrText?: string } | null) => void;
  activeDocumentViewer: { docId?: string; filename?: string; url?: string; initialPage?: number } | null;
  setActiveDocumentViewer: (doc: { docId?: string; filename?: string; url?: string; initialPage?: number } | null) => void;
  uploadAndInsertMedia: (file: File | Blob, filename?: string, memoryId?: string, runOcr?: boolean) => Promise<{ url: string; filename: string; ocrText?: string; mediaId?: string }>;
  uploadAndProcessPdf: (file: File | Blob, filename?: string, memoryId?: string, runOcr?: boolean) => Promise<DocumentUploadResponse>;
  triggerMediaOcr: (mediaId: string, customPrompt?: string) => Promise<string>;
  triggerDocumentOcr: (docIdentifier: string, customPrompt?: string) => Promise<string>;
  cancelActiveMediaUpload: () => void;




  // Background Task & Toast Notification Center
  tasks: AsyncTask[];
  toasts: ToastNotification[];
  startTask: (title: string, description?: string) => string;
  completeTask: (id: string, resultSummary?: string, showToast?: boolean, toastTitle?: string) => void;
  failTask: (id: string, errorMsg: string, showToast?: boolean) => void;
  addToast: (toast: Omit<ToastNotification, 'id' | 'createdAt'>) => string;
  dismissToast: (id: string) => void;
  clearFinishedTasks: () => void;

  // Multi-selection & Merge State
  selectedNoteIds: string[];
  toggleNoteSelection: (id: string) => void;
  selectAllNotes: (ids?: string[]) => void;
  clearNoteSelection: () => void;
  openMergeModal: (initialIds?: string[]) => void;

  // LLM Config
  selectedModel: string;
  selectedProvider: string;
  setSelectedModel: (model: string) => void;
  setSelectedProvider: (provider: string) => void;

  // Persistence sets
  pinnedIds: string[];
  favoriteIds: string[];

  // Delete Confirmation State
  notePendingDelete: {
    id?: string;
    ids?: string[];
    title: string;
    count?: number;
    permanent: boolean;
    isEmptyTrash?: boolean;
  } | null;
  requestDeleteNote: (id: string, permanent?: boolean) => void;
  requestDeleteBatch: (ids: string[], permanent?: boolean) => void;
  requestEmptyTrash: () => void;
  cancelDeleteNote: () => void;
  confirmDeleteNote: () => Promise<void>;

  // Actions
  fetchNotes: () => Promise<void>;
  fetchCategories: () => Promise<void>;
  selectNote: (id: string | null) => void;
  createNewNote: (category?: string, initialTitle?: string, initialTags?: string[]) => Note;
  updateActiveNote: (fields: Partial<Note>, syncRemote?: boolean) => void;
  saveCurrentNoteRemote: () => Promise<void>;
  organizeNote: (memoryId: string, instruction?: string, useAi?: boolean, generateTitle?: boolean) => Promise<any>;
  generateNoteTitle: (memoryId: string, customContent?: string, instruction?: string) => Promise<string | undefined>;
  transformSelectedText: (selectedText: string, instruction?: string, mode?: string, fullContext?: string) => Promise<string | undefined>;
  autoTagActiveNote: (memoryId: string, customContent?: string, title?: string) => Promise<{ tags: string[]; category?: string } | undefined>;
  deleteNote: (id: string, permanent?: boolean) => Promise<void>;
  deleteBatchNotes: (ids: string[], permanent?: boolean) => Promise<void>;
  emptyTrash: () => void;
  restoreNote: (id: string) => void;
  restoreBatchNotes: (ids: string[]) => Promise<void>;
  togglePin: (id: string) => void;
  toggleFavorite: (id: string) => void;
  setActiveView: (view: SystemView) => void;
  setSelectedCategory: (category: string | null) => void;
  setSelectedTag: (tag: string | null) => void;
  setSearchQuery: (query: string) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  setIsFullScreen: (full: boolean) => void;
  setIsFocusMode: (focus: boolean) => void;
  toggleFullScreen: () => void;
  toggleFocusMode: () => void;
  setActiveModal: (modal: NotesState['activeModal']) => void;
  exportActiveNote: () => void;
}


// Local storage keys
const THEME_KEY = 'memorize_theme';
const PINNED_KEY = 'memorize_pinned_ids';
const FAVORITES_KEY = 'memorize_favorite_ids';
const TRASH_KEY = 'memorize_trash_notes';
const MODEL_KEY = 'memorize_selected_model';
const PROVIDER_KEY = 'memorize_selected_provider';

function getStoredTheme(): ThemeMode {
  const t = localStorage.getItem(THEME_KEY) as ThemeMode;
  if (t === 'light' || t === 'dark' || t === 'black') return t;
  return 'dark'; // Default is Dark Mode
}

function applyThemeClass(theme: ThemeMode) {
  const root = document.documentElement;
  root.classList.remove('dark', 'black');
  if (theme === 'dark') {
    root.classList.add('dark');
  } else if (theme === 'black') {
    root.classList.add('dark', 'black');
  }
}

function stripRedundantH1(content: string, title?: string): string {
  if (!content) return '';
  const lines = content.trim().split('\n');
  if (lines.length === 0) return '';
  const firstLine = lines[0].trim();
  if (firstLine.startsWith('# ') && !firstLine.startsWith('## ')) {
    const h1Text = firstLine.slice(2).trim();
    const cleanH1 = h1Text.toLowerCase().replace(/[^\w\s]/g, '').trim();
    const cleanTitle = (title || '').toLowerCase().replace(/[^\w\s]/g, '').trim();
    if (
      !cleanTitle ||
      cleanTitle === 'untitled note' ||
      cleanTitle === 'untitled memory' ||
      cleanH1 === cleanTitle ||
      cleanH1.includes(cleanTitle) ||
      cleanTitle.includes(cleanH1) ||
      cleanTitle.startsWith(cleanH1) ||
      cleanH1.startsWith(cleanTitle)
    ) {
      lines.shift();
      while (lines.length > 0 && !lines[0].trim()) {
        lines.shift();
      }
      return lines.join('\n').trim();
    }
  }
  return content.trim();
}

// Debounce helper for auto-saving
let saveTimer: any = null;
let activeUploadController: AbortController | null = null;

export const useNotesStore = create<NotesState>((set, get) => {

  const initialTheme = getStoredTheme();
  applyThemeClass(initialTheme);

  const initialPinned: string[] = JSON.parse(localStorage.getItem(PINNED_KEY) || '[]');
  const initialFavorites: string[] = JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]');
  const initialTrash: Note[] = JSON.parse(localStorage.getItem(TRASH_KEY) || '[]');
  const initialModel = localStorage.getItem(MODEL_KEY) || '';
  const initialProvider = localStorage.getItem(PROVIDER_KEY) || 'ollama';
  const initialCodeTheme = (localStorage.getItem('memorize_code_theme') as CodeTheme) || 'monokai';
  const initialAppIcon = (localStorage.getItem('memorize_app_icon') as AppIconType) || 'monogram';

  return {
    theme: initialTheme,
    setTheme: (theme) => {
      localStorage.setItem(THEME_KEY, theme);
      applyThemeClass(theme);
      set({ theme });
    },

    codeTheme: initialCodeTheme,
    setCodeTheme: (codeTheme) => {
      localStorage.setItem('memorize_code_theme', codeTheme);
      set({ codeTheme });
    },

    appIcon: initialAppIcon,
    setAppIcon: (appIcon) => {
      localStorage.setItem('memorize_app_icon', appIcon);
      set({ appIcon });
    },

    selectedModel: initialModel,
    selectedProvider: initialProvider,
    setSelectedModel: (model) => {
      localStorage.setItem(MODEL_KEY, model);
      set({ selectedModel: model });
    },
    setSelectedProvider: (provider) => {
      localStorage.setItem(PROVIDER_KEY, provider);
      set({ selectedProvider: provider });
    },

    notes: [],
    trashNotes: initialTrash,
    activeNoteId: null,
    categories: [],
    activeView: 'all',
    selectedCategory: null,
    selectedTag: null,
    searchQuery: '',

    isLoading: false,
    isSaving: false,
    isOrganizingNote: false,
    isGeneratingTitle: false,
    isTransformingSelection: false,
    isAutoTagging: false,
    isUploadingMedia: false,
    isOnline: true,
    lastSavedAt: null,
    sidebarCollapsed: false,
    isFullScreen: false,
    isFocusMode: false,
    activeModal: null,
    activeLightboxImage: null,
    activeDocumentViewer: null,


    pinnedIds: initialPinned,
    favoriteIds: initialFavorites,

    // Task & Toast Notification Center
    tasks: [],
    toasts: [],

    startTask: (title: string, description?: string) => {
      const id = `task_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const newTask: AsyncTask = {
        id,
        title,
        description,
        status: 'running',
        startedAt: Date.now(),
      };
      set((state) => ({ tasks: [newTask, ...state.tasks.slice(0, 19)] }));
      return id;
    },

    completeTask: (id: string, resultSummary?: string, showToast: boolean = true, toastTitle?: string) => {
      const task = get().tasks.find((t) => t.id === id);
      set((state) => ({
        tasks: state.tasks.map((t) =>
          t.id === id
            ? { ...t, status: 'success' as const, completedAt: Date.now(), resultSummary }
            : t
        ),
      }));

      if (showToast) {
        get().addToast({
          title: toastTitle || task?.title || 'Task Completed',
          description: resultSummary || task?.description,
          type: 'success',
        });
      }
    },

    failTask: (id: string, errorMsg: string, showToast: boolean = true) => {
      const task = get().tasks.find((t) => t.id === id);
      set((state) => ({
        tasks: state.tasks.map((t) =>
          t.id === id
            ? { ...t, status: 'error' as const, completedAt: Date.now(), error: errorMsg }
            : t
        ),
      }));

      if (showToast) {
        get().addToast({
          title: `${task?.title || 'Task'} Failed`,
          description: errorMsg,
          type: 'error',
        });
      }
    },

    addToast: (toast) => {
      const id = `toast_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const newToast: ToastNotification = {
        ...toast,
        id,
        createdAt: Date.now(),
        duration: toast.duration || 4500,
      };
      set((state) => ({ toasts: [newToast, ...state.toasts.slice(0, 4)] }));
      return id;
    },

    dismissToast: (id: string) => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    },

    clearFinishedTasks: () => {
      set((state) => ({ tasks: state.tasks.filter((t) => t.status === 'running') }));
    },

    fetchNotes: async () => {
      set({ isLoading: true });
      try {
        const rawNotes = await api.getMemories();
        const { pinnedIds, favoriteIds } = get();

        const notes = rawNotes.map((n) => ({
          ...n,
          content: stripRedundantH1(n.content, n.title),
          isPinned: pinnedIds.includes(n.id),
          isFavorite: favoriteIds.includes(n.id),
        }));


        set((state) => {
          let activeNoteId = state.activeNoteId;
          if (state.activeView === 'trash') {
            if (!state.trashNotes.some((n) => n.id === activeNoteId)) {
              activeNoteId = state.trashNotes.length > 0 ? state.trashNotes[0].id : null;
            }
          } else {
            if (!activeNoteId && notes.length > 0) {
              activeNoteId = notes[0].id;
            } else if (activeNoteId && !notes.some((n) => n.id === activeNoteId)) {
              activeNoteId = notes.length > 0 ? notes[0].id : null;
            }
          }
          return {
            notes,
            activeNoteId,
            isLoading: false,
            isOnline: true,
          };
        });
      } catch (err) {
        console.error('Failed to fetch notes from backend:', err);
        set({ isLoading: false, isOnline: false });
      }
    },

    fetchCategories: async () => {
      try {
        const rawCategories = await api.getCategories();
        const { notes } = get();

        // Calculate count per category
        const counts: Record<string, number> = {};
        notes.forEach((n) => {
          const cat = (n.category || 'personal').toLowerCase();
          counts[cat] = (counts[cat] || 0) + 1;
        });

        // Merge rawCategories and active categories
        const catMap = new Map<string, number>();
        rawCategories.forEach((c) => {
          catMap.set(c.category.toLowerCase(), counts[c.category.toLowerCase()] || c.count || 0);
        });

        Object.keys(counts).forEach((cat) => {
          if (!catMap.has(cat)) {
            catMap.set(cat, counts[cat]);
          }
        });

        const categories: CategoryStat[] = Array.from(catMap.entries()).map(([category, count]) => ({
          category,
          count,
        }));

        set({ categories, isOnline: true });
      } catch (err) {
        console.error('Failed to fetch categories:', err);
      }
    },

    selectNote: (id) => {
      set({ activeNoteId: id });
    },

    createNewNote: (categoryParam, initialTitle, initialTags = []) => {
      const { selectedCategory, notes, activeView } = get();
      const cat = categoryParam || (selectedCategory && selectedCategory !== 'all' ? selectedCategory : 'personal');
      const newId = `memo_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const now = new Date().toISOString();

      const newNote: Note = {
        id: newId,
        title: initialTitle || 'New Note',
        content: '',
        category: cat,
        folderId: cat,
        tags: initialTags,
        keywords: [],
        isPinned: false,
        isFavorite: false,
        createdAt: now,
        updatedAt: now,
      };

      set({
        notes: [newNote, ...notes.filter((n) => n.id !== newId)],
        activeNoteId: newId,
        activeView: (activeView === 'trash' || activeView === 'settings' || activeView === 'docs') ? 'all' : activeView,
        searchQuery: '',
      });

      // Save asynchronously to backend with action: 'insert'
      api.saveMemory({
        title: newNote.title,
        content: newNote.content,
        category: newNote.category,
        tags: newNote.tags,
        action: 'insert',
        memory_id: newId,
      }).then(() => {
        get().fetchCategories();
      }).catch((e) => console.error('Failed to create note on backend:', e));

      return newNote;
    },

    updateActiveNote: (fields, syncRemote = true) => {
      const { activeNoteId, notes } = get();
      if (!activeNoteId) return;

      const now = new Date().toISOString();
      const updatedNotes = notes.map((n) => {
        if (n.id === activeNoteId) {
          return {
            ...n,
            ...fields,
            updatedAt: now,
          };
        }
        return n;
      });

      set({ notes: updatedNotes });

      if (syncRemote) {
        if (saveTimer) clearTimeout(saveTimer);
        set({ isSaving: true });
        saveTimer = setTimeout(() => {
          get().saveCurrentNoteRemote();
        }, 800);
      }
    },

    saveCurrentNoteRemote: async () => {
      const { activeNoteId, notes, activeView } = get();
      if (activeView === 'trash') return; // Don't auto-save trashed notes
      const current = notes.find((n) => n.id === activeNoteId);
      if (!current) {
        set({ isSaving: false });
        return;
      }

      const taskId = get().startTask('Saving Note', `Saving "${current.title || 'Untitled'}" and updating vector embeddings...`);
      set({ isSaving: true });
      try {
        await api.saveMemory({
          title: current.title,
          content: current.content,
          category: current.category,
          tags: current.tags,
          action: 'overwrite',
          memory_id: current.id,
        });
        set({
          isSaving: false,
          lastSavedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isOnline: true,
        });
        get().completeTask(taskId, `Note "${current.title || 'Untitled'}" saved & vector index updated`, false);
        get().fetchCategories();
      } catch (err: any) {
        console.error('Remote save failed:', err);
        set({ isSaving: false, isOnline: false });
        get().failTask(taskId, err?.message || 'Failed to save note');
      }
    },

    organizeNote: async (memoryId: string, instruction?: string, useAi: boolean = true, generateTitle: boolean = false) => {
      const { notes } = get();
      const target = notes.find((n) => n.id === memoryId);
      if (!target) return;

      const taskTitle = instruction ? 'Custom AI Transform' : 'AI Polish & Restructure';
      const taskId = get().startTask(taskTitle, `Analyzing and restructuring "${target.title || 'Untitled'}"...`);
      set({ isOrganizingNote: true });
      try {
        const res = await api.organizeMemory(memoryId, instruction, useAi, generateTitle);
        if (res.status === 'success' && res.content) {
          const updatedNote: Note = {
            ...target,
            title: res.title || target.title,
            content: res.content,
            snippet: res.content_preview || res.content.slice(0, 180),
            updatedAt: new Date().toISOString(),
          };

          set((state) => ({
            notes: state.notes.map((n) => (n.id === memoryId ? updatedNote : n)),
            isOrganizingNote: false,
          }));

          get().completeTask(
            taskId,
            `Successfully polished "${res.title || target.title}"`,
            true,
            'AI Polish Complete'
          );
          await get().fetchCategories();
          return res;
        }
      } catch (err: any) {
        console.error('Failed to organize note with AI:', err);
        get().failTask(taskId, err?.message || 'AI organize failed');
      } finally {
        set({ isOrganizingNote: false });
      }
    },

    generateNoteTitle: async (memoryId: string, customContent?: string, instruction?: string) => {
      const { notes, activeNoteId } = get();
      const target = notes.find((n) => n.id === memoryId);
      const contentToUse = customContent !== undefined ? customContent : target?.content || '';
      if (!contentToUse.trim()) return;

      if (saveTimer) {
        clearTimeout(saveTimer);
        saveTimer = null;
      }

      const taskId = get().startTask('Generate Title', `Extracting smart title from content...`);
      set({ isGeneratingTitle: true });
      try {
        const res = await api.generateTitle(
          contentToUse,
          target?.title,
          instruction,
          memoryId,
          true
        );
        if (res.status === 'success' && res.title) {
          const cleanTitle = res.title;
          const updatedNotes = get().notes.map((n) =>
            n.id === memoryId
              ? {
                  ...n,
                  title: cleanTitle,
                  content: contentToUse,
                  updatedAt: new Date().toISOString(),
                }
              : n
          );
          set({
            notes: updatedNotes,
            isGeneratingTitle: false,
          });
          get().completeTask(taskId, `Title updated to "${cleanTitle}"`, true, 'Title Generated');
          await get().fetchCategories();
          return cleanTitle;
        }
      } catch (err: any) {
        console.error('Failed to generate title with AI:', err);
        get().failTask(taskId, err?.message || 'Title generation failed');
      } finally {
        set({ isGeneratingTitle: false });
      }
    },

    transformSelectedText: async (selectedText: string, instruction?: string, mode: string = 'polish', fullContext?: string) => {
      if (!selectedText || !selectedText.trim()) return;
      const taskId = get().startTask('AI Selection Transform', `Applying ${mode} transform to selected paragraph...`);
      set({ isTransformingSelection: true });
      try {
        const res = await api.transformSelection(selectedText, instruction, mode, fullContext);
        if (res.status === 'success') {
          get().completeTask(taskId, `Applied ${mode} transformation`, true, 'Selection Transformed');
          return res.transformed_text;
        }
      } catch (err: any) {
        console.error('Failed to transform selected text:', err);
        get().failTask(taskId, err?.message || 'Selection transform failed');
      } finally {
        set({ isTransformingSelection: false });
      }
    },

    autoTagActiveNote: async (memoryId: string, customContent?: string, title?: string) => {
      const { notes } = get();
      const target = notes.find((n) => n.id === memoryId);
      const contentToUse = customContent !== undefined ? customContent : target?.content || '';
      if (!contentToUse.trim()) return;

      const taskId = get().startTask('Auto-Tag & Classify', `Extracting tags and determining category for "${target?.title || 'Note'}"...`);
      set({ isAutoTagging: true });
      try {
        const res = await api.autoTagNote({
          content: contentToUse,
          title: title || target?.title,
          memory_id: memoryId,
          save_to_memory: true,
        });

        if (res.status === 'success') {
          const generatedTags = res.tags || [];
          const detectedCat = res.category;

          if (target) {
            // Merge existing tags and new tags without duplicates
            const currentTags = Array.isArray(target.tags) ? target.tags : [];
            const mergedTags = [...currentTags];
            for (const gt of generatedTags) {
              if (!mergedTags.includes(gt)) {
                mergedTags.push(gt);
              }
            }

            const updatedNote: Note = {
              ...target,
              tags: mergedTags,
              category: detectedCat || target.category,
              folderId: detectedCat || target.category,
              updatedAt: new Date().toISOString(),
            };

            set((state) => ({
              notes: state.notes.map((n) => (n.id === memoryId ? updatedNote : n)),
              isAutoTagging: false,
            }));
            await get().fetchCategories();
          }

          get().completeTask(
            taskId,
            `Applied ${generatedTags.length} tags: ${generatedTags.map(t => `#${t}`).join(' ')} (${detectedCat || 'personal'})`,
            true,
            'Auto-Tagging Complete'
          );
          return { tags: generatedTags, category: detectedCat };
        }
      } catch (err: any) {
        console.error('Failed to auto-tag note with AI:', err);
        get().failTask(taskId, err?.message || 'Auto-tagging failed');
      } finally {
        set({ isAutoTagging: false });
      }
    },

    setActiveLightboxImage: (img) =>
      set({ activeLightboxImage: img, activeDocumentViewer: img ? null : get().activeDocumentViewer }),
    setActiveDocumentViewer: (doc) =>
      set({ activeDocumentViewer: doc, activeLightboxImage: doc ? null : get().activeLightboxImage }),


    uploadAndInsertMedia: async (file: File | Blob, filename?: string, memoryId?: string, runOcr: boolean = false) => {
      const fileNameStr = (file as File).name || filename || 'image';
      const taskId = get().startTask(
        runOcr ? 'GLM-OCR Vision Extraction' : 'Image Attachment',
        `Uploading "${fileNameStr}"...`
      );
      set({ isUploadingMedia: true });

      const controller = new AbortController();
      activeUploadController = controller;

      try {
        const res = await api.uploadMedia(file, filename, memoryId, runOcr, undefined, controller.signal);
        const media = res.media;
        const ocrText = res.ocr?.text || media.ocr_text || '';
        const charCount = ocrText.length;
        get().completeTask(
          taskId,
          charCount > 0
            ? `Attached "${media.original_filename || media.filename}" (${charCount.toLocaleString()} chars extracted)`
            : `Attached image "${media.original_filename || media.filename}"`,
          true,
          'Image Ready'
        );
        return {
          url: media.url,
          filename: media.original_filename || media.filename,
          ocrText,
          mediaId: media.id,
        };
      } catch (err: any) {
        if (err.name === 'AbortError' || controller.signal.aborted) {
          get().completeTask(taskId, 'Media upload cancelled by user', false);
          throw new Error('Upload cancelled');
        }
        console.error('Image upload failed:', err);
        get().failTask(taskId, err?.message || 'Failed to upload image');
        throw err;
      } finally {
        if (activeUploadController === controller) {
          activeUploadController = null;
        }
        set({ isUploadingMedia: false });
      }
    },

    uploadAndProcessPdf: async (file: File | Blob, filename?: string, memoryId?: string, runOcr: boolean = false) => {
      const fileNameStr = (file as File).name || filename || 'document.pdf';
      const taskId = get().startTask(
        'PDF Ingestion',
        `Uploading "${fileNameStr}" & generating page thumbnails...`
      );
      set({ isUploadingMedia: true });

      const controller = new AbortController();
      activeUploadController = controller;

      try {
        const res = await documentApi.uploadPdf(file, filename, memoryId, runOcr, undefined, 50, controller.signal);
        const pageCount = res.document.page_count;
        get().completeTask(
          taskId,
          `Ready: ${pageCount} page${pageCount > 1 ? 's' : ''} loaded`,
          true,
          'PDF Attached'
        );
        return res;
      } catch (err: any) {
        if (err.name === 'AbortError' || controller.signal.aborted) {
          get().completeTask(taskId, 'PDF processing cancelled by user', false);
          throw new Error('Processing cancelled');
        }
        console.error('PDF document processing failed:', err);
        get().failTask(taskId, err?.message || 'Failed to process PDF document');
        throw err;
      } finally {
        if (activeUploadController === controller) {
          activeUploadController = null;
        }
        set({ isUploadingMedia: false });
      }
    },

    triggerMediaOcr: async (mediaId: string, customPrompt?: string): Promise<string> => {
      const taskId = get().startTask('GLM-OCR Vision Extraction', `Extracting text with local Ollama GLM-OCR model...`);
      try {
        const res = await api.triggerMediaOcr(mediaId, customPrompt);
        const text = res?.ocr_text || '';
        get().completeTask(
          taskId,
          text.length > 0
            ? `Extracted ${text.length.toLocaleString()} characters`
            : `Completed GLM-OCR scan`,
          true,
          'GLM-OCR Complete'
        );
        return text;
      } catch (err: any) {
        console.error('Trigger media OCR failed:', err);
        get().failTask(taskId, err?.message || 'GLM-OCR extraction failed');
        throw err;
      }
    },

    triggerDocumentOcr: async (docIdentifier: string, customPrompt?: string): Promise<string> => {
      const taskId = get().startTask('Document GLM-OCR', `Extracting text across PDF pages with local Ollama GLM-OCR...`);
      try {
        const res = await documentApi.triggerDocumentOcr(docIdentifier, customPrompt);
        const text = res?.ocr_text || '';
        get().completeTask(
          taskId,
          `Processed ${res.total_pages || 1} page${(res.total_pages || 1) > 1 ? 's' : ''} (${text.length.toLocaleString()} characters)`,
          true,
          'Document OCR Complete'
        );
        return text;
      } catch (err: any) {
        console.error('Trigger document OCR failed:', err);
        get().failTask(taskId, err?.message || 'Document OCR extraction failed');
        throw err;
      }
    },


    cancelActiveMediaUpload: () => {
      if (activeUploadController) {
        activeUploadController.abort();
        activeUploadController = null;
      }
      set({ isUploadingMedia: false });
      set((state) => ({
        tasks: state.tasks.map((t) =>
          t.status === 'running' &&
          (t.title.includes('GLM-OCR') || t.title.includes('PDF') || t.title.includes('Vision'))
            ? { ...t, status: 'error', error: 'Cancelled by user', completedAt: Date.now() }
            : t
        ),
      }));
    },





    notePendingDelete: null,
    requestDeleteNote: (id, permanent = false) => {
      const { notes, trashNotes } = get();
      const target = notes.find((n) => n.id === id) || trashNotes.find((n) => n.id === id);
      const title = target?.title || 'Untitled Note';
      set({ notePendingDelete: { id, title, permanent, count: 1 } });
    },
    requestDeleteBatch: (ids, permanent = false) => {
      if (!ids || ids.length === 0) return;
      const count = ids.length;
      const title = `${count} selected note${count > 1 ? 's' : ''}`;
      set({ notePendingDelete: { ids, title, permanent, count } });
    },
    requestEmptyTrash: () => {
      const { trashNotes } = get();
      if (trashNotes.length === 0) return;
      set({
        notePendingDelete: {
          isEmptyTrash: true,
          title: `all ${trashNotes.length} trashed notes`,
          permanent: true,
          count: trashNotes.length,
        },
      });
    },
    cancelDeleteNote: () => {
      set({ notePendingDelete: null });
    },
    confirmDeleteNote: async () => {
      const { notePendingDelete, deleteNote, deleteBatchNotes, emptyTrash } = get();
      if (!notePendingDelete) return;
      const { id, ids, permanent, isEmptyTrash } = notePendingDelete;
      set({ notePendingDelete: null });

      if (isEmptyTrash) {
        emptyTrash();
      } else if (ids && ids.length > 0) {
        await deleteBatchNotes(ids, permanent);
      } else if (id) {
        await deleteNote(id, permanent);
      }
    },

    deleteNote: async (id, permanent = false) => {
      const { notes, trashNotes, activeNoteId, selectedNoteIds } = get();
      const target = notes.find((n) => n.id === id);

      if (!target && !permanent) return;

      if (!permanent && target) {
        // Move to trash
        const trashedNote = { ...target, isDeleted: true };
        const updatedTrash = [trashedNote, ...trashNotes.filter((n) => n.id !== id)];
        localStorage.setItem(TRASH_KEY, JSON.stringify(updatedTrash));
        const updatedNotes = notes.filter((n) => n.id !== id);

        const nextActiveId = activeNoteId === id
          ? (updatedNotes.length > 0 ? updatedNotes[0].id : null)
          : activeNoteId;

        set({
          notes: updatedNotes,
          trashNotes: updatedTrash,
          activeNoteId: nextActiveId,
          selectedNoteIds: selectedNoteIds.filter((x) => x !== id),
        });

        // Remote deletion
        try {
          await api.deleteMemory(id);
          get().fetchCategories();
        } catch (err) {
          console.error('Backend delete error:', err);
        }
      } else {
        // Permanent deletion from trash
        const updatedTrash = trashNotes.filter((n) => n.id !== id);
        localStorage.setItem(TRASH_KEY, JSON.stringify(updatedTrash));
        const nextActiveId = activeNoteId === id
          ? (updatedTrash.length > 0 ? updatedTrash[0].id : null)
          : activeNoteId;
        set({
          trashNotes: updatedTrash,
          activeNoteId: nextActiveId,
          selectedNoteIds: selectedNoteIds.filter((x) => x !== id),
        });
      }
    },

    deleteBatchNotes: async (ids, permanent = false) => {
      const { notes, trashNotes, activeNoteId, selectedNoteIds } = get();
      if (!ids || ids.length === 0) return;
      const idsSet = new Set(ids);

      if (!permanent) {
        // Move batch to trash
        const trashedBatch: Note[] = [];
        const remainingNotes = notes.filter((n) => {
          if (idsSet.has(n.id)) {
            trashedBatch.push({ ...n, isDeleted: true });
            return false;
          }
          return true;
        });

        const updatedTrash = [...trashedBatch, ...trashNotes.filter((n) => !idsSet.has(n.id))];
        localStorage.setItem(TRASH_KEY, JSON.stringify(updatedTrash));

        const nextActiveId = activeNoteId && idsSet.has(activeNoteId)
          ? (remainingNotes.length > 0 ? remainingNotes[0].id : null)
          : activeNoteId;

        set({
          notes: remainingNotes,
          trashNotes: updatedTrash,
          activeNoteId: nextActiveId,
          selectedNoteIds: selectedNoteIds.filter((x) => !idsSet.has(x)),
        });

        // Batch delete from backend
        try {
          await api.deleteBatchMemories(ids);
          get().fetchCategories();
        } catch (err) {
          console.error('Backend batch delete error:', err);
        }
      } else {
        // Permanent batch delete from trash
        const updatedTrash = trashNotes.filter((n) => !idsSet.has(n.id));
        localStorage.setItem(TRASH_KEY, JSON.stringify(updatedTrash));

        const nextActiveId = activeNoteId && idsSet.has(activeNoteId)
          ? (updatedTrash.length > 0 ? updatedTrash[0].id : null)
          : activeNoteId;

        set({
          trashNotes: updatedTrash,
          activeNoteId: nextActiveId,
          selectedNoteIds: selectedNoteIds.filter((x) => !idsSet.has(x)),
        });
      }
    },

    emptyTrash: () => {
      const { trashNotes, activeNoteId, activeView } = get();
      if (trashNotes.length === 0) return;

      localStorage.removeItem(TRASH_KEY);
      const isViewingTrashActiveNote = trashNotes.some((n) => n.id === activeNoteId);

      set({
        trashNotes: [],
        activeNoteId: isViewingTrashActiveNote ? null : activeNoteId,
        selectedNoteIds: activeView === 'trash' ? [] : get().selectedNoteIds,
      });

      // Clear any remote backend memories if needed
      get().fetchCategories();
    },

    restoreNote: (id) => {
      const { trashNotes, notes } = get();
      const target = trashNotes.find((n) => n.id === id);
      if (!target) return;

      const restored: Note = { ...target, isDeleted: false };
      const updatedTrash = trashNotes.filter((n) => n.id !== id);
      localStorage.setItem(TRASH_KEY, JSON.stringify(updatedTrash));

      set({
        notes: [restored, ...notes],
        trashNotes: updatedTrash,
        activeNoteId: id,
        activeView: 'all',
      });

      // Save back to backend
      api.saveMemory({
        title: restored.title,
        content: restored.content,
        category: restored.category,
        tags: restored.tags,
        action: 'insert',
        memory_id: restored.id,
      }).then(() => {
        get().fetchCategories();
      }).catch((e) => console.error('Failed to re-insert restored note:', e));
    },

    restoreBatchNotes: async (ids) => {
      const { trashNotes, notes, selectedNoteIds } = get();
      if (!ids || ids.length === 0) return;
      const idsSet = new Set(ids);

      const restoredBatch: Note[] = [];
      const remainingTrash = trashNotes.filter((n) => {
        if (idsSet.has(n.id)) {
          restoredBatch.push({ ...n, isDeleted: false });
          return false;
        }
        return true;
      });

      localStorage.setItem(TRASH_KEY, JSON.stringify(remainingTrash));

      set({
        notes: [...restoredBatch, ...notes],
        trashNotes: remainingTrash,
        activeNoteId: restoredBatch.length > 0 ? restoredBatch[0].id : get().activeNoteId,
        selectedNoteIds: selectedNoteIds.filter((x) => !idsSet.has(x)),
        activeView: 'all',
      });

      // Save all restored notes back to backend in parallel
      await Promise.allSettled(
        restoredBatch.map((item) =>
          api.saveMemory({
            title: item.title,
            content: item.content,
            category: item.category,
            tags: item.tags,
            action: 'insert',
            memory_id: item.id,
          })
        )
      );
      get().fetchCategories();
    },

    togglePin: (id) => {
      const { pinnedIds, notes } = get();
      const isPinned = pinnedIds.includes(id);
      const updatedPinned = isPinned
        ? pinnedIds.filter((item) => item !== id)
        : [...pinnedIds, id];

      localStorage.setItem(PINNED_KEY, JSON.stringify(updatedPinned));

      set({
        pinnedIds: updatedPinned,
        notes: notes.map((n) => (n.id === id ? { ...n, isPinned: !isPinned } : n)),
      });
    },

    toggleFavorite: (id) => {
      const { favoriteIds, notes } = get();
      const isFav = favoriteIds.includes(id);
      const updatedFavs = isFav
        ? favoriteIds.filter((item) => item !== id)
        : [...favoriteIds, id];

      localStorage.setItem(FAVORITES_KEY, JSON.stringify(updatedFavs));

      set({
        favoriteIds: updatedFavs,
        notes: notes.map((n) => (n.id === id ? { ...n, isFavorite: !isFav } : n)),
      });
    },

    setActiveView: (view) => {
      const { notes, trashNotes, activeNoteId } = get();
      let nextActiveId = activeNoteId;
      if (view === 'trash') {
        if (!trashNotes.some((n) => n.id === activeNoteId)) {
          nextActiveId = trashNotes.length > 0 ? trashNotes[0].id : null;
        }
      } else {
        if (!notes.some((n) => n.id === activeNoteId)) {
          nextActiveId = notes.length > 0 ? notes[0].id : null;
        }
      }

      set({
        activeView: view,
        selectedCategory: null,
        selectedTag: null,
        activeNoteId: nextActiveId,
        selectedNoteIds: [],
      });
    },

    setSelectedCategory: (category) => {
      set({
        selectedCategory: category,
        activeView: 'all',
        selectedTag: null,
      });
    },

    setSelectedTag: (tag) => {
      set({
        selectedTag: tag,
        activeView: 'all',
        selectedCategory: null,
      });
    },

    setSearchQuery: (query) => {
      set({ searchQuery: query });
    },

    setSidebarCollapsed: (collapsed) => {
      set({ sidebarCollapsed: collapsed });
    },

    toggleSidebar: () => {
      set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed }));
    },

    setIsFullScreen: (full) => {
      set({ isFullScreen: full });
    },

    setIsFocusMode: (focus) => {
      set({ isFocusMode: focus });
    },

    toggleFullScreen: () => {
      if (typeof document !== 'undefined') {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen?.().catch((err) => {
            console.warn('Error requesting fullscreen:', err);
          });
          set({ isFullScreen: true });
        } else {
          document.exitFullscreen?.().catch((err) => {
            console.warn('Error exiting fullscreen:', err);
          });
          set({ isFullScreen: false });
        }
      }
    },

    toggleFocusMode: () => {
      set((state) => ({ isFocusMode: !state.isFocusMode }));
    },

    selectedNoteIds: [],
    toggleNoteSelection: (id) => {
      set((state) => {
        const exists = state.selectedNoteIds.includes(id);
        return {
          selectedNoteIds: exists
            ? state.selectedNoteIds.filter((x) => x !== id)
            : [...state.selectedNoteIds, id],
        };
      });
    },
    selectAllNotes: (ids) => {
      if (ids) {
        set({ selectedNoteIds: ids });
      } else {
        const { notes } = get();
        set({ selectedNoteIds: notes.map((n) => n.id) });
      }
    },
    clearNoteSelection: () => {
      set({ selectedNoteIds: [] });
    },
    openMergeModal: (initialIds) => {
      if (initialIds && initialIds.length > 0) {
        set({ selectedNoteIds: initialIds, activeModal: 'merge' });
      } else {
        set({ activeModal: 'merge' });
      }
    },

    setActiveModal: (modal) => {
      set({ activeModal: modal });
    },

    exportActiveNote: () => {
      const { activeNoteId, notes } = get();
      const current = notes.find((n) => n.id === activeNoteId);
      if (!current) return;

      const fullMd = `# ${current.title}\n\n${current.content}`;
      const blob = new Blob([fullMd], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${current.title.toLowerCase().replace(/[^a-z0-9_-]/gi, '_') || 'note'}.md`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },
  };
});
