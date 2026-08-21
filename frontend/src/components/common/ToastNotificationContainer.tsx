import React, { useEffect } from 'react';
import { CheckCircle2, AlertTriangle, Info, X, Loader2 } from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';
import { ToastNotification } from '@/types';
import { cn } from '@/lib/utils';


export const ToastNotificationContainer: React.FC = () => {
  const { toasts, dismissToast } = useNotesStore();

  if (!toasts || toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none select-none"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={() => dismissToast(toast.id)} />
      ))}
    </div>
  );
};

interface ToastItemProps {
  toast: ToastNotification;
  onDismiss: () => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onDismiss }) => {
  useEffect(() => {
    const duration = toast.duration || 4500;
    const timer = setTimeout(() => {
      onDismiss();
    }, duration);
    return () => clearTimeout(timer);
  }, [toast, onDismiss]);

  const isError = toast.type === 'error';
  const isSuccess = toast.type === 'success';

  return (
    <div
      className={cn(
        'pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl border bg-card/95 backdrop-blur-md shadow-2xl text-xs transition-all animate-in slide-in-from-bottom-3 fade-in duration-200 ring-1 ring-border/50 text-foreground',
        isError ? 'border-destructive/40 bg-destructive/5' : 'border-border'
      )}
    >
      <div className="shrink-0 mt-0.5">
        {isSuccess ? (
          <CheckCircle2 className="w-4 h-4 text-foreground" />
        ) : isError ? (
          <AlertTriangle className="w-4 h-4 text-destructive" />
        ) : (
          <Info className="w-4 h-4 text-muted-foreground" />
        )}
      </div>

      <div className="flex-1 min-w-0 space-y-0.5">
        <h4 className="font-bold text-foreground text-xs leading-tight truncate">
          {toast.title}
        </h4>
        {toast.description && (
          <p className="text-[11px] text-muted-foreground leading-relaxed break-words line-clamp-3">
            {toast.description}
          </p>
        )}
      </div>

      <button
        onClick={onDismiss}
        className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors shrink-0 cursor-pointer"
        title="Dismiss"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
