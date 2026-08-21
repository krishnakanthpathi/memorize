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
  BookOpen,
  Brain,
  Terminal,
  Database,
  Expand,
  Shrink,
} from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';
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
    isFocusMode,
    toggleFocusMode,
  } = useNotesStore();

  // Categories and Tags pre-closed by default
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
      <div className="h-14 px-3.5 flex items-center justify-between border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-foreground text-background flex items-center justify-center font-bold text-sm tracking-tighter shadow-2xs">
            {renderBrandIcon()}
          </div>
          <div>
            <span className="font-bold text-sm tracking-tight">
              memorize
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveModal('new-category')}
            title="Create Category"
            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
          >
            <FolderPlus className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              setActiveView('all');
              createNewNote();
            }}
            title="Quick New Note (⌘N)"
            className="p-1.5 rounded-md text-foreground bg-surface-selected hover:bg-surface-hover transition-colors cursor-pointer shadow-2xs"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Navigation Scroll Area */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        
        {/* Quick Action Strip (Search + Zen Mode) */}
        <div className="space-y-1.5">
          <button
            onClick={() => setActiveModal('search')}
            className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-surface-hover/60 hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-all cursor-pointer text-xs font-medium border border-border/50"
          >
            <div className="flex items-center gap-2">
              <Search className="w-3.5 h-3.5 text-foreground" />
              <span>Search Knowledge</span>
            </div>
            <kbd className="text-[10px] font-mono bg-surface-list px-1.5 py-0.5 rounded border border-border/70 text-muted-foreground">
              ⌘K
            </kbd>
          </button>

          <button
            onClick={toggleFocusMode}
            title="Zen Focus Mode (⌘⇧Z)"
            className={cn(
              'w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer border',
              isFocusMode
                ? 'bg-foreground text-background border-foreground font-semibold shadow-2xs'
                : 'bg-surface-hover/40 hover:bg-surface-hover text-muted-foreground hover:text-foreground border-border/50'
            )}
          >
            <div className="flex items-center gap-2">
              {isFocusMode ? (
                <Shrink className="w-3.5 h-3.5 text-background" />
              ) : (
                <Expand className="w-3.5 h-3.5 text-foreground" />
              )}
              <span>{isFocusMode ? 'Exit Zen Mode' : 'Zen Focus Mode'}</span>
            </div>
            <kbd
              className={cn(
                'text-[10px] font-mono px-1.5 py-0.5 rounded border',
                isFocusMode
                  ? 'bg-background/20 border-background/30 text-background'
                  : 'bg-surface-list border-border/70 text-muted-foreground'
              )}
            >
              ⌘⇧Z
            </kbd>
          </button>
        </div>

        {/* Section 1: Views & Collections */}
        <div className="pt-1">
          <div className="px-2 pb-1.5 text-[10px] font-bold tracking-wider text-muted-foreground uppercase font-mono">
            Views
          </div>
          <div className="space-y-0.5">
            <button
              onClick={() => {
                setSelectedCategory(null);
                setSelectedTag(null);
                setActiveView('all');
              }}
              className={cn(
                'w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer',
                activeView === 'all' && !selectedCategory && !selectedTag
                  ? 'bg-surface-selected text-foreground font-semibold shadow-2xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
              )}
            >
              <div className="flex items-center gap-2.5">
                <FileText className="w-4 h-4" />
                <span>All Notes</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-hover font-mono">
                {notes.length}
              </span>
            </button>

            <button
              onClick={() => {
                setSelectedCategory(null);
                setSelectedTag(null);
                setActiveView('pinned');
              }}
              className={cn(
                'w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer',
                activeView === 'pinned'
                  ? 'bg-surface-selected text-foreground font-semibold shadow-2xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
              )}
            >
              <div className="flex items-center gap-2.5">
                <Pin className="w-4 h-4" />
                <span>Pinned</span>
              </div>
              {pinnedCount > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-hover font-mono">
                  {pinnedCount}
                </span>
              )}
            </button>

            <button
              onClick={() => {
                setSelectedCategory(null);
                setSelectedTag(null);
                setActiveView('favorites');
              }}
              className={cn(
                'w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer',
                activeView === 'favorites'
                  ? 'bg-surface-selected text-foreground font-semibold shadow-2xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
              )}
            >
              <div className="flex items-center gap-2.5">
                <Star className="w-4 h-4" />
                <span>Favorites</span>
              </div>
              {favCount > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-hover font-mono">
                  {favCount}
                </span>
              )}
            </button>

            <button
              onClick={() => {
                setSelectedCategory(null);
                setSelectedTag(null);
                setActiveView('trash');
              }}
              className={cn(
                'w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer',
                activeView === 'trash'
                  ? 'bg-surface-selected text-foreground font-semibold shadow-2xs'
                  : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
              )}
            >
              <div className="flex items-center gap-2.5">
                <Trash2 className="w-4 h-4 text-muted-foreground" />
                <span>Trash</span>
              </div>
              {trashNotes.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-hover text-muted-foreground font-mono">
                  {trashNotes.length}
                </span>
              )}
            </button>

          </div>
        </div>

        {/* Section 2: Folders & Categories (Pre-closed / Collapsed by default) */}
        <div className="pt-1">
          <div className="flex items-center justify-between px-2 pb-1.5">
            <button
              onClick={() => setCategoriesOpen(!categoriesOpen)}
              className="flex items-center gap-1.5 text-[10px] font-bold tracking-wider text-muted-foreground uppercase font-mono hover:text-foreground transition-colors cursor-pointer"
            >
              {categoriesOpen ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronRight className="w-3 h-3" />
              )}
              <span>Categories ({categories.length})</span>
            </button>
            <button
              onClick={() => setActiveModal('new-category')}
              className="text-muted-foreground hover:text-foreground p-0.5 rounded transition-colors cursor-pointer"
              title="Add Category"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          {categoriesOpen && (
            <div className="space-y-0.5">
              {categories.length === 0 ? (
                <div className="px-3 py-1.5 text-xs text-muted-foreground italic">
                  No categories found
                </div>
              ) : (
                categories.map((cat) => {
                  const isSelected = selectedCategory === cat.category;
                  return (
                    <button
                      key={cat.category}
                      onClick={() => {
                        setSelectedTag(null);
                        setSelectedCategory(cat.category);
                        if (activeView === 'settings' || activeView === 'docs') {
                          setActiveView('all');
                        }
                      }}
                      className={cn(
                        'w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer',
                        isSelected
                          ? 'bg-surface-selected text-foreground font-semibold shadow-2xs'
                          : 'text-muted-foreground hover:text-foreground hover:bg-surface-hover'
                      )}
                    >
                      <div className="flex items-center gap-2.5 truncate">
                        <FolderIcon className="w-4 h-4 shrink-0" />
                        <span className="truncate capitalize">{cat.category}</span>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-hover font-mono shrink-0">
                        {cat.count}
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* Section 3: Tags (Pre-closed / Collapsed by default) */}
        {tagCounts.length > 0 && (
          <div className="pt-1">
            <div className="flex items-center justify-between px-2 pb-1.5">
              <button
                onClick={() => setTagsOpen(!tagsOpen)}
                className="flex items-center gap-1.5 text-[10px] font-bold tracking-wider text-muted-foreground uppercase font-mono hover:text-foreground transition-colors cursor-pointer"
              >
                {tagsOpen ? (
                  <ChevronDown className="w-3 h-3" />
                ) : (
                  <ChevronRight className="w-3 h-3" />
                )}
                <span>Tags ({tagCounts.length})</span>
              </button>
            </div>

            {tagsOpen && (
              <div className="flex flex-wrap gap-1 px-1.5 pt-0.5">
                {tagCounts.map(([tag, count]) => {
                  const isSelected = selectedTag === tag;
                  return (
                    <button
                      key={tag}
                      onClick={() => {
                        setSelectedTag(isSelected ? null : tag);
                        if (activeView === 'settings' || activeView === 'docs') {
                          setActiveView('all');
                        }
                      }}
                      className={cn(
                        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono transition-all cursor-pointer',
                        isSelected
                          ? 'bg-foreground text-background font-semibold shadow-2xs'
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

        {/* Section 4: System Tools & Diagnostics Drawer */}
        <div className="pt-1">
          <div className="flex items-center justify-between px-2 pb-1.5">
            <button
              onClick={() => setToolsOpen(!toolsOpen)}
              className="flex items-center gap-1.5 text-[10px] font-bold tracking-wider text-muted-foreground uppercase font-mono hover:text-foreground transition-colors cursor-pointer"
            >
              {toolsOpen ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronRight className="w-3 h-3" />
              )}
              <span>Diagnostics & Tools</span>
            </button>
          </div>

          {toolsOpen && (
            <div className="space-y-0.5">
              <button
                onClick={() => setActiveModal('audit')}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-foreground/80" />
                  <span>Storage & Audit</span>
                </div>
                <span className="w-1.5 h-1.5 rounded-full bg-foreground/50" />
              </button>

              <button
                onClick={() => setActiveModal('backup')}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2.5">
                  <HardDriveDownload className="w-4 h-4 text-foreground/80" />
                  <span>Backup & Snapshots</span>
                </div>
              </button>

              <button
                onClick={() => setActiveView('settings')}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2.5">
                  <Cpu className="w-4 h-4 text-foreground/80" />
                  <span>LLM & Prompts</span>
                </div>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Footer: Monochrome Status, 3-Way Switcher, Settings */}
      <div className="p-3 border-t border-border space-y-2.5 bg-surface-sidebar">
        {/* Status Indicator */}
        <div className="flex items-center justify-between text-[10px] px-1 text-muted-foreground font-mono">
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                'w-2 h-2 rounded-full inline-block',
                isOnline ? 'bg-foreground/80 shadow-2xs' : 'bg-muted-foreground animate-pulse'
              )}
            />
            <span className="font-semibold text-foreground/90">
              {isOnline ? (isSaving ? 'Saving...' : 'Connected') : 'Offline'}
            </span>
          </div>
          {lastSavedAt && (
            <span className="text-[9px] opacity-70">
              Synced {lastSavedAt}
            </span>
          )}
        </div>

        {/* 3-Way Monochrome Theme Switcher */}
        <div className="p-0.5 rounded-lg bg-surface-hover border border-border/70 flex items-center justify-between">
          <button
            onClick={() => setTheme('light')}
            title="Light Mode"
            className={cn(
              'flex-1 flex items-center justify-center gap-1 py-1 px-1 rounded-md text-xs transition-all cursor-pointer',
              theme === 'light'
                ? 'bg-card text-foreground font-semibold shadow-2xs'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Sun className="w-3 h-3 text-foreground" />
            <span className="text-[10px]">Light</span>
          </button>

          <button
            onClick={() => setTheme('dark')}
            title="Dark Mode"
            className={cn(
              'flex-1 flex items-center justify-center gap-1 py-1 px-1 rounded-md text-xs transition-all cursor-pointer',
              theme === 'dark'
                ? 'bg-card text-foreground font-semibold shadow-2xs'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Moon className="w-3 h-3 text-foreground" />
            <span className="text-[10px]">Dark</span>
          </button>

          <button
            onClick={() => setTheme('black')}
            title="Pitch Black OLED Mode"
            className={cn(
              'flex-1 flex items-center justify-center gap-1 py-1 px-1 rounded-md text-xs transition-all cursor-pointer',
              theme === 'black'
                ? 'bg-card text-foreground font-semibold ring-1 ring-border shadow-2xs'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Zap className="w-3 h-3 text-foreground" />
            <span className="text-[10px]">OLED</span>
          </button>
        </div>

        {/* Settings Button */}
        <button
          onClick={() => setActiveView('settings')}
          className={cn(
            'w-full flex items-center justify-between py-1.5 px-2.5 rounded-lg text-xs font-medium transition-colors cursor-pointer border',
            activeView === 'settings'
              ? 'bg-surface-selected text-foreground font-semibold border-border'
              : 'bg-surface-hover/50 text-muted-foreground hover:text-foreground hover:bg-surface-hover border-border/40'
          )}
        >
          <div className="flex items-center gap-2">
            <Settings className="w-3.5 h-3.5" />
            <span>Preferences & Settings</span>
          </div>
          <kbd className="text-[9px] font-mono opacity-70">⌘,</kbd>
        </button>
      </div>
    </aside>
  );
};

