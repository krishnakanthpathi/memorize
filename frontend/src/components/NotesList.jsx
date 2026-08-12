import React from 'react';
import { FileText } from 'lucide-react';

export default function NotesList({
  notes,
  activeNoteId,
  onSelectNote,
  hasActiveFilters,
  isLoadingNotes,
}) {
  return (
    <div className="d-flex flex-column h-100 bg-mono-dark border-end border-mono overflow-auto">
      
      {/* Header bar for Notes Stream */}
      <div className="px-3 py-2 border-bottom border-mono bg-mono-surface d-flex align-items-center justify-content-between">
        <span className="font-mono fs-8 text-uppercase text-secondary">
          Notes Stream ({notes.length})
        </span>
        {hasActiveFilters && (
          <span className="badge bg-mono-dark text-secondary border border-mono fs-8 font-mono">
            Filtered
          </span>
        )}
      </div>

      {/* Full Uncropped Title Cards (Title & Category ONLY) or Bootstrap Spinner */}
      <div className="p-2.5 d-flex flex-column gap-2 overflow-auto flex-grow-1">
        {isLoadingNotes ? (
          <div className="text-center py-5 px-3 my-auto">
            <div className="spinner-border text-light mb-2" role="status" style={{ width: '1.75rem', height: '1.75rem' }}>
              <span className="visually-hidden">Loading memories...</span>
            </div>
            <p className="text-secondary font-mono fs-8 mb-0">Filtering memories...</p>
          </div>
        ) : notes.length === 0 ? (
          <div className="text-center py-5 px-3 text-secondary my-auto">
            <FileText size={28} className="mb-2 opacity-50" />
            <p className="mb-1 fs-7">No notes found.</p>
            <small className="fs-8">Try adjusting filter selections.</small>
          </div>
        ) : (
          notes.map((note) => {
            const isActive = activeNoteId === note.id;

            return (
              <div
                key={note.id}
                className={`card-mono p-3 cursor-pointer ${isActive ? 'card-mono-active' : ''}`}
                onClick={() => onSelectNote(note.id)}
                style={{ cursor: 'pointer' }}
              >
                {/* Full Uncropped Title & Category Badge */}
                <div className="d-flex align-items-start justify-content-between gap-2">
                  <h6
                    className="mb-0 font-weight-semibold text-light fs-7 lh-sm text-wrap pe-1"
                    style={{ wordBreak: 'break-word' }}
                  >
                    {note.title || 'Untitled Note'}
                  </h6>
                  <span className="badge bg-mono-dark border border-mono text-secondary font-mono fs-8 text-uppercase flex-shrink-0">
                    {note.category}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
