import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  Wrench,
  Trash2,
  RotateCw,
  X,
  Loader2,
  Database,
  FileCode,
  Layers,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { useNotesStore } from '@/store/useNotesStore';
import { api } from '@/services/api';
import { AuditSummary } from '@/types';
import { cn } from '@/lib/utils';

export const AuditModal: React.FC = () => {
  const { activeModal, setActiveModal, fetchNotes, fetchCategories } = useNotesStore();
  const isOpen = activeModal === 'audit';

  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [fixing, setFixing] = useState(false);
  const [msg, setMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const loadAudit = async () => {
    setLoading(true);
    setMsg(null);
    try {
      const data = await api.getAuditSummary();
      setSummary(data);
    } catch (err: any) {
      setMsg({ text: `Failed to load audit: ${err.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadAudit();
    }
  }, [isOpen]);

  const handleAutoFix = async () => {
    setFixing(true);
    setMsg(null);
    try {
      const res = await api.runAuditFix();
      setSummary(res);
      setMsg({
        text: 'Auto-fix completed successfully! All storage layers reconciled.',
        type: 'success',
      });
      await fetchNotes();
      await fetchCategories();
    } catch (err: any) {
      setMsg({ text: `Auto-fix error: ${err.message}`, type: 'error' });
    } finally {
      setFixing(false);
    }
  };

  const handleDeleteOrphans = async (type: 'files' | 'indexes' | 'chunks') => {
    if (!confirm(`Are you sure you want to clean orphan ${type}?`)) return;
    try {
      await api.deleteOrphans(type);
      setMsg({ text: `Orphan ${type} cleaned successfully.`, type: 'success' });
      await loadAudit();
    } catch (err: any) {
      setMsg({ text: `Failed to clean orphan ${type}: ${err.message}`, type: 'error' });
    }
  };

  const totalOrphans = summary
    ? (summary.orphan_files_count || 0) +
      (summary.orphan_indexes_count || 0) +
      (summary.orphan_chunks_count || 0)
    : 0;

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && setActiveModal(null)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl bg-card text-card-foreground border border-border rounded-xl shadow-2xl z-50 p-0 overflow-hidden animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="h-14 px-6 border-b border-border flex items-center justify-between bg-surface-sidebar select-none">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="w-5 h-5 text-foreground" />
              <div>
                <h3 className="text-sm font-bold leading-tight">Storage Integrity & Audit</h3>
                <p className="text-[10px] text-muted-foreground font-mono">
                  Multi-tier consistency verification (SQLite, Markdown Files, Vector DB)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={loadAudit}
                title="Refresh Audit"
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

          {/* Feedback Message */}
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
          <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
            {loading && !summary ? (
              <div className="py-12 text-center text-muted-foreground">
                <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                <p className="text-xs">Auditing database records, filesystem, and vector embeddings...</p>
              </div>
            ) : summary ? (
              <>
                {/* 3-Tier Storage Metric Cards */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-4 rounded-xl bg-surface-hover border border-border/80 text-center">
                    <Database className="w-5 h-5 mx-auto mb-1.5 text-foreground" />
                    <span className="text-2xl font-bold font-mono block">
                      {summary.total_db_records}
                    </span>
                    <span className="text-[11px] text-muted-foreground">SQLite Records</span>
                  </div>

                  <div className="p-4 rounded-xl bg-surface-hover border border-border/80 text-center">
                    <FileCode className="w-5 h-5 mx-auto mb-1.5 text-foreground" />
                    <span className="text-2xl font-bold font-mono block">
                      {summary.total_files}
                    </span>
                    <span className="text-[11px] text-muted-foreground">Markdown Files</span>
                  </div>

                  <div className="p-4 rounded-xl bg-surface-hover border border-border/80 text-center">
                    <Layers className="w-5 h-5 mx-auto mb-1.5 text-foreground" />
                    <span className="text-2xl font-bold font-mono block">
                      {summary.total_vector_chunks}
                    </span>
                    <span className="text-[11px] text-muted-foreground">Vector Chunks</span>
                  </div>
                </div>

                {/* Integrity Status Report */}
                <div className="p-4 rounded-xl bg-surface-list border border-border space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {totalOrphans === 0 ? (
                        <CheckCircle2 className="w-5 h-5 text-foreground" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-foreground" />
                      )}
                      <div>
                        <h4 className="text-xs font-bold">
                          {totalOrphans === 0
                            ? 'All Storage Tiers Synced'
                            : `${totalOrphans} Discrepancies / Orphans Found`}
                        </h4>

                        <p className="text-[11px] text-muted-foreground">
                          {totalOrphans === 0
                            ? 'Files, database indexes, and ChromaDB vector embeddings are fully aligned.'
                            : 'Orphans can be automatically reconciled or cleaned below.'}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={handleAutoFix}
                      disabled={fixing}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-foreground text-background text-xs font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 shadow-xs"
                    >
                      {fixing ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Wrench className="w-3.5 h-3.5" />
                      )}
                      <span>1-Click Auto-Fix</span>
                    </button>
                  </div>

                  {/* Discrepancies Details */}
                  <div className="divide-y divide-border/40 text-xs pt-2">
                    <div className="py-2 flex items-center justify-between">
                      <span className="text-muted-foreground">Orphan Markdown Files</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold">
                          {summary.orphan_files_count}
                        </span>
                        {summary.orphan_files_count > 0 && (
                          <button
                            onClick={() => handleDeleteOrphans('files')}
                            className="p-1 text-destructive hover:bg-destructive/10 rounded"
                            title="Delete orphan files"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="py-2 flex items-center justify-between">
                      <span className="text-muted-foreground">Orphan DB Indexes</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold">
                          {summary.orphan_indexes_count}
                        </span>
                        {summary.orphan_indexes_count > 0 && (
                          <button
                            onClick={() => handleDeleteOrphans('indexes')}
                            className="p-1 text-destructive hover:bg-destructive/10 rounded"
                            title="Delete orphan indexes"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="py-2 flex items-center justify-between">
                      <span className="text-muted-foreground">Orphan ChromaDB Vector Chunks</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold">
                          {summary.orphan_chunks_count}
                        </span>
                        {summary.orphan_chunks_count > 0 && (
                          <button
                            onClick={() => handleDeleteOrphans('chunks')}
                            className="p-1 text-destructive hover:bg-destructive/10 rounded"
                            title="Delete orphan chunks"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
