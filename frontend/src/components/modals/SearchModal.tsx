import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Sparkles,
  X,
  Folder,
  ArrowRight,
  Loader2,
  SlidersHorizontal,
} from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { useNotesStore } from '@/store/useNotesStore';
import { api } from '@/services/api';
import { SearchResult } from '@/types';
import { cn, cleanMarkdownSnippet } from '@/lib/utils';

export const SearchModal: React.FC = () => {
  const {
    activeModal,
    setActiveModal,
    categories,
    selectNote,
  } = useNotesStore();

  const isOpen = activeModal === 'search';
  const [query, setQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 50);
    } else {
      setQuery('');
      setResults([]);
      setHasSearched(false);
    }
  }, [isOpen]);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setHasSearched(true);
    try {
      const data = await api.searchMemories(query.trim(), categoryFilter || undefined, 10);
      setResults(data);
    } catch (err) {
      console.error('Hybrid search error:', err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectResult = (id: string) => {
    selectNote(id);
    setActiveModal(null);
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && setActiveModal(null)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 animate-in fade-in" />
        <Dialog.Content className="fixed top-[15%] left-1/2 -translate-x-1/2 w-full max-w-2xl bg-card text-card-foreground border border-border rounded-xl shadow-2xl z-50 p-0 overflow-hidden animate-in fade-in zoom-in-95">
          {/* Header Bar */}
          <form onSubmit={handleSearch} className="p-4 border-b border-border flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-foreground shrink-0" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Deep Hybrid Semantic Search (e.g. 'Project notes on machine learning')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 bg-transparent text-sm border-none outline-none focus:ring-0 placeholder:text-muted-foreground/60 text-foreground"
            />
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            ) : (
              <button
                type="submit"
                className="px-3 py-1 bg-foreground text-background text-xs font-semibold rounded-md hover:opacity-90 transition-opacity"
              >
                Search
              </button>
            )}
            <Dialog.Close asChild>
              <button className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover">
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </form>

          {/* Category Filter Chips */}
          <div className="px-4 py-2 bg-surface-hover/50 border-b border-border/60 flex items-center gap-2 overflow-x-auto text-xs">
            <span className="text-[11px] text-muted-foreground shrink-0 font-medium">
              Category:
            </span>
            <button
              onClick={() => {
                setCategoryFilter('');
                if (query.trim()) handleSearch();
              }}
              className={cn(
                'px-2 py-0.5 rounded text-[11px] font-mono transition-colors shrink-0',
                categoryFilter === ''
                  ? 'bg-foreground text-background font-semibold'
                  : 'bg-muted text-muted-foreground hover:text-foreground'
              )}
            >
              All
            </button>
            {categories.map((c) => (
              <button
                key={c.category}
                onClick={() => {
                  setCategoryFilter(c.category);
                  if (query.trim()) handleSearch();
                }}
                className={cn(
                  'px-2 py-0.5 rounded text-[11px] font-mono transition-colors capitalize shrink-0',
                  categoryFilter === c.category
                    ? 'bg-foreground text-background font-semibold'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                )}
              >
                {c.category}
              </button>
            ))}
          </div>

          {/* Results List */}
          <div className="max-h-[380px] overflow-y-auto p-3 divide-y divide-border/40">
            {loading ? (
              <div className="py-12 flex flex-col items-center justify-center text-center text-muted-foreground">
                <Loader2 className="w-6 h-6 animate-spin mb-2" />
                <p className="text-xs">Computing hybrid vector & BM25 relevance scores...</p>
              </div>
            ) : results.length > 0 ? (
              results.map((res) => {
                const score = res.final_score !== undefined ? Math.round(res.final_score * 100) : (res.score !== undefined ? Math.round(res.score * 100) : null);
                return (
                  <div
                    key={res.id}
                    onClick={() => handleSelectResult(res.id)}
                    className="p-3 rounded-lg hover:bg-surface-hover cursor-pointer transition-colors group flex items-start justify-between gap-3"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-foreground group-hover:underline truncate">
                          {res.title || 'Untitled Note'}
                        </span>
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-muted text-muted-foreground capitalize">
                          {res.category}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {cleanMarkdownSnippet(res.snippet || res.content || '') || (
                          <span className="italic opacity-60">No preview text</span>
                        )}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      {score !== null && (
                        <div className="text-right">
                          <span className="text-[11px] font-mono font-bold text-foreground">
                            {score}% match
                          </span>
                          <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden mt-1">
                            <div
                              className="h-full bg-foreground rounded-full"
                              style={{ width: `${Math.min(score, 100)}%` }}
                            />
                          </div>
                        </div>
                      )}
                      <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-foreground group-hover:translate-x-0.5 transition-all" />
                    </div>
                  </div>
                );
              })
            ) : hasSearched ? (
              <div className="py-12 text-center text-muted-foreground">
                <Search className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p className="text-xs font-medium">No matching memories found</p>
                <p className="text-[11px] opacity-70 mt-0.5">
                  Try searching with different keywords or clearing the category filter.
                </p>
              </div>
            ) : (
              <div className="py-10 text-center text-muted-foreground">
                <p className="text-xs">
                  Type any topic, concept, or query to retrieve memories across semantic vectors and keywords.
                </p>
              </div>
            )}
          </div>

          {/* Footer Shortcuts */}
          <div className="p-3 bg-surface-sidebar border-t border-border flex items-center justify-between text-[11px] text-muted-foreground font-mono">
            <span>Powered by ChromaDB Vector & Hybrid Scorer</span>
            <div className="flex items-center gap-2">
              <span>Navigate: ↵</span>
              <span>•</span>
              <span>Close: ESC</span>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
