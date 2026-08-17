import React, { useMemo, useState } from 'react';
import {
  FileText,
  Star,
  Pin,
  Trash2,
  Folder as FolderIcon,
  Tag as TagIcon,
  Plus,
  Search,
  Sparkles,
  Bot,
  ShieldCheck,
  HardDriveDownload,
  Settings,
  Sun,
  Moon,
  Zap,
  ChevronDown,
  ChevronRight,
  FolderPlus,
  Cpu,
  Layers,
  CircleDot,
  BookOpen,
  Brain,
  Terminal,
  Database,
  Maximize2,
  Minimize2,
  Expand,
  Shrink,
} from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';
import { ThemeMode } from '@/types';
import { cn } from '@/lib/utils';

export const Sidebar: React.FC = () => {
  const {
    notes,
    trashNotes,
    categories,
    activeView,
    selectedCategory,
    selectedTag,
    theme,
    appIcon,
    isOnline,
    isSaving,
    lastSavedAt,
    setTheme,
    setActiveView,
    setSelectedCategory,
    setSelectedTag,
    createNewNote,
    setActiveModal,
    isFullScreen,
    isFocusMode,
    toggleFullScreen,
    toggleFocusMode,
  } = useNotesStore();

  const [categoriesOpen, setCategoriesOpen] = useState(false);
  const [tagsOpen, setTagsOpen] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(false);

  // Extract distinct tags and counts
  const tagCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    notes.forEach((note) => {
      if (Array.isArray(note.tags)) {
        note.tags.forEach((t) => {
          const clean = t.trim().replace(/^#/, '');
          if (clean) {
            counts[clean] = (counts[clean] || 0) + 1;
          }
        });
      }
    });
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [notes]);

  const pinnedCount = useMemo(() => notes.filter((n) => n.isPinned).length, [notes]);
  const favCount = useMemo(() => notes.filter((n) => n.isFavorite).length, [notes]);

  const renderBrandIcon = () => {
    switch (appIcon) {
      case 'brain':
        return <Brain className="w-4 h-4" />;
      case 'terminal':
        return <Terminal className="w-4 h-4" />;
      case 'book':
        return <BookOpen className="w-4 h-4" />;
      case 'zap':
        return <Zap className="w-4 h-4" />;
      case 'database':
        return <Database className="w-4 h-4" />;
      case 'sparkles':
        return <Sparkles className="w-4 h-4" />;
      case 'monogram':
      default:
        return 'M';
    }
  };

  return (
    <aside className="h-full w-full flex flex-col bg-surface-sidebar border-r border-border select-none text-foreground">
      {/* App Header */}
      <div className="h-14 px-4 flex items-center justify-between border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-foreground text-background flex items-center justify-center font-bold text-sm tracking-tighter shadow-2xs">
            {renderBrandIcon()}
          </div>
          <div>
            <span className="font-semibold text-sm tracking-tight">
              memorize
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveModal('new-category')}
            title="Create Category"
            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
          >
            <FolderPlus className="w-4 h-4" />
          </button>
          <button
            onClick={() => createNewNote()}
            title="Quick New Note"
            className="p-1.5 rounded-md text-foreground bg-surface-selected hover:bg-surface-hover transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Navigation Scroll Area */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-5">
        {/* Section 1: System Views */}
        <div>
          <div className="px-2 pb-1.5 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
            Quick Views
          </div>
          <div className="space-y-0.5">
            <button
              onClick={() => setActiveView('all')}
              className={cn(
                'w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors',
                activeView === 'all' && !selectedCategory && !selectedTag
                  ? 'bg-surface-selected text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
              )}
            >
              <div className="flex items-center gap-2.5">
                <FileText className="w-4 h-4" />
                <span>All Notes</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted font-mono">
                {notes.length}
              </span>
            </button>

            <button
              onClick={() => setActiveView('pinned')}
              className={cn(
                'w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors',
                activeView === 'pinned'
                  ? 'bg-surface-selected text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
              )}
            >
              <div className="flex items-center gap-2.5">
                <Pin className="w-4 h-4" />
                <span>Pinned</span>
              </div>
              {pinnedCount > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted font-mono">
                  {pinnedCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveView('favorites')}
              className={cn(
                'w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors',
                activeView === 'favorites'
                  ? 'bg-surface-selected text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
              )}
            >
              <div className="flex items-center gap-2.5">
                <Star className="w-4 h-4" />
                <span>Favorites</span>
              </div>
              {favCount > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted font-mono">
                  {favCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveView('trash')}
              className={cn(
                'w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors',
                activeView === 'trash'
                  ? 'bg-surface-selected text-foreground font-semibold shadow-xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
              )}
            >
              <div className="flex items-center gap-2.5">
                <Trash2 className="w-4 h-4 text-destructive/80" />
                <span>Trash</span>
              </div>
              {trashNotes.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-destructive/20 text-destructive font-mono">
                  {trashNotes.length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Section 2: Folders & Categories */}
        <div>
          <div className="flex items-center justify-between px-2 pb-1.5">
            <button
              onClick={() => setCategoriesOpen(!categoriesOpen)}
              className="flex items-center gap-1.5 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase hover:text-foreground transition-colors"
            >
              {categoriesOpen ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5" />
              )}
              <span>Categories</span>
            </button>
            <button
              onClick={() => setActiveModal('new-category')}
              className="text-muted-foreground hover:text-foreground p-0.5 rounded transition-colors"
              title="Add Category"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          {categoriesOpen && (
            <div className="space-y-0.5">
              {categories.length === 0 ? (
                <div className="px-3 py-2 text-xs text-muted-foreground italic">
                  No categories found
                </div>
              ) : (
                categories.map((cat) => {
                  const isSelected = selectedCategory === cat.category;
                  return (
                    <button
                      key={cat.category}
                      onClick={() => setSelectedCategory(cat.category)}
                      className={cn(
                        'w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors',
                        isSelected
                          ? 'bg-surface-selected text-foreground font-semibold shadow-xs'
                          : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
                      )}
                    >
                      <div className="flex items-center gap-2.5 truncate">
                        <FolderIcon className="w-4 h-4 shrink-0" />
                        <span className="truncate capitalize">{cat.category}</span>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted font-mono shrink-0">
                        {cat.count}
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* Section 3: Tags */}
        {tagCounts.length > 0 && (
          <div>
            <div className="flex items-center justify-between px-2 pb-1.5">
              <button
                onClick={() => setTagsOpen(!tagsOpen)}
                className="flex items-center gap-1.5 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase hover:text-foreground transition-colors"
              >
                {tagsOpen ? (
                  <ChevronDown className="w-3.5 h-3.5" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5" />
                )}
                <span>Tags</span>
              </button>
            </div>

            {tagsOpen && (
              <div className="flex flex-wrap gap-1 px-1.5">
                {tagCounts.map(([tag, count]) => {
                  const isSelected = selectedTag === tag;
                  return (
                    <button
                      key={tag}
                      onClick={() =>
                        setSelectedTag(isSelected ? null : tag)
                      }
                      className={cn(
                        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono transition-all',
                        isSelected
                          ? 'bg-foreground text-background font-semibold'
                          : 'bg-surface-hover text-muted-foreground hover:text-foreground hover:bg-surface-selected'
                      )}
                    >
                      <span>#{tag}</span>
                      <span className="text-[9px] opacity-70">({count})</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Section 4: System Tools & Backend Integrations */}
        <div>
          <div className="flex items-center justify-between px-2 pb-1.5">
            <button
              onClick={() => setToolsOpen(!toolsOpen)}
              className="flex items-center gap-1.5 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase hover:text-foreground transition-colors"
            >
              {toolsOpen ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5" />
              )}
              <span>AI & Storage</span>
            </button>
          </div>

          {toolsOpen && (
            <div className="space-y-0.5">
              <button
                onClick={() => setActiveModal('search')}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <Sparkles className="w-4 h-4 text-foreground/80" />
                  <span>Hybrid AI Search</span>
                </div>
                <kbd className="text-[9px] font-mono bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                  ⌘K
                </kbd>
              </button>

              <button
                onClick={() => setActiveModal('chat')}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <Bot className="w-4 h-4 text-foreground/80" />
                  <span>AI Companion Chat</span>
                </div>
                <kbd className="text-[9px] font-mono bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                  /chat
                </kbd>
              </button>

              <button
                onClick={() => setActiveModal('audit')}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-foreground/80" />
                  <span>Storage & Audit</span>
                </div>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              </button>

              <button
                onClick={() => setActiveModal('backup')}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <HardDriveDownload className="w-4 h-4 text-foreground/80" />
                  <span>Backup & Restore</span>
                </div>
              </button>

              <button
                onClick={() => setActiveModal('models')}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <Cpu className="w-4 h-4 text-foreground/80" />
                  <span>LLM Models Engine</span>
                </div>
              </button>

              <button
                onClick={toggleFullScreen}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2.5">
                  {isFullScreen ? (
                    <Minimize2 className="w-4 h-4 text-amber-500" />
                  ) : (
                    <Maximize2 className="w-4 h-4 text-foreground/80" />
                  )}
                  <span>{isFullScreen ? 'Exit Full Screen' : 'Full Screen Mode'}</span>
                </div>
                <kbd className="text-[9px] font-mono bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                  F11
                </kbd>
              </button>

              <button
                onClick={toggleFocusMode}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2.5">
                  {isFocusMode ? (
                    <Shrink className="w-4 h-4 text-primary" />
                  ) : (
                    <Expand className="w-4 h-4 text-foreground/80" />
                  )}
                  <span>{isFocusMode ? 'Exit Zen Mode' : 'Zen Focus Mode'}</span>
                </div>
                <kbd className="text-[9px] font-mono bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                  ⌘⇧Z
                </kbd>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Footer: 3-Way Theme Switcher & Status */}
      <div className="p-3 border-t border-border space-y-2.5 bg-surface-sidebar">
        {/* Status Indicator */}
        <div className="flex items-center justify-between text-[11px] px-1 text-muted-foreground font-mono">
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                'w-2 h-2 rounded-full inline-block',
                isOnline ? 'bg-emerald-500' : 'bg-rose-500 animate-pulse'
              )}
            />
            <span>{isOnline ? (isSaving ? 'Saving...' : 'Connected') : 'Offline'}</span>
          </div>
          {lastSavedAt && (
            <span className="text-[10px] text-muted-foreground opacity-70">
              Synced {lastSavedAt}
            </span>
          )}
        </div>

        {/* 3-Way Monochrome Theme Switcher */}
        <div className="p-1 rounded-lg bg-surface-hover border border-border/60 flex items-center justify-between">
          <button
            onClick={() => setTheme('light')}
            title="Light Mode (Crisp White)"
            className={cn(
              'flex-1 flex items-center justify-center gap-1 py-1 px-1.5 rounded-md text-xs transition-all',
              theme === 'light'
                ? 'bg-white text-zinc-900 font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Sun className="w-3.5 h-3.5" />
            <span className="text-[10px]">Light</span>
          </button>

          <button
            onClick={() => setTheme('dark')}
            title="Dark Mode (Slate Zinc - Default)"
            className={cn(
              'flex-1 flex items-center justify-center gap-1 py-1 px-1.5 rounded-md text-xs transition-all',
              theme === 'dark'
                ? 'bg-zinc-800 text-zinc-100 font-semibold shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Moon className="w-3.5 h-3.5" />
            <span className="text-[10px]">Dark</span>
          </button>

          <button
            onClick={() => setTheme('black')}
            title="Pitch Black OLED Mode (Pure Black)"
            className={cn(
              'flex-1 flex items-center justify-center gap-1 py-1 px-1.5 rounded-md text-xs transition-all',
              theme === 'black'
                ? 'bg-black text-white font-semibold ring-1 ring-zinc-700 shadow-xs'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Zap className="w-3.5 h-3.5" />
            <span className="text-[10px]">OLED</span>
          </button>
        </div>

        {/* Documentation link */}
        <button
          onClick={() => setActiveView('docs')}
          className={cn(
            "w-full flex items-center justify-between py-1.5 px-2.5 rounded-md text-xs font-medium transition-colors mb-1",
            activeView === 'docs'
              ? "bg-surface-selected text-foreground font-semibold"
              : "text-muted-foreground hover:text-foreground hover:bg-surface-hover"
          )}
        >
          <div className="flex items-center gap-2">
            <BookOpen className="w-3.5 h-3.5" />
            <span>Documentation</span>
          </div>
        </button>

        {/* Settings button */}
        <button
          onClick={() => setActiveView('settings')}
          className={cn(
            "w-full flex items-center justify-between py-1.5 px-2.5 rounded-md text-xs font-medium transition-colors",
            activeView === 'settings'
              ? "bg-surface-selected text-foreground font-semibold"
              : "text-muted-foreground hover:text-foreground hover:bg-surface-hover"
          )}
        >
          <div className="flex items-center gap-2">
            <Settings className="w-3.5 h-3.5" />
            <span>Settings</span>
          </div>
          <kbd className="px-1.5 py-0.5 text-[9px] font-mono text-muted-foreground bg-surface-hover border border-border/70 rounded">⌘,</kbd>
        </button>
      </div>
    </aside>
  );
};
