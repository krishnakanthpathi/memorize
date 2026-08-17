import { create } from 'zustand';
import { api } from '@/services/api';
import { AppIconType, CategoryStat, CodeTheme, Note, SystemView, ThemeMode } from '@/types';

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
  isOnline: boolean;
  lastSavedAt: string | null;
  sidebarCollapsed: boolean;
  isFullScreen: boolean;
  isFocusMode: boolean;
  activeModal: 'search' | 'chat' | 'versions' | 'audit' | 'backup' | 'models' | 'settings' | 'new-category' | 'shortcuts' | 'merge' | null;

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
  notePendingDelete: { id: string; title: string; permanent: boolean } | null;
  requestDeleteNote: (id: string, permanent?: boolean) => void;
  cancelDeleteNote: () => void;
  confirmDeleteNote: () => Promise<void>;

  // Actions
  fetchNotes: () => Promise<void>;
  fetchCategories: () => Promise<void>;
  selectNote: (id: string | null) => void;
  createNewNote: (category?: string) => Note;
  updateActiveNote: (fields: Partial<Note>, syncRemote?: boolean) => void;
  saveCurrentNoteRemote: () => Promise<void>;
  organizeNote: (memoryId: string, instruction?: string, useAi?: boolean, generateTitle?: boolean) => Promise<any>;
  generateNoteTitle: (memoryId: string, customContent?: string, instruction?: string) => Promise<string | undefined>;
  transformSelectedText: (selectedText: string, instruction?: string, mode?: string, fullContext?: string) => Promise<string | undefined>;
  deleteNote: (id: string, permanent?: boolean) => Promise<void>;
  restoreNote: (id: string) => void;
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

// Debounce helper for auto-saving
let saveTimer: any = null;

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
    isOnline: true,
    lastSavedAt: null,
    sidebarCollapsed: false,
    isFullScreen: false,
    isFocusMode: false,
    activeModal: null,

    pinnedIds: initialPinned,
    favoriteIds: initialFavorites,

    fetchNotes: async () => {
      set({ isLoading: true });
      try {
        const rawNotes = await api.getMemories();
        const { pinnedIds, favoriteIds } = get();

        const notes = rawNotes.map((n) => ({
          ...n,
          isPinned: pinnedIds.includes(n.id),
          isFavorite: favoriteIds.includes(n.id),
        }));

        set((state) => {
          let activeNoteId = state.activeNoteId;
          if (!activeNoteId && notes.length > 0) {
            activeNoteId = notes[0].id;
          } else if (activeNoteId && !notes.some((n) => n.id === activeNoteId)) {
            activeNoteId = notes.length > 0 ? notes[0].id : null;
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

    createNewNote: (categoryParam) => {
      const { selectedCategory, notes, pinnedIds, favoriteIds } = get();
      const cat = categoryParam || selectedCategory || 'personal';
      const newId = `memo_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const now = new Date().toISOString();

      const newNote: Note = {
        id: newId,
        title: 'New Note',
        content: '',
        category: cat,
        folderId: cat,
        tags: [],
        keywords: [],
        isPinned: false,
        isFavorite: false,
        createdAt: now,
        updatedAt: now,
      };

      set({
        notes: [newNote, ...notes],
        activeNoteId: newId,
        searchQuery: '',
      });

      // Save asynchronously to backend
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
        get().fetchCategories();
      } catch (err) {
        console.error('Remote save failed:', err);
        set({ isSaving: false, isOnline: false });
      }
    },

    organizeNote: async (memoryId: string, instruction?: string, useAi: boolean = true, generateTitle: boolean = false) => {
      const { notes } = get();
      const target = notes.find((n) => n.id === memoryId);
      if (!target) return;

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

          await get().fetchCategories();
          return res;
        }
      } catch (err) {
        console.error('Failed to organize note with AI:', err);
      } finally {
        set({ isOrganizingNote: false });
      }
    },

    generateNoteTitle: async (memoryId: string, customContent?: string, instruction?: string) => {
      const { notes } = get();
      const target = notes.find((n) => n.id === memoryId);
      const contentToUse = customContent !== undefined ? customContent : target?.content || '';
      if (!contentToUse.trim()) return;

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
          if (target) {
            const updatedNote: Note = {
              ...target,
              title: cleanTitle,
              updatedAt: new Date().toISOString(),
            };
            set((state) => ({
              notes: state.notes.map((n) => (n.id === memoryId ? updatedNote : n)),
              isGeneratingTitle: false,
            }));
            await get().fetchCategories();
          }
          return cleanTitle;
        }
      } catch (err) {
        console.error('Failed to generate title with AI:', err);
      } finally {
        set({ isGeneratingTitle: false });
      }
    },

    transformSelectedText: async (selectedText: string, instruction?: string, mode: string = 'polish', fullContext?: string) => {
      if (!selectedText || !selectedText.trim()) return;
      set({ isTransformingSelection: true });
      try {
        const res = await api.transformSelection(selectedText, instruction, mode, fullContext);
        if (res.status === 'success') {
          return res.transformed_text;
        }
      } catch (err) {
        console.error('Failed to transform selected text:', err);
      } finally {
        set({ isTransformingSelection: false });
      }
    },

    notePendingDelete: null,
    requestDeleteNote: (id, permanent = false) => {
      const { notes, trashNotes } = get();
      const target = notes.find((n) => n.id === id) || trashNotes.find((n) => n.id === id);
      const title = target?.title || 'Untitled Note';
      set({ notePendingDelete: { id, title, permanent } });
    },
    cancelDeleteNote: () => {
      set({ notePendingDelete: null });
    },
    confirmDeleteNote: async () => {
      const { notePendingDelete, deleteNote } = get();
      if (!notePendingDelete) return;
      const { id, permanent } = notePendingDelete;
      set({ notePendingDelete: null });
      await deleteNote(id, permanent);
    },

    deleteNote: async (id, permanent = false) => {
      const { notes, trashNotes, activeNoteId } = get();
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
        set({ trashNotes: updatedTrash, activeNoteId: nextActiveId });
      }
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
