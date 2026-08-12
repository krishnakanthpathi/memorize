import React, { useState, useEffect } from 'react';
import { Sparkles, Save, Trash2, History, Tag, Folder, CheckCircle, RefreshCw, ChevronDown, ChevronUp, AlertTriangle, Zap } from 'lucide-react';
import { fetchAutoSuggestion } from '../services/api';

export default function NoteEditor({
  note,
  onSave,
  onDelete,
  onAutoOrganize,
  onSmartMerge,
  onOpenVersions,
  availableCategories,
  activeModel,
  isOrganizing,
}) {
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('personal');
  const [tags, setTags] = useState([]);
  const [tagInput, setTagInput] = useState('');
  const [content, setContent] = useState('');
  const [summary, setSummary] = useState('');
  const [isSavedAlert, setIsSavedAlert] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);

  // VS Code Copilot Ghost Text State
  const [ghostText, setGhostText] = useState('');

  useEffect(() => {
    if (note) {
      setTitle(note.title || '');
      setCategory(note.category || 'personal');
      setTags(note.tags || []);
      setContent(note.content || '');
      setSummary(note.summary || '');
      setGhostText('');
    } else {
      setTitle('');
      setCategory('personal');
      setTags([]);
      setContent('');
      setSummary('');
      setGhostText('');
    }
  }, [note]);

  // Handle Tab key interception for VS Code Copilot Ghost Text completion
  const handleEditorKeyDown = (e) => {
    if (e.key === 'Tab' && ghostText) {
      e.preventDefault();
      // Accept VS Code Ghost Text Completion!
      setContent((prev) => `${prev}${ghostText}`);
      setGhostText('');
    } else if (e.key === 'Escape') {
      setGhostText('');
    }
  };

  // Trigger VS Code style Ghost Text suggestions based on active model & typed text
  useEffect(() => {
    if (!content.trim()) {
      setGhostText('');
      return;
    }

    const timer = setTimeout(() => {
      const lower = content.toLowerCase();
      if (lower.includes('pruning') && !lower.includes('magnitude')) {
        setGhostText('\n\n### Ghost Copilot Completion:\n- Magnitude Pruning: Zeroing weights below threshold.\n- Structured Pruning: Removing channels for GPU speedup.');
      } else if (lower.includes('graphrag') && !lower.includes('chromadb')) {
        setGhostText('\n\n### Ghost Copilot Completion:\n- ChromaDB Hybrid Vector Retrieval\n- Multi-Hop LangGraph Relationship Extraction');
      } else if (lower.includes('sync') && !lower.includes('sqlite')) {
        setGhostText('\n\n### Ghost Copilot Completion:\n- SQLite Relational Index Audit\n- Zero Drift Guarantee Protocol');
      } else if (content.endsWith(' ')) {
        setGhostText(` // Press [Tab] to complete synthesis via ${activeModel}...`);
      } else {
        setGhostText('');
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [content, activeModel]);

  const handleAddTag = (e) => {
    if ((e.key === 'Enter' || e.key === ',') && tagInput.trim()) {
      e.preventDefault();
      const cleanTag = tagInput.trim().toLowerCase().replace(/^#/, '');
      if (!tags.includes(cleanTag)) {
        setTags([...tags, cleanTag]);
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleSaveClick = () => {
    onSave({
      id: note?.id,
      title: title || 'Untitled Note',
      category,
      tags,
      content,
      summary,
    });
    setIsSavedAlert(true);
    setTimeout(() => setIsSavedAlert(false), 2000);
  };

  return (
    <div className="d-flex flex-column h-100 bg-mono-dark p-3.5 overflow-hidden">
      
      {/* Top Action Header */}
      <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom border-mono flex-shrink-0">
        <div className="d-flex align-items-center gap-2 flex-wrap">
          
          {/* ✨ Auto-Organize Button */}
          <button
            className="btn btn-mono-primary btn-sm py-1.5 px-3 fs-8 d-flex align-items-center gap-2"
            onClick={async () => {
              const res = await onAutoOrganize(content, title);
              if (res && res.status === 'success') {
                if (res.title) setTitle(res.title);
                if (res.category) setCategory(res.category);
                if (res.tags) setTags(res.tags);
                if (res.summary) setSummary(res.summary);
                if (res.organized_content) setContent(res.organized_content);
              }
            }}
            disabled={isOrganizing || !content.trim()}
            title="Auto-generate title, tags, category, and summary using active LLM"
          >
            {isOrganizing ? (
              <>
                <span className="spinner-border spinner-border-sm text-light me-1" role="status" aria-hidden="true"></span>
                <span>Organizing...</span>
              </>
            ) : (
              <>
                <Sparkles size={14} className="me-1" />
                <span>Auto-Organize</span>
              </>
            )}
          </button>

          {/* ⚡ Smart Merge / Modify Memory Button */}
          <button
            className="btn btn-mono-outline btn-sm py-1.5 px-3 fs-8 d-flex align-items-center gap-2 text-light"
            onClick={async () => {
              const res = await onSmartMerge(content, title);
              if (res && res.status === 'success') {
                if (res.title) setTitle(res.title);
                if (res.category) setCategory(res.category);
                if (res.tags) setTags(res.tags);
                if (res.summary) setSummary(res.summary);
                if (res.organized_content) setContent(res.organized_content);
              }
            }}
            disabled={isOrganizing || !content.trim()}
            title="Use active LLM to contextually merge & modify memory with editor content"
          >
            <Zap size={14} className="me-1 text-white" />
            <span>Smart Merge</span>
          </button>

          {/* 💡 AI Auto-Suggest Button (Backend LLM Powered) */}
          <button
            className="btn btn-mono-outline btn-sm py-1.5 px-3 fs-8 d-flex align-items-center gap-2 text-light"
            onClick={async () => {
              setIsSuggesting(true);
              try {
                const res = await fetchAutoSuggestion(content, title, activeModel);
                if (res.suggestion) {
                  setGhostText(`\n\n### AI Auto-Suggestion (${res.model || activeModel}):\n${res.suggestion}`);
                }
              } catch (e) {
                console.warn('Auto-suggest error:', e);
              } finally {
                setIsSuggesting(false);
              }
            }}
            disabled={isSuggesting || !content.trim()}
            title="Generate AI continuation & key point suggestions using backend LLM"
          >
            {isSuggesting ? (
              <>
                <span className="spinner-border spinner-border-sm text-warning me-1" role="status" aria-hidden="true"></span>
                <span>Suggesting...</span>
              </>
            ) : (
              <>
                <Sparkles size={14} className="me-1 text-warning" />
                <span>Auto-Suggest</span>
              </>
            )}
          </button>

          {/* 💾 Save Note */}
          <button
            className="btn btn-mono-outline btn-sm py-1.5 px-3 fs-8 d-flex align-items-center gap-2 text-light"
            onClick={handleSaveClick}
          >
            <Save size={14} className="me-1" />
            <span>Save</span>
          </button>

          {/* Version History Button */}
          {note?.id && (
            <button
              className="btn btn-mono-outline btn-sm py-1.5 px-2.5 fs-8 d-flex align-items-center gap-2 text-secondary"
              onClick={onOpenVersions}
              title="View Version Snapshots"
            >
              <History size={14} className="me-1" />
              <span>History ({note.versions?.length || 1})</span>
            </button>
          )}
        </div>

        {/* Saved Alert & Delete Trigger */}
        <div className="d-flex align-items-center gap-2">
          {isSavedAlert && (
            <span className="text-success font-mono fs-8 d-flex align-items-center gap-1.5 me-2">
              <CheckCircle size={14} /> Saved
            </span>
          )}
          {note?.id && (
            <button
              className="btn btn-mono-outline btn-sm p-1.5 px-2 text-danger border-0 hover-white"
              onClick={() => setShowDeleteConfirm(true)}
              title="Delete Note"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Note Title Input */}
      <div className="mb-2 flex-shrink-0">
        <input
          type="text"
          className="form-control bg-transparent border-0 text-white fw-bold px-1 focus-none"
          placeholder="Note Title..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={{ fontSize: '1.45rem', outline: 'none', boxShadow: 'none' }}
        />
      </div>

      {/* Upward Sub-Header Row: Category (Folder Icon) & Tags Settings Dropdown */}
      <div className="d-flex align-items-center justify-content-between mb-3 pb-2.5 border-bottom border-mono-muted flex-shrink-0 fs-8 font-mono">
        
        {/* Bootstrap Category Dropdown Component */}
        <div className="dropdown">
          <button
            className="btn btn-sm btn-mono-outline dropdown-toggle font-mono fs-8 border-0 bg-transparent text-secondary text-capitalize fw-medium d-flex align-items-center gap-2 px-1 py-0.5"
            type="button"
            data-bs-toggle="dropdown"
            aria-expanded="false"
          >
            <Folder size={14} className="text-secondary flex-shrink-0" />
            <span>{availableCategories?.find(c => c.id === category)?.name || category}</span>
          </button>
          <ul className="dropdown-menu bg-mono-surface border-mono shadow-sm">
            {availableCategories?.filter(c => c.id !== 'all').map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  className={`dropdown-item btn-sm font-mono fs-8 text-capitalize ${
                    category === c.id ? 'active bg-mono-dark text-white' : 'text-light'
                  }`}
                  onClick={() => setCategory(c.id)}
                >
                  {c.name}
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Tags Settings Dropdown */}
        <div className="dropdown">
          <button
            className="btn btn-sm btn-mono-outline dropdown-toggle font-mono fs-8 border-0 bg-transparent text-secondary fw-medium d-flex align-items-center gap-2 px-1 py-0.5"
            type="button"
            data-bs-toggle="dropdown"
            aria-expanded="false"
            data-bs-auto-close="outside"
          >
            <Tag size={14} className="text-secondary flex-shrink-0" />
            <span>Tags ({tags.length})</span>
          </button>
          <div className="dropdown-menu dropdown-menu-end bg-mono-surface border-mono shadow-lg p-3" style={{ minWidth: '250px', maxWidth: '340px' }}>
            <h6 className="font-mono fs-8 text-uppercase text-secondary mb-2">Note Tags ({tags.length})</h6>
            
            {/* Tag Pills Container */}
            <div className="d-flex flex-wrap gap-1.5 mb-3" style={{ maxHeight: '140px', overflowY: 'auto' }}>
              {tags.length === 0 ? (
                <span className="text-secondary fs-8 font-mono opacity-75">No tags added yet.</span>
              ) : (
                tags.map((tag) => (
                  <span
                    key={tag}
                    className="badge rounded-pill bg-dark border border-secondary text-secondary font-mono fs-8 py-1.5 px-2.5 d-flex align-items-center gap-1.5"
                  >
                    #{tag}
                    <button
                      type="button"
                      className="btn-close btn-close-white ms-1"
                      style={{ width: '7px', height: '7px' }}
                      aria-label="Remove tag"
                      onClick={() => handleRemoveTag(tag)}
                    ></button>
                  </span>
                ))
              )}
            </div>

            {/* Quick Add Tag Input */}
            <div className="input-group input-group-sm">
              <input
                type="text"
                className="form-control form-control-mono font-mono fs-8"
                placeholder="Add new tag..."
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleAddTag}
              />
              <button
                type="button"
                className="btn btn-mono-primary btn-sm font-mono fs-8 px-2.5"
                onClick={() => {
                  if (tagInput.trim()) {
                    const cleanTag = tagInput.trim().toLowerCase().replace(/^#/, '');
                    if (!tags.includes(cleanTag)) setTags([...tags, cleanTag]);
                    setTagInput('');
                  }
                }}
              >
                + Add
              </button>
            </div>
          </div>
        </div>

      </div>

      {/* Main Text Editor Workspace with Seamless Full-Width Ghost Text Completion */}
      <div className="flex-grow-1 d-flex flex-column mb-3 overflow-hidden border border-mono rounded bg-mono-surface">
        <textarea
          className="form-control form-control-mono flex-grow-1 font-mono p-3.5 border-0 text-light bg-transparent"
          placeholder="Type or paste markdown content here (Try typing 'pruning', 'graphrag', or 'sync' to see Copilot ghost completion)..."
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleEditorKeyDown}
          style={{ outline: 'none', boxShadow: 'none', resize: 'none' }}
        />

        {/* Full-Width Copilot Ghost Completion Bar (Uncropped, Full Width, Seamless) */}
        {ghostText && (
          <div className="p-2.5 px-3 bg-dark border-top border-mono font-mono fs-8 text-light d-flex align-items-center justify-content-between gap-3 flex-shrink-0">
            <div className="d-flex align-items-center gap-2 text-truncate">
              <span className="badge bg-secondary-subtle text-secondary-emphasis font-mono fs-8 flex-shrink-0">
                Ghost Completion
              </span>
              <span className="text-secondary text-truncate font-mono" style={{ fontStyle: 'italic', color: '#a1a1aa' }}>
                {ghostText.trim()}
              </span>
            </div>
            <div className="d-flex align-items-center gap-2 flex-shrink-0">
              <button
                type="button"
                className="btn btn-mono-primary btn-sm py-1 px-3 font-mono fs-8 d-flex align-items-center gap-1.5"
                onClick={() => {
                  setContent((prev) => `${prev}${ghostText}`);
                  setGhostText('');
                }}
              >
                <span>Insert</span>
                <kbd className="bg-dark text-white px-1.5 py-0.5 rounded border border-secondary fs-8">Tab ↹</kbd>
              </button>
              <button
                type="button"
                className="btn-close btn-close-white"
                aria-label="Dismiss ghost text"
                onClick={() => setGhostText('')}
              ></button>
            </div>
          </div>
        )}
      </div>

      {/* Optional AI Summary Collapsible Bar */}
      {summary && (
        <div className="flex-shrink-0">
          <button
            className="btn btn-mono-outline btn-sm w-100 py-1.5 px-3 text-start font-mono fs-8 text-secondary d-flex align-items-center justify-content-between"
            onClick={() => setShowSummary(!showSummary)}
          >
            <span className="d-flex align-items-center gap-2">
              <Sparkles size={13} className="text-light" />
              <span>AI Executive Summary</span>
            </span>
            {showSummary ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
          </button>
          {showSummary && (
            <div className="p-3 mt-2 bg-mono-surface border border-mono-muted rounded text-light fs-8 font-mono lh-base">
              {summary}
            </div>
          )}
        </div>
      )}

      {/* Large Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div
          className="modal d-block bg-dark bg-opacity-75"
          style={{ zIndex: 1060 }}
          tabIndex="-1"
          onClick={() => setShowDeleteConfirm(false)}
        >
          <div
            className="modal-dialog modal-dialog-centered modal-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-content bg-mono-surface border-mono text-light shadow-lg">
              
              <div className="modal-header border-bottom border-mono bg-mono-dark py-3 px-4">
                <h5 className="modal-title font-mono fs-6 d-flex align-items-center gap-2 text-danger fw-bold mb-0">
                  <AlertTriangle size={18} />
                  <span>Delete Memory Note</span>
                </h5>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={() => setShowDeleteConfirm(false)}
                ></button>
              </div>

              <div className="modal-body p-4 font-mono fs-7">
                <p className="text-light mb-2">
                  Are you sure you want to permanently delete <strong className="text-white">"{title || 'Untitled Note'}"</strong>?
                </p>
                <div className="p-3 bg-mono-dark border border-mono-muted rounded text-secondary fs-8">
                  This action will permanently delete the Markdown file on disk, SQLite database index record, and ChromaDB vector embeddings chunk. This cannot be undone.
                </div>
              </div>

              <div className="modal-footer border-top border-mono bg-mono-dark py-3 px-4 d-flex align-items-center justify-content-end gap-3">
                <button
                  className="btn btn-mono-outline btn-sm font-mono fs-8 py-1.5 px-3.5"
                  onClick={() => setShowDeleteConfirm(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-danger btn-sm font-mono fs-8 py-1.5 px-4 d-flex align-items-center gap-2"
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    onDelete(note.id);
                  }}
                >
                  <Trash2 size={14} />
                  <span>Delete Permanently</span>
                </button>
              </div>

            </div>
          </div>
        </div>
      )}

    </div>
  );
}
