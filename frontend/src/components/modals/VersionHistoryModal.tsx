import React, { useEffect, useState } from 'react';
import {
  History,
  RotateCcw,
  X,
  Clock,
  Loader2,
  CheckCircle2,
  FileText,
  Calendar,
  Layers,
} from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { useNotesStore } from '@/store/useNotesStore';
import { api } from '@/services/api';
import { VersionItem } from '@/types';
import { cn, formatDateRelative } from '@/lib/utils';

export const VersionHistoryModal: React.FC = () => {
  const {
    activeModal,
    setActiveModal,
    activeNoteId,
    notes,
    fetchNotes,
  } = useNotesStore();

  const isOpen = activeModal === 'versions';
  const [versions, setVersions] = useState<VersionItem[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<VersionItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [reverting, setReverting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const currentNote = notes.find((n) => n.id === activeNoteId);

  useEffect(() => {
    if (isOpen && activeNoteId) {
      setLoading(true);
      setSuccessMsg('');
      api.getVersions(activeNoteId)
        .then((items) => {
          setVersions(items);
          if (items.length > 0) {
            setSelectedVersion(items[0]);
          } else {
            setSelectedVersion(null);
          }
        })
        .catch((err) => {
          console.error('Failed to load version history:', err);
          setVersions([]);
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, activeNoteId]);

  const handleRevert = async (versionNumber: number) => {
    if (!activeNoteId) return;
    if (!confirm(`Are you sure you want to revert to Version #${versionNumber}?`)) return;

    setReverting(true);
    try {
      await api.revertVersion(activeNoteId, versionNumber);
      setSuccessMsg(`Successfully restored Version #${versionNumber}!`);
      await fetchNotes();
      setTimeout(() => {
        setActiveModal(null);
      }, 1200);
    } catch (err: any) {
      alert(`Revert failed: ${err.message}`);
    } finally {
      setReverting(false);
    }
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && setActiveModal(null)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-4xl bg-card text-card-foreground border border-border rounded-xl shadow-2xl z-50 p-0 overflow-hidden flex flex-col h-[80vh] animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="h-14 px-6 border-b border-border flex items-center justify-between bg-surface-sidebar select-none">
            <div className="flex items-center gap-2.5">
              <History className="w-5 h-5 text-foreground" />
              <div>
                <h3 className="text-sm font-bold truncate max-w-md">
                  Version History: {currentNote?.title || 'Note'}
                </h3>
                <p className="text-[10px] text-muted-foreground font-mono">
                  Browse previous snapshots and roll back changes
                </p>
              </div>
            </div>

            <Dialog.Close asChild>
              <button className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors">
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>

          {/* Success Banner */}
          {successMsg && (
            <div className="px-6 py-2 bg-emerald-500/10 border-b border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-2 font-medium">
              <CheckCircle2 className="w-4 h-4" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Main 2-column view inside modal */}
          <div className="flex-1 flex overflow-hidden">
            {/* Version list timeline */}
            <div className="w-72 border-r border-border overflow-y-auto bg-surface-list divide-y divide-border/40 p-2">
              <div className="px-3 py-2 text-[10px] uppercase font-bold text-muted-foreground tracking-wider">
                Snapshots ({versions.length})
              </div>

              {loading ? (
                <div className="py-12 text-center text-muted-foreground">
                  <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                  <span className="text-xs">Loading versions...</span>
                </div>
              ) : versions.length === 0 ? (
                <div className="p-6 text-center text-muted-foreground text-xs">
                  No previous versions recorded yet. Versions are created automatically whenever you modify existing notes.
                </div>
              ) : (
                versions.map((ver) => {
                  const isSelected = selectedVersion?.version_number === ver.version_number;
                  return (
                    <div
                      key={ver.version_number}
                      onClick={() => setSelectedVersion(ver)}
                      className={cn(
                        'p-3 rounded-lg cursor-pointer transition-colors text-xs space-y-1',
                        isSelected
                          ? 'bg-surface-selected font-semibold border-l-2 border-foreground'
                          : 'hover:bg-surface-hover border-l-2 border-transparent'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-foreground">
                          v{ver.version_number}
                        </span>
                        <span className="text-[10px] text-muted-foreground font-mono">
                          {formatDateRelative(ver.created_at)}
                        </span>
                      </div>
                      <p className="text-[11px] text-muted-foreground truncate">
                        {ver.title}
                      </p>
                      <div className="text-[10px] text-muted-foreground font-mono flex items-center gap-1">
                        <Calendar className="w-2.5 h-2.5" />
                        <span>{new Date(ver.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Selected Version Preview */}
            <div className="flex-1 flex flex-col bg-surface-editor overflow-hidden">
              {selectedVersion ? (
                <>
                  <div className="p-4 border-b border-border flex items-center justify-between bg-surface-hover/30">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-foreground">
                          Version #{selectedVersion.version_number}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground capitalize">
                          {selectedVersion.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-muted-foreground font-mono mt-0.5">
                        Recorded at {new Date(selectedVersion.created_at).toLocaleString()}
                      </p>
                    </div>

                    <button
                      onClick={() => handleRevert(selectedVersion.version_number)}
                      disabled={reverting}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-foreground text-background text-xs font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 shadow-xs"
                    >
                      {reverting ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <RotateCcw className="w-3.5 h-3.5" />
                      )}
                      <span>Restore This Version</span>
                    </button>
                  </div>

                  <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    <h2 className="text-xl font-bold">{selectedVersion.title}</h2>
                    <pre className="p-4 rounded-lg bg-muted/50 border border-border font-mono text-xs whitespace-pre-wrap leading-relaxed overflow-x-auto">
                      {selectedVersion.content}
                    </pre>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-center p-8 text-muted-foreground text-xs">
                  Select a version snapshot to preview its content and rollback.
                </div>
              )}
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
