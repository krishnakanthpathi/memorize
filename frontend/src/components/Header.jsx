import React from 'react';
import { Brain, Plus, MessageSquare, Sliders, FileText, PanelLeftClose, PanelLeft, ListFilter, Cpu, ChevronDown } from 'lucide-react';

export default function Header({
  activeView,
  setActiveView,
  onNewNote,
  onToggleChat,
  isBrainFilled,
  setIsBrainFilled,
  isSidebarOpen,
  setIsSidebarOpen,
  isNotesListOpen,
  setIsNotesListOpen,
  activeModel,
  modelsData,
  onSelectModel,
}) {
  return (
    <header className="border-bottom border-mono bg-mono-surface px-3 py-2">
      <div className="container-fluid d-flex align-items-center justify-content-between p-0">
        
        {/* Left Section: Brain Icon & Brand Title (+ Side Panel Toggles only in Notes mode) */}
        <div className="d-flex align-items-center gap-2.5">
          
          {/* Brain Icon & MEMORIZE Brand Name */}
          <div className="d-flex align-items-center gap-2 me-1">
            <button
              className={`brain-icon-btn ${isBrainFilled ? 'filled' : 'hollow'}`}
              onClick={() => setIsBrainFilled(!isBrainFilled)}
              title={`Brain Icon Mode: ${isBrainFilled ? 'Filled' : 'Hollow'} (Click to toggle)`}
              type="button"
            >
              <Brain size={20} strokeWidth={isBrainFilled ? 1.5 : 2} />
            </button>
            <span className="fw-bold tracking-tight text-white font-mono fs-6 user-select-none">
              MEMORIZE
            </span>
          </div>

          {/* Side Panel Toggles (ONLY visible in Notes mode!) */}
          {activeView === 'notes' && (
            <>
              {/* Toggle Left Sidebar */}
              <button
                className={`btn btn-mono-outline btn-sm p-1 px-2 ${!isSidebarOpen ? 'btn-mono-active' : ''}`}
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                title={isSidebarOpen ? 'Hide Category & Tag Sidebar' : 'Show Category & Tag Sidebar'}
                type="button"
              >
                {isSidebarOpen ? <PanelLeftClose size={16} /> : <PanelLeft size={16} />}
              </button>

              {/* Toggle Notes List Stream */}
              <button
                className={`btn btn-mono-outline btn-sm p-1 px-2 ${!isNotesListOpen ? 'btn-mono-active' : ''}`}
                onClick={() => setIsNotesListOpen(!isNotesListOpen)}
                title={isNotesListOpen ? 'Hide Notes Stream Pane' : 'Show Notes Stream Pane'}
                type="button"
              >
                <ListFilter size={16} />
              </button>
            </>
          )}

        </div>

        {/* Center Section: View Mode Switcher */}
        <div className="nav nav-pills bg-mono-dark p-1 rounded border border-mono-muted">
          <button
            className={`nav-link btn-sm py-1 px-3 d-flex align-items-center gap-2 rounded-1 ${
              activeView === 'notes' ? 'btn-mono-active text-white' : 'text-secondary hover-white'
            }`}
            onClick={() => setActiveView('notes')}
          >
            <FileText size={14} />
            <span>Notes</span>
          </button>

          <button
            className={`nav-link btn-sm py-1 px-3 d-flex align-items-center gap-2 rounded-1 ${
              activeView === 'admin' ? 'btn-mono-active text-white' : 'text-secondary hover-white'
            }`}
            onClick={() => setActiveView('admin')}
          >
            <Sliders size={14} />
            <span>Admin</span>
          </button>
        </div>

        {/* Right Section: Model Selector & Actions */}
        <div className="d-flex align-items-center gap-2">
          
          {/* Dynamic LLM Model Selector Dropdown */}
          <div className="dropdown">
            <button
              className="btn btn-mono-outline btn-sm font-mono fs-8 text-light dropdown-toggle d-flex align-items-center gap-1.5 py-1 px-2.5"
              type="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
              title="Select Active Backend LLM Model"
            >
              <Cpu size={14} className="text-secondary flex-shrink-0" />
              <span className="fw-semibold text-truncate" style={{ maxWidth: '140px' }}>
                {activeModel}
              </span>
            </button>
            <ul className="dropdown-menu dropdown-menu-end bg-mono-surface border-mono shadow-lg p-1" style={{ minWidth: '220px' }}>
              <li className="dropdown-header font-mono fs-8 text-uppercase text-secondary px-2 py-1">
                Discovered Ollama & API Models
              </li>
              {modelsData?.generative_models?.map((m) => (
                <li key={m.id}>
                  <button
                    type="button"
                    className={`dropdown-item btn-sm font-mono fs-8 rounded py-1 px-2 d-flex align-items-center justify-content-between ${
                      m.id === activeModel ? 'active bg-mono-dark text-white fw-bold' : 'text-light'
                    }`}
                    onClick={() => onSelectModel(m.id)}
                  >
                    <span className="text-truncate">{m.name || m.id}</span>
                    <span className="badge bg-mono-dark text-secondary border border-mono-muted fs-8 ms-2">
                      {(m.provider || 'ollama').toUpperCase()}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* New Note Action */}
          <button
            className="btn btn-mono-primary btn-sm d-flex align-items-center gap-1"
            onClick={onNewNote}
          >
            <Plus size={16} />
            <span>New Note</span>
          </button>

          {/* GraphRAG Companion Chat Drawer Trigger */}
          <button
            className="btn btn-mono-outline btn-sm d-flex align-items-center gap-1 text-light"
            onClick={onToggleChat}
            title="Open GraphRAG Companion Chat"
          >
            <MessageSquare size={16} />
            <span className="d-none d-md-inline">Chat</span>
          </button>

        </div>

      </div>
    </header>
  );
}
