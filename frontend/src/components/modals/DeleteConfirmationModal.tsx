import React from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { useNotesStore } from '@/store/useNotesStore';

export const DeleteConfirmationModal: React.FC = () => {
  const { notePendingDelete, cancelDeleteNote, confirmDeleteNote } = useNotesStore();

  const isOpen = notePendingDelete !== null;
  if (!notePendingDelete) return null;

  const { title, permanent, count = 1, isEmptyTrash } = notePendingDelete;

  const modalTitle = isEmptyTrash
    ? `Empty Trash (${count} Note${count > 1 ? 's' : ''})?`
    : count > 1
    ? permanent
      ? `Permanently Delete ${count} Notes?`
      : `Move ${count} Notes to Trash?`
    : permanent
    ? 'Permanently Delete Note?'
    : 'Move Note to Trash?';

  const actionButtonText = isEmptyTrash
    ? 'Empty Trash'
    : count > 1
    ? permanent
      ? `Delete ${count} Notes`
      : `Move ${count} to Trash`
    : permanent
    ? 'Delete Permanently'
    : 'Move to Trash';

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && cancelDeleteNote()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-card text-card-foreground border border-border rounded-xl shadow-2xl z-50 p-0 overflow-hidden animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="h-14 px-6 border-b border-border flex items-center justify-between bg-surface-sidebar select-none">
            <div className="flex items-center gap-2.5 text-destructive">
              <AlertTriangle className="w-5 h-5" />
              <div>
                <h3 className="text-sm font-bold leading-tight">
                  {modalTitle}
                </h3>
              </div>
            </div>

            <Dialog.Close asChild>
              <button
                onClick={cancelDeleteNote}
                className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>

          {/* Content Body */}
          <div className="p-6 space-y-4 text-xs">
            <p className="text-muted-foreground leading-relaxed">
              {isEmptyTrash ? (
                <>
                  Are you sure you want to empty the Trash and permanently remove all{' '}
                  <strong className="text-foreground">{count} trashed note{count > 1 ? 's' : ''}</strong>?
                  This action cannot be undone.
                </>
              ) : count > 1 ? (
                permanent ? (
                  <>
                    Are you sure you want to permanently delete{' '}
                    <strong className="text-foreground">{count} selected notes</strong>?
                    This action cannot be undone and will remove all vector embeddings, version revisions, and database records.
                  </>
                ) : (
                  <>
                    Are you sure you want to move{' '}
                    <strong className="text-foreground">{count} selected notes</strong> to Trash?
                    You can restore them at any time from the Trash view.
                  </>
                )
              ) : permanent ? (
                <>
                  Are you sure you want to permanently delete{' '}
                  <strong className="text-foreground">"{title}"</strong>? This action cannot be
                  undone and will remove all vector embeddings, version revisions, and database records.
                </>
              ) : (
                <>
                  Are you sure you want to move{' '}
                  <strong className="text-foreground">"{title}"</strong> to Trash? You can restore it
                  at any time from the Trash view.
                </>
              )}
            </p>

            {/* Actions Button Row */}
            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={cancelDeleteNote}
                className="px-4 py-2 rounded-lg bg-surface-hover hover:bg-surface-selected text-foreground text-xs font-semibold border border-border transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDeleteNote}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-destructive text-destructive-foreground text-xs font-bold hover:opacity-90 transition-opacity shadow-xs cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{actionButtonText}</span>
              </button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
