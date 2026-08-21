import React, { useState, useEffect } from 'react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { Loader2, CheckCircle2, AlertTriangle, Activity, Trash2, ChevronUp, X } from 'lucide-react';
import { useNotesStore } from '@/store/useNotesStore';
import { cn } from '@/lib/utils';

export const TaskProgressWidget: React.FC = () => {
  const { tasks, clearFinishedTasks, cancelActiveMediaUpload } = useNotesStore();

  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const runningTasks = tasks.filter((t) => t.status === 'running');
  const finishedTasks = tasks.filter((t) => t.status !== 'running');

  // Update timer every second when any task is running
  useEffect(() => {
    if (runningTasks.length === 0) return;
    const interval = setInterval(() => {
      setElapsedSeconds((s) => s + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [runningTasks.length]);

  if (tasks.length === 0) return null;

  const hasRunning = runningTasks.length > 0;
  const primaryRunningTask = runningTasks[0];

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          title={
            hasRunning
              ? `${runningTasks.length} background task(s) running - click to view details`
              : `Activity History (${finishedTasks.length} completed tasks)`
          }
          className={cn(
            'flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono transition-all cursor-pointer select-none border',
            hasRunning
              ? 'bg-surface-selected border-foreground/30 text-foreground font-semibold animate-pulse shadow-2xs'
              : 'hover:bg-surface-hover hover:text-foreground text-muted-foreground border-transparent hover:border-border'
          )}
        >
          {hasRunning ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin text-foreground shrink-0" />
              <span className="truncate max-w-[140px]">
                {runningTasks.length === 1
                  ? primaryRunningTask.title
                  : `${runningTasks.length} running`}
              </span>
            </>
          ) : (
            <>
              <Activity className="w-3 h-3 text-muted-foreground shrink-0" />
              <span>Activity ({finishedTasks.length})</span>
            </>
          )}
          <ChevronUp className="w-2.5 h-2.5 opacity-50 shrink-0" />
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          side="top"
          align="start"
          sideOffset={8}
          className="z-50 min-w-[320px] max-w-md bg-popover text-popover-foreground rounded-xl p-2.5 border border-border shadow-2xl text-xs space-y-2.5 animate-in fade-in zoom-in-95"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-1.5 pb-1.5 border-b border-border/60">
            <div className="flex items-center gap-1.5 font-bold text-foreground">
              <Activity className="w-3.5 h-3.5" />
              <span>Background Tasks & Activity</span>
            </div>
            {finishedTasks.length > 0 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  clearFinishedTasks();
                }}
                className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-surface-hover cursor-pointer border border-transparent hover:border-border"
                title="Clear completed task history"
              >
                <Trash2 className="w-2.5 h-2.5" />
                <span>Clear History</span>
              </button>
            )}
          </div>

          {/* Active Running Tasks Section */}
          {hasRunning && (
            <div className="space-y-1.5 px-0.5">
              <div className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider px-1">
                In Progress ({runningTasks.length})
              </div>
              <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
                {runningTasks.map((t) => {
                  const runningTimeSec = Math.max(1, Math.round((Date.now() - t.startedAt) / 1000));
                  return (
                    <div
                      key={t.id}
                      className="p-2.5 rounded-lg bg-surface-hover border border-border/80 space-y-1.5 shadow-2xs"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 truncate">
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-foreground shrink-0" />
                          <span className="font-bold text-foreground truncate">{t.title}</span>
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <span className="text-[10px] font-mono text-muted-foreground">
                            {runningTimeSec}s
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              cancelActiveMediaUpload();
                            }}
                            className="p-1 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors cursor-pointer"
                            title="Cancel task"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>

                      </div>
                      {t.description && (
                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                          {t.description}
                        </p>
                      )}
                      {/* Subtle animated progress bar */}
                      <div className="w-full h-1 bg-border/60 rounded-full overflow-hidden">
                        <div className="h-full bg-foreground rounded-full animate-pulse w-3/4" />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Recent Completed / Failed Tasks Section */}
          {finishedTasks.length > 0 && (
            <div className="space-y-1.5 px-0.5">
              <div className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider px-1">
                Recent Completed Tasks ({finishedTasks.length})
              </div>
              <div className="space-y-1 max-h-52 overflow-y-auto pr-1">
                {finishedTasks.map((t) => (
                  <div
                    key={t.id}
                    className="p-2 rounded-lg bg-surface-hover/50 hover:bg-surface-hover border border-border/40 space-y-0.5 text-xs transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 truncate">
                        {t.status === 'success' ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-foreground shrink-0" />
                        ) : (
                          <AlertTriangle className="w-3.5 h-3.5 text-destructive shrink-0" />
                        )}
                        <span className="font-semibold text-foreground truncate">{t.title}</span>
                      </div>
                      {t.completedAt && (
                        <span className="text-[10px] font-mono text-muted-foreground/70 shrink-0">
                          {new Date(t.completedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                      )}
                    </div>
                    {t.resultSummary && (
                      <p className="text-[11px] text-muted-foreground leading-snug break-words">
                        {t.resultSummary}
                      </p>
                    )}
                    {t.error && (
                      <p className="text-[11px] text-destructive leading-snug break-words">
                        {t.error}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
};
