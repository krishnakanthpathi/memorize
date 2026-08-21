import React, { useEffect } from 'react';
import { Command, X, Keyboard, FileText, Trash2, Pin, Star, Search, Settings, Save, Sparkles, FolderPlus } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { useNotesStore } from '@/store/useNotesStore';

interface ShortcutRow {
  title: string;
  keys: string[];
  description: string;
}

export const KeyboardShortcutsModal: React.FC = () => {
  const { activeModal, setActiveModal } = useNotesStore();
  const isOpen = activeModal === 'shortcuts';

  const shortcuts: { section: string; items: ShortcutRow[] }[] = [
    {
      section: 'Note Editing & Lifecycle',
      items: [
        { title: 'Save Note', keys: ['⌘/Ctrl', 'S'], description: 'Instantly save active note to backend' },
        { title: 'New Note', keys: ['⌘N', 'or', '⌥N', 'or', '⌃N'], description: 'Open Create Note confirmation modal' },
        { title: 'Delete Note', keys: ['⌘', '⌫'], description: 'Move active note to Trash' },
        { title: 'Pin Note', keys: ['⌘', '⇧', 'P'], description: 'Toggle pinned status of active note' },
        { title: 'Favorite Note', keys: ['⌘', '⇧', 'S'], description: 'Toggle favorite status of active note' },
      ],
    },
    {
      section: 'Navigation & Tools',
      items: [
        { title: 'Full Screen Mode', keys: ['F11', 'or', '⌘', '⇧', 'F'], description: 'Toggle native browser full screen' },
        { title: 'Zen Focus Mode', keys: ['⌘', '⇧', 'Z'], description: 'Toggle distraction-free full editor canvas' },
        { title: 'Global Search', keys: ['⌘', 'K'], description: 'Open hybrid vector & text search' },
        { title: 'Settings View', keys: ['⌘', ','], description: 'Open dedicated full settings environment' },
        { title: 'Shortcuts Help', keys: ['⌘', '/'], description: 'Show keyboard shortcuts cheat sheet' },
        { title: 'Close / Back', keys: ['Esc'], description: 'Close active modal, exit focus, or return to notes' },
      ],
    },
  ];

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && setActiveModal(null)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-xl bg-card text-card-foreground border border-border rounded-xl shadow-2xl z-50 p-0 overflow-hidden flex flex-col animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="h-14 px-6 border-b border-border flex items-center justify-between bg-surface-sidebar select-none">
            <div className="flex items-center gap-2.5">
              <Keyboard className="w-5 h-5 text-foreground" />
              <div>
                <h3 className="text-sm font-bold leading-tight">Keyboard Shortcuts</h3>
                <p className="text-[10px] text-muted-foreground font-mono">
                  Quick key bindings for high-speed note management
                </p>
              </div>
            </div>

            <Dialog.Close asChild>
              <button className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors">
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
            {shortcuts.map((group) => (
              <div key={group.section} className="space-y-2.5">
                <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                  {group.section}
                </h4>
                <div className="divide-y divide-border/50 border border-border/70 rounded-xl bg-surface-hover/30 overflow-hidden">
                  {group.items.map((sc) => (
                    <div
                      key={sc.title}
                      className="px-4 py-2.5 flex items-center justify-between gap-4 text-xs"
                    >
                      <div>
                        <span className="font-semibold text-foreground block">{sc.title}</span>
                        <span className="text-[11px] text-muted-foreground">{sc.description}</span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        {sc.keys.map((k) => (
                          <kbd
                            key={k}
                            className="px-2 py-1 rounded bg-surface-selected border border-border font-mono text-[11px] font-bold shadow-2xs min-w-[24px] text-center"
                          >
                            {k}
                          </kbd>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
