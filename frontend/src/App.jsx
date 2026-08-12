import React, { useState, useMemo, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import NotesList from './components/NotesList';
import NoteEditor from './components/NoteEditor';
import AdminDashboard from './components/AdminDashboard';
import GraphChatDrawer from './components/GraphChatDrawer';
import VersionHistoryModal from './components/VersionHistoryModal';
import { Plus } from 'lucide-react';

import {
  initialNotes,
  initialCategories,
  initialModels,
  mockAuditData,
  mockMetrics,
  simulateAutoOrganizeNote,
  simulateSmartMergeNote,
} from './mockData';

export default function App() {
  const [activeView, setActiveView] = useState('notes'); // 'notes' | 'admin'
  const [notes, setNotes] = useState(initialNotes);
  const [activeNoteId, setActiveNoteId] = useState(initialNotes[0]?.id || null);
  
  // Multi-Filter Selection State
  const [selectedCategories, setSelectedCategories] = useState([]); // Array of category IDs
  const [selectedTags, setSelectedTags] = useState([]); // Array of tag strings
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoadingNotes, setIsLoadingNotes] = useState(false);
  
  // Closeable / Collapsible Sidebars State with LocalStorage Persistence
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => {
    const saved = localStorage.getItem('memorize_is_sidebar_open');
    return saved !== null ? JSON.parse(saved) : true;
  });
  const [isNotesListOpen, setIsNotesListOpen] = useState(() => {
    const saved = localStorage.getItem('memorize_is_noteslist_open');
    return saved !== null ? JSON.parse(saved) : true;
  });

  // Resizable Sidebars Width State with LocalStorage Persistence
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const saved = localStorage.getItem('memorize_sidebar_width');
    return saved ? parseInt(saved, 10) : 240;
  });
  const [notesListWidth, setNotesListWidth] = useState(() => {
    const saved = localStorage.getItem('memorize_noteslist_width');
    return saved ? parseInt(saved, 10) : 320;
  });

  const [isResizingSidebar, setIsResizingSidebar] = useState(false);
  const [isResizingNotesList, setIsResizingNotesList] = useState(false);

  // Sync state changes to localStorage
  useEffect(() => {
    localStorage.setItem('memorize_sidebar_width', sidebarWidth.toString());
  }, [sidebarWidth]);

  useEffect(() => {
    localStorage.setItem('memorize_noteslist_width', notesListWidth.toString());
  }, [notesListWidth]);

  useEffect(() => {
    localStorage.setItem('memorize_is_sidebar_open', JSON.stringify(isSidebarOpen));
  }, [isSidebarOpen]);

  useEffect(() => {
    localStorage.setItem('memorize_is_noteslist_open', JSON.stringify(isNotesListOpen));
  }, [isNotesListOpen]);

  // Mouse Move Event Handlers for Drag Resizing
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isResizingSidebar) {
        // Clamp sidebar width between 160px and 450px
        const newWidth = Math.min(Math.max(e.clientX, 160), 450);
        setSidebarWidth(newWidth);
      } else if (isResizingNotesList) {
        // Calculate offset based on sidebar state
        const currentSidebarOffset = isSidebarOpen ? sidebarWidth : 0;
        const newNotesListWidth = Math.min(Math.max(e.clientX - currentSidebarOffset, 200), 550);
        setNotesListWidth(newNotesListWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizingSidebar(false);
      setIsResizingNotesList(false);
    };

    if (isResizingSidebar || isResizingNotesList) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingSidebar, isResizingNotesList, isSidebarOpen, sidebarWidth]);

  // Settings / LLM State
  const [activeModel, setActiveModel] = useState('gpt-4o-mini');
  const [activeEngine, setActiveEngine] = useState('langgraph');
  const [isBrainFilled, setIsBrainFilled] = useState(false); // Hollow vs Filled icon toggle

  // Drawers & Modals
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isVersionsOpen, setIsVersionsOpen] = useState(false);
  const [showNewNoteConfirm, setShowNewNoteConfirm] = useState(false);
  const [isOrganizing, setIsOrganizing] = useState(false);

  // Category counts
  const categories = useMemo(() => {
    return initialCategories.map((c) => {
      if (c.id === 'all') return { ...c, count: notes.length };
      return {
        ...c,
        count: notes.filter((n) => n.category === c.id).length,
      };
    });
  }, [notes]);

  const allTags = useMemo(() => {
    const set = new Set();
    notes.forEach((n) => n.tags?.forEach((t) => set.add(t)));
    return Array.from(set);
  }, [notes]);

  // Filter setters with loading spinner triggers
  const handleSetSelectedCategories = (cats) => {
    setIsLoadingNotes(true);
    setSelectedCategories(cats);
    setTimeout(() => setIsLoadingNotes(false), 500);
  };

  const handleSetSelectedTags = (tgs) => {
    setIsLoadingNotes(true);
    setSelectedTags(tgs);
    setTimeout(() => setIsLoadingNotes(false), 500);
  };

  const handleSetSearchQuery = (q) => {
    setIsLoadingNotes(true);
    setSearchQuery(q);
    setTimeout(() => setIsLoadingNotes(false), 500);
  };

  // Multi-Filter Filtering Logic
  const filteredNotes = useMemo(() => {
    return notes.filter((note) => {
      if (selectedCategories.length > 0 && !selectedCategories.includes(note.category)) {
        return false;
      }
      if (selectedTags.length > 0 && !note.tags?.some((t) => selectedTags.includes(t))) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchTitle = note.title.toLowerCase().includes(q);
        const matchContent = note.content.toLowerCase().includes(q);
        const matchTags = note.tags?.some((t) => t.toLowerCase().includes(q));
        if (!matchTitle && !matchContent && !matchTags) return false;
      }
      return true;
    });
  }, [notes, selectedCategories, selectedTags, searchQuery]);

  const activeNote = useMemo(() => {
    return notes.find((n) => n.id === activeNoteId) || null;
  }, [notes, activeNoteId]);

  // Handlers
  const handleConfirmNewNote = () => {
    const newNote = {
      id: `mem_${Date.now().toString(36)}`,
      title: 'Untitled Note',
      category: selectedCategories.length > 0 ? selectedCategories[0] : 'personal',
      tags: selectedTags.length > 0 ? [...selectedTags] : ['draft'],
      summary: 'New memory draft created.',
      content: '# New Note\n\nType your thoughts here and click Auto-Organize or Smart Merge...',
      updated_at: new Date().toISOString(),
      versions: [
        {
          version_number: 1,
          created_at: new Date().toISOString(),
          summary: 'Draft created.',
        },
      ],
    };
    setNotes([newNote, ...notes]);
    setActiveNoteId(newNote.id);
    setActiveView('notes');
  };

  const handleSaveNote = (updatedData) => {
    setNotes((prevNotes) => {
      const exists = prevNotes.some((n) => n.id === updatedData.id);
      if (exists) {
        return prevNotes.map((n) => {
          if (n.id === updatedData.id) {
            const newVersionNum = (n.versions?.length || 0) + 1;
            const newVersions = [
              {
                version_number: newVersionNum,
                created_at: new Date().toISOString(),
                summary: updatedData.summary || `Updated version ${newVersionNum}`,
              },
              ...(n.versions || []),
            ];
            return {
              ...n,
              ...updatedData,
              updated_at: new Date().toISOString(),
              versions: newVersions,
            };
          }
          return n;
        });
      } else {
        const newNote = {
          ...updatedData,
          id: updatedData.id || `mem_${Date.now().toString(36)}`,
          updated_at: new Date().toISOString(),
          versions: [
            {
              version_number: 1,
              created_at: new Date().toISOString(),
              summary: 'Initial version.',
            },
          ],
        };
        return [newNote, ...prevNotes];
      }
    });
  };

  const handleDeleteNote = (noteId) => {
    const remaining = notes.filter((n) => n.id !== noteId);
    setNotes(remaining);
    if (activeNoteId === noteId) {
      setActiveNoteId(remaining[0]?.id || null);
    }
  };

  const handleAutoOrganize = (content, currentTitle) => {
    setIsOrganizing(true);
    setTimeout(() => {
      const res = simulateAutoOrganizeNote(content, currentTitle, activeModel);
      if (res.status === 'success') {
        handleSaveNote({
          id: activeNoteId,
          title: res.title,
          category: res.category,
          tags: res.tags,
          summary: res.summary,
          content: res.organized_content,
        });
      }
      setIsOrganizing(false);
    }, 1600);
  };

  const handleSmartMerge = (content, currentTitle) => {
    setIsOrganizing(true);
    setTimeout(() => {
      const res = simulateSmartMergeNote(content, activeNote, activeModel);
      if (res.status === 'success') {
        handleSaveNote({
          id: activeNoteId,
          title: res.title,
          category: res.category,
          tags: res.tags,
          summary: res.summary,
          content: res.organized_content,
        });
      }
      setIsOrganizing(false);
    }, 1600);
  };

  const handleRevertVersion = (versionNumber) => {
    if (!activeNote) return;
    const ver = activeNote.versions?.find((v) => v.version_number === versionNumber);
    if (ver) {
      handleSaveNote({
        id: activeNote.id,
        title: activeNote.title,
        category: activeNote.category,
        tags: activeNote.tags,
        summary: `Reverted to version ${versionNumber}: ${ver.summary}`,
        content: activeNote.content,
      });
    }
    setIsVersionsOpen(false);
  };

  return (
    <div className="d-flex flex-column vh-100 bg-mono-dark text-light overflow-hidden">
      
      {/* Top Header */}
      <Header
        activeView={activeView}
        setActiveView={setActiveView}
        onNewNote={() => setShowNewNoteConfirm(true)}
        onToggleChat={() => setIsChatOpen(!isChatOpen)}
        isBrainFilled={isBrainFilled}
        setIsBrainFilled={setIsBrainFilled}
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        isNotesListOpen={isNotesListOpen}
        setIsNotesListOpen={setIsNotesListOpen}
      />

      {/* Main Body Workspace */}
      <main className="flex-grow-1 overflow-hidden">
        {activeView === 'notes' ? (
          <div className="d-flex h-100 w-100 overflow-hidden position-relative">
            
            {/* Resizable Left Sidebar */}
            {isSidebarOpen && (
              <div style={{ width: `${sidebarWidth}px`, minWidth: `${sidebarWidth}px` }} className="h-100 flex-shrink-0">
                <Sidebar
                  categories={categories}
                  selectedCategories={selectedCategories}
                  setSelectedCategories={handleSetSelectedCategories}
                  allTags={allTags}
                  selectedTags={selectedTags}
                  setSelectedTags={handleSetSelectedTags}
                  searchQuery={searchQuery}
                  setSearchQuery={handleSetSearchQuery}
                  totalNotesCount={notes.length}
                />
              </div>
            )}

            {/* Drag Resizer 1: Between Sidebar and Notes Stream */}
            {isSidebarOpen && (
              <div
                className={`resizer-handle ${isResizingSidebar ? 'resizing' : ''}`}
                onMouseDown={() => setIsResizingSidebar(true)}
                title="Drag to resize Category & Tag Sidebar"
              />
            )}

            {/* Resizable Middle Notes Stream List */}
            {isNotesListOpen && (
              <div style={{ width: `${notesListWidth}px`, minWidth: `${notesListWidth}px` }} className="h-100 flex-shrink-0">
                <NotesList
                  notes={filteredNotes}
                  activeNoteId={activeNoteId}
                  onSelectNote={setActiveNoteId}
                  hasActiveFilters={selectedCategories.length > 0 || selectedTags.length > 0 || searchQuery !== ''}
                  isLoadingNotes={isLoadingNotes}
                />
              </div>
            )}

            {/* Drag Resizer 2: Between Notes Stream and Note Editor */}
            {isNotesListOpen && (
              <div
                className={`resizer-handle ${isResizingNotesList ? 'resizing' : ''}`}
                onMouseDown={() => setIsResizingNotesList(true)}
                title="Drag to resize Notes Stream Pane"
              />
            )}

            {/* Flexible Note Editor Pane */}
            <div className="flex-grow-1 h-100 overflow-hidden">
              <NoteEditor
                note={activeNote}
                onSave={handleSaveNote}
                onDelete={handleDeleteNote}
                onAutoOrganize={handleAutoOrganize}
                onSmartMerge={handleSmartMerge}
                onOpenVersions={() => setIsVersionsOpen(true)}
                availableCategories={categories}
                activeModel={activeModel}
                isOrganizing={isOrganizing}
              />
            </div>

          </div>
        ) : (
          /* Admin Dashboard View */
          <AdminDashboard
            modelsData={initialModels}
            activeModel={activeModel}
            setActiveModel={setActiveModel}
            activeEngine={activeEngine}
            setActiveEngine={setActiveEngine}
            auditData={mockAuditData}
            metrics={mockMetrics}
            onTriggerBackup={() => {}}
          />
        )}
      </main>

      {/* GraphRAG Companion Slide-over Drawer */}
      <GraphChatDrawer
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        activeModel={activeModel}
      />

      {/* Version Control Timeline Modal */}
      <VersionHistoryModal
        isOpen={isVersionsOpen}
        onClose={() => setIsVersionsOpen(false)}
        note={activeNote}
        onRevert={handleRevertVersion}
      />

      {/* New Note Creation Confirmation Modal */}
      {showNewNoteConfirm && (
        <div
          className="modal d-block bg-dark bg-opacity-75"
          style={{ zIndex: 1060 }}
          tabIndex="-1"
          onClick={() => setShowNewNoteConfirm(false)}
        >
          <div
            className="modal-dialog modal-dialog-centered modal-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-content bg-mono-surface border-mono text-light shadow-lg">
              
              <div className="modal-header border-bottom border-mono bg-mono-dark py-3 px-4">
                <h5 className="modal-title font-mono fs-6 d-flex align-items-center gap-2 text-white fw-bold mb-0">
                  <Plus size={18} />
                  <span>Create New Memory Note?</span>
                </h5>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={() => setShowNewNoteConfirm(false)}
                ></button>
              </div>

              <div className="modal-body p-4 font-mono fs-7">
                <p className="text-light mb-2">
                  Do you want to initialize a new blank memory note draft?
                </p>
                <div className="p-3 bg-mono-dark border border-mono-muted rounded text-secondary fs-8">
                  You can type your thoughts or paste raw content, then use <strong className="text-white">Auto-Organize</strong> or <strong className="text-white">Smart Merge</strong> to automatically categorize, tag, and structure your memory.
                </div>
              </div>

              <div className="modal-footer border-top border-mono bg-mono-dark py-3 px-4 d-flex align-items-center justify-content-end gap-3">
                <button
                  className="btn btn-mono-outline btn-sm font-mono fs-8 py-1.5 px-3.5"
                  onClick={() => setShowNewNoteConfirm(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-mono-primary btn-sm font-mono fs-8 py-1.5 px-4 d-flex align-items-center gap-2"
                  onClick={() => {
                    setShowNewNoteConfirm(false);
                    handleConfirmNewNote();
                  }}
                >
                  <Plus size={15} />
                  <span>Create Note</span>
                </button>
              </div>

            </div>
          </div>
        </div>
      )}

    </div>
  );
}
