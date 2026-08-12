import React, { useState, useEffect } from 'react';
import { X, History, RotateCcw, Clock } from 'lucide-react';
import { fetchMemoryVersions } from '../services/api';

export default function VersionHistoryModal({ isOpen, onClose, note, onRevert }) {
  const [liveVersions, setLiveVersions] = useState(note?.versions || []);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen && note?.id) {
      let isMounted = true;
      setIsLoading(true);
      fetchMemoryVersions(note.id).then((res) => {
        if (isMounted && res.status === 'success' && res.versions) {
          setLiveVersions(res.versions);
        } else if (isMounted) {
          setLiveVersions(note.versions || []);
        }
        if (isMounted) setIsLoading(false);
      });
      return () => {
        isMounted = false;
      };
    }
  }, [isOpen, note?.id]);

  if (!isOpen || !note) return null;

  const versionsToDisplay = liveVersions.length > 0 ? liveVersions : (note.versions || []);

  return (
    <div
      className="modal d-block bg-dark bg-opacity-75"
      style={{ zIndex: 1060 }}
      tabIndex="-1"
      onClick={onClose}
    >
      <div
        className="modal-dialog modal-dialog-centered modal-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-content bg-mono-surface border-mono text-light shadow-lg">
          
          <div className="modal-header border-bottom border-mono bg-mono-dark">
            <h5 className="modal-title font-mono fs-6 d-flex align-items-center gap-2 text-white">
              <History size={18} />
              <span>Version History Timeline: {note.title}</span>
            </h5>
            <button
              type="button"
              className="btn-close btn-close-white"
              onClick={onClose}
            ></button>
          </div>

          <div className="modal-body p-3 font-mono fs-8">
            <p className="text-secondary mb-3">
              Every save and auto-organize creates an immutable version snapshot. Select a previous version to roll back.
            </p>

            <div className="d-flex flex-column gap-2">
              {versionsToDisplay.map((ver) => (
                <div
                  key={ver.version_number}
                  className="p-3 bg-mono-dark border border-mono-muted rounded d-flex align-items-center justify-content-between gap-3"
                >
                  <div>
                    <div className="d-flex align-items-center gap-2 mb-1">
                      <span className="badge bg-secondary text-dark">
                        Version {ver.version_number}
                      </span>
                      <small className="text-secondary d-flex align-items-center gap-1">
                        <Clock size={12} />
                        {new Date(ver.created_at).toLocaleString()}
                      </small>
                    </div>
                    <p className="mb-0 text-light opacity-90">{ver.summary}</p>
                  </div>

                  <button
                    className="btn btn-mono-outline btn-sm d-flex align-items-center gap-1 text-light"
                    onClick={() => onRevert(ver.version_number)}
                  >
                    <RotateCcw size={14} />
                    <span>Revert</span>
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="modal-footer border-top border-mono bg-mono-dark">
            <button className="btn btn-mono-outline btn-sm" onClick={onClose}>
              Close
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
