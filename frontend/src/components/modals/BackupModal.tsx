import React, { useEffect, useState } from 'react';
import {
  HardDriveDownload,
  Download,
  Trash2,
  X,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  FileText,
  RotateCw,
} from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { useNotesStore } from '@/store/useNotesStore';
import { api } from '@/services/api';
import { cn } from '@/lib/utils';

export const BackupModal: React.FC = () => {
  const { activeModal, setActiveModal, fetchNotes, fetchCategories } = useNotesStore();
  const isOpen = activeModal === 'backup';

  const [readmeText, setReadmeText] = useState('');
  const [loading, setLoading] = useState(false);
  const [backingUp, setBackingUp] = useState(false);
  const [purging, setPurging] = useState(false);
  const [msg, setMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const loadBackupStatus = async () => {
    setLoading(true);
    setMsg(null);
    try {
      const data = await api.getBackupInfo();
      setReadmeText(data.readme_text || 'No previous backup recorded.');
    } catch (err: any) {
      setMsg({ text: `Failed to load backup info: ${err.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadBackupStatus();
    }
  }, [isOpen]);

  const handleCreateBackup = async () => {
    setBackingUp(true);
    setMsg(null);
    try {
      const res = await api.createBackup();
      setMsg({
        text: `Backup snapshot generated successfully! (${res.backup_count || 'all'} files backed up)`,
        type: 'success',
      });
      await loadBackupStatus();
    } catch (err: any) {
      setMsg({ text: `Backup error: ${err.message}`, type: 'error' });
    } finally {
      setBackingUp(false);
    }
  };

  const handlePurge = async () => {
    const confirmText = prompt('Type "PURGE" to permanently wipe all stored memories:');
    if (confirmText !== 'PURGE') return;

    setPurging(true);
    setMsg(null);
    try {
      await api.purgeAllMemories();
      setMsg({ text: 'All memories have been purged from database & disk.', type: 'success' });
      await fetchNotes();
      await fetchCategories();
      await loadBackupStatus();
    } catch (err: any) {
      setMsg({ text: `Purge failed: ${err.message}`, type: 'error' });
    } finally {
      setPurging(false);
    }
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && setActiveModal(null)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-xl bg-card text-card-foreground border border-border rounded-xl shadow-2xl z-50 p-0 overflow-hidden animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="h-14 px-6 border-b border-border flex items-center justify-between bg-surface-sidebar select-none">
            <div className="flex items-center gap-2.5">
              <HardDriveDownload className="w-5 h-5 text-foreground" />
              <div>
                <h3 className="text-sm font-bold leading-tight">Backup & Restore</h3>
                <p className="text-[10px] text-muted-foreground font-mono">
                  Full snapshots of Markdown files & SQLite databases
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={loadBackupStatus}
                title="Refresh Status"
                className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <RotateCw className={cn('w-4 h-4', loading && 'animate-spin')} />
              </button>
              <Dialog.Close asChild>
                <button className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </Dialog.Close>
            </div>
          </div>

          {/* Feedback */}
          {msg && (
            <div
              className={cn(
                'px-6 py-2 border-b text-xs flex items-center gap-2 font-medium',
                msg.type === 'success'
                  ? 'bg-surface-hover border-border text-foreground'
                  : 'bg-destructive/10 border-destructive/20 text-destructive'
              )}
            >
              {msg.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 shrink-0" />
              )}
              <span>{msg.text}</span>
            </div>
          )}


          {/* Content */}
          <div className="p-6 space-y-5 max-h-[70vh] overflow-y-auto text-xs">
            <div className="flex items-center justify-between p-4 rounded-xl bg-surface-hover border border-border">
              <div>
                <h4 className="font-bold text-foreground">Create Snapshot Backup</h4>
                <p className="text-[11px] text-muted-foreground">
                  Copies all memories and index tables to <code>data/backups/</code> with automated README.
                </p>
              </div>
              <button
                onClick={handleCreateBackup}
                disabled={backingUp}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-foreground text-background text-xs font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 shadow-xs shrink-0"
              >
                {backingUp ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Download className="w-3.5 h-3.5" />
                )}
                <span>Backup Now</span>
              </button>
            </div>

            {/* Readme Snapshot Log */}
            <div>
              <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1.5">
                Latest Backup Manifest:
              </label>
              <pre className="p-4 rounded-xl bg-surface-list border border-border font-mono text-[11px] whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed text-muted-foreground">
                {readmeText}
              </pre>
            </div>

            {/* Danger Zone */}
            <div className="pt-4 border-t border-border/80">
              <div className="p-4 rounded-xl border border-destructive/30 bg-destructive/5 flex items-center justify-between gap-4">
                <div>
                  <h4 className="font-bold text-destructive">Danger Zone: Purge Database</h4>
                  <p className="text-[11px] text-muted-foreground">
                    Permanently delete all markdown files, vector chunks, and database indexes.
                  </p>
                </div>
                <button
                  onClick={handlePurge}
                  disabled={purging}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-destructive text-destructive-foreground text-xs font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 shrink-0 shadow-xs"
                >
                  {purging ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="w-3.5 h-3.5" />
                  )}
                  <span>Purge All</span>
                </button>
              </div>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
