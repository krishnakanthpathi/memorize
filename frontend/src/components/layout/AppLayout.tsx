import React, { useEffect } from 'react';
import { Group, Panel, Separator } from 'react-resizable-panels';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { NotesList } from '@/components/notes-list/NotesList';
import { EditorCanvas } from '@/components/editor/EditorCanvas';
import { SettingsPanel } from '@/components/settings/SettingsPanel';
import { DocsPanel } from '@/components/docs/DocsPanel';
import { SearchModal } from '@/components/modals/SearchModal';
import { VersionHistoryModal } from '@/components/modals/VersionHistoryModal';
import { AuditModal } from '@/components/modals/AuditModal';
import { BackupModal } from '@/components/modals/BackupModal';
import { NewCategoryModal } from '@/components/modals/NewCategoryModal';
import { DeleteConfirmationModal } from '@/components/modals/DeleteConfirmationModal';
import { KeyboardShortcutsModal } from '@/components/modals/KeyboardShortcutsModal';
import { MergeMemoriesModal } from '@/components/modals/MergeMemoriesModal';
import { ManageTagsModal } from '@/components/modals/ManageTagsModal';
import { RenameNoteModal } from '@/components/modals/RenameNoteModal';
import { CreateNoteModal } from '@/components/modals/CreateNoteModal';
import { ToastNotificationContainer } from '@/components/common/ToastNotificationContainer';

import { useNotesStore } from '@/store/useNotesStore';




export const AppLayout: React.FC = () => {
  const {
    sidebarCollapsed,
    activeView,
    activeModal,
    activeNoteId,
    isFullScreen,
    isFocusMode,
    fetchNotes,
    fetchCategories,
    setActiveView,
    setActiveModal,
    createNewNote,
    saveCurrentNoteRemote,
    requestDeleteNote,
    togglePin,
    toggleFavorite,
    setIsFullScreen,
    setIsFocusMode,
    toggleFullScreen,
    toggleFocusMode,
  } = useNotesStore();

  // Sync native full-screen changes with store state
  useEffect(() => {
    const handleFullScreenChange = () => {
      setIsFullScreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullScreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullScreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullScreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullScreenChange);
    };
  }, [setIsFullScreen]);

  // Initial fetch and global hotkeys
  useEffect(() => {
    fetchNotes();
    fetchCategories();

    const handleKeyDown = (e: KeyboardEvent) => {
      const isInput = ['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName || '');

      // F11 or ⌘⇧F / Ctrl+Shift+F for Full Screen Toggle
      if (
        e.key === 'F11' ||
        ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'f' || e.key === 'F'))
      ) {
        e.preventDefault();
        toggleFullScreen();
        return;
      }

      // ⌘⇧Z or Ctrl+Shift+Z for Zen Focus / Distraction-Free Mode
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'z' || e.key === 'Z')) {
        e.preventDefault();
        toggleFocusMode();
        return;
      }

      // ⌘K or Ctrl+K for Hybrid Search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setActiveModal('search');
        return;
      }

      // New Note shortcuts on Mac & Windows:
      // - ⌘N (Command+N) on Mac
      // - ⌃N (Control+N) on Mac / Windows / Linux
      // - ⌥N (Option+N / Alt+N) on Mac
      // - ⌘⇧N (Command+Shift+N)
      const isKeyN = e.key === 'n' || e.key === 'N' || e.code === 'KeyN' || e.key === '˜' || e.key === 'ñ';
      const isNewNoteTrigger = (e.metaKey || e.ctrlKey || e.altKey) && isKeyN;

      if (isNewNoteTrigger) {
        e.preventDefault();
        e.stopPropagation();
        setActiveView('all');
        setActiveModal('new-note');
        return;
      }

      // ⌘S or Ctrl+S for Save
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        saveCurrentNoteRemote();
        return;
      }

      // ⌘, or Ctrl+, for Settings View
      if ((e.metaKey || e.ctrlKey) && e.key === ',') {
        e.preventDefault();
        setActiveView(activeView === 'settings' ? 'all' : 'settings');
        return;
      }

      // ⌘/ or Ctrl+/ for Keyboard Shortcuts Sheet
      if ((e.metaKey || e.ctrlKey) && e.key === '/') {
        e.preventDefault();
        setActiveModal(activeModal === 'shortcuts' ? null : 'shortcuts');
        return;
      }

      // ⌘⇧D or Alt+D for Documentation View
      if (
        ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'd' || e.key === 'D')) ||
        (e.altKey && (e.key === 'd' || e.key === 'D'))
      ) {
        e.preventDefault();
        setActiveView(activeView === 'docs' ? 'all' : 'docs');
        return;
      }

      // ⌘⇧P or Alt+P for Pin/Unpin Active Note
      if (
        ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'p' || e.key === 'P')) ||
        (e.altKey && (e.key === 'p' || e.key === 'P'))
      ) {
        e.preventDefault();
        if (activeNoteId) togglePin(activeNoteId);
        return;
      }

      // ⌘⇧S or Alt+S for Favorite/Star Active Note (when not standard Ctrl+S save)
      if (
        ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 's' || e.key === 'S')) ||
        (e.altKey && (e.key === 's' || e.key === 'S'))
      ) {
        e.preventDefault();
        if (activeNoteId) toggleFavorite(activeNoteId);
        return;
      }

      // ⌘⌫ or Ctrl+Backspace or Delete key (when not focused in text input/textarea) -> Delete Note
      if (
        ((e.metaKey || e.ctrlKey) && (e.key === 'Backspace' || e.key === 'Delete')) ||
        (!isInput && e.key === 'Delete')
      ) {
        if (activeNoteId && activeView !== 'trash') {
          e.preventDefault();
          requestDeleteNote(activeNoteId, false);
          return;
        }
      }

      // Escape key -> Close modals, exit Focus Mode, or exit Settings / Docs to Notes view
      if (e.key === 'Escape') {
        if (activeModal) {
          e.preventDefault();
          setActiveModal(null);
        } else if (isFocusMode) {
          e.preventDefault();
          setIsFocusMode(false);
        } else if (activeView === 'settings' || activeView === 'docs') {
          e.preventDefault();
          setActiveView('all');
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [
    activeView,
    activeModal,
    activeNoteId,
    isFocusMode,
    setActiveView,
    setActiveModal,
    createNewNote,
    saveCurrentNoteRemote,
    requestDeleteNote,
    togglePin,
    toggleFavorite,
    toggleFullScreen,
    toggleFocusMode,
    setIsFocusMode,
  ]);

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-background text-foreground select-none relative">
      {/* Zen Focus Mode View vs 3-Column Resizable Panel Layout */}
      {isFocusMode ? (
        <div className="flex-1 w-full h-full animate-in fade-in zoom-in-99 duration-200">
          <EditorCanvas />
        </div>
      ) : (
        <Group orientation="horizontal" className="flex-1 w-full h-full">
          {/* Column 1: Sidebar */}
          {!sidebarCollapsed && (
            <>
              <Panel
                id="sidebar-panel"
                defaultSize="18%"
                minSize="12%"
                maxSize="30%"
                className="h-full"
              >
                <Sidebar />
              </Panel>
              <Separator className="w-[1px] bg-border hover:bg-foreground/50 transition-colors" />
            </>
          )}

          {/* Column 2: Note Master List */}
          <Panel
            id="notes-list-panel"
            defaultSize="24%"
            minSize="18%"
            maxSize="40%"
            className="h-full"
          >
            <NotesList />
          </Panel>

          <Separator className="w-[1px] bg-border hover:bg-foreground/50 transition-colors" />

          {/* Column 3: Editor Canvas */}
          <Panel
            id="editor-canvas-panel"
            defaultSize={sidebarCollapsed ? '76%' : '58%'}
            minSize="35%"
            className="h-full"
          >
            <EditorCanvas />
          </Panel>
        </Group>
      )}

      {/* Full-Screen Dedicated Overlays (Cover entire window with zero overlaps) */}
      {activeView === 'settings' && <SettingsPanel />}
      {activeView === 'docs' && <DocsPanel />}

      {/* Global Modals */}
      <SearchModal />
      <VersionHistoryModal />
      <AuditModal />
      <BackupModal />
      <NewCategoryModal />
      <DeleteConfirmationModal />
      <KeyboardShortcutsModal />
      <MergeMemoriesModal />
      <ManageTagsModal />
      <RenameNoteModal />
      <CreateNoteModal />

      {/* Global Toast Notification Banner Stack */}
      <ToastNotificationContainer />
    </div>
  );
};

