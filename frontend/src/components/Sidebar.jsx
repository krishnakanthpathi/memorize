import React from 'react';
import { Search, Folder, Tag, Layers, X, CheckSquare, Square } from 'lucide-react';

export default function Sidebar({
  categories,
  selectedCategories,
  setSelectedCategories,
  allTags,
  selectedTags,
  setSelectedTags,
  searchQuery,
  setSearchQuery,
  totalNotesCount,
}) {
  const toggleCategory = (catId) => {
    if (catId === 'all') {
      setSelectedCategories([]);
      return;
    }
    if (selectedCategories.includes(catId)) {
      setSelectedCategories(selectedCategories.filter((c) => c !== catId));
    } else {
      setSelectedCategories([...selectedCategories, catId]);
    }
  };

  const toggleTag = (tag) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter((t) => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const hasActiveFilters =
    selectedCategories.length > 0 || selectedTags.length > 0 || searchQuery.trim() !== '';

  return (
    <aside className="d-flex flex-column h-100 bg-mono-surface border-end border-mono p-3 overflow-auto">
      
      {/* Search Bar with Auto-Suggestions */}
      <div className="mb-3 position-relative">
        <div className="input-group input-group-sm">
          <span className="input-group-text bg-dark border-mono text-secondary px-2-5">
            <Search size={14} />
          </span>
          <input
            type="text"
            className="form-control form-control-mono"
            placeholder="Search notes or tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button
              className="btn btn-mono-outline btn-sm text-secondary px-2"
              onClick={() => setSearchQuery('')}
            >
              <X size={13} />
            </button>
          )}
        </div>

        {/* Auto-Suggestion Dropdown */}
        {searchQuery.trim().length > 0 && (
          <div className="position-absolute start-0 end-0 top-100 mt-1 bg-mono-surface border border-mono rounded shadow-lg p-2 z-3 font-mono fs-8">
            <small className="text-uppercase text-secondary fs-8 opacity-75 d-block mb-1.5 px-1">
              Search Auto-Suggestions
            </small>
            <div className="d-flex flex-column gap-1">
              {allTags
                .filter((t) => t.toLowerCase().includes(searchQuery.toLowerCase()) && t.toLowerCase() !== searchQuery.toLowerCase())
                .slice(0, 3)
                .map((t) => (
                  <button
                    key={`sug_tag_${t}`}
                    className="btn btn-sm btn-mono-outline text-start py-1 px-2 font-mono fs-8 text-light d-flex align-items-center justify-content-between"
                    onClick={() => setSearchQuery(t)}
                  >
                    <span>Tag: #{t}</span>
                    <small className="text-secondary fs-8">Filter</small>
                  </button>
                ))}
              {categories
                .filter((c) => c.id !== 'all' && c.name.toLowerCase().includes(searchQuery.toLowerCase()))
                .slice(0, 2)
                .map((c) => (
                  <button
                    key={`sug_cat_${c.id}`}
                    className="btn btn-sm btn-mono-outline text-start py-1 px-2 font-mono fs-8 text-light d-flex align-items-center justify-content-between"
                    onClick={() => setSearchQuery(c.name)}
                  >
                    <span>Category: {c.name}</span>
                    <small className="text-secondary fs-8">Category</small>
                  </button>
                ))}
              {['pruning', 'graphrag', 'sqlite', 'chromadb', 'sync', 'vector', 'models', 'architecture']
                .filter((k) => k.includes(searchQuery.toLowerCase()) && k !== searchQuery.toLowerCase())
                .slice(0, 3)
                .map((k) => (
                  <button
                    key={`sug_key_${k}`}
                    className="btn btn-sm btn-mono-outline text-start py-1 px-2 font-mono fs-8 text-light d-flex align-items-center justify-content-between"
                    onClick={() => setSearchQuery(k)}
                  >
                    <span>Keyword: {k}</span>
                    <small className="text-secondary fs-8">Keyword</small>
                  </button>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* Category Multi-Select Navigation */}
      <div className="mb-4">
        <div className="d-flex align-items-center justify-content-between mb-2">
          <small className="text-uppercase text-secondary font-mono fs-8 fw-semibold d-flex align-items-center gap-2">
            <Folder size={13} />
            <span>Categories</span>
          </small>
        </div>

        <div className="list-group list-group-flush border-0">
          
          {/* All Notes Reset item */}
          <button
            className={`list-group-item list-group-item-action bg-transparent border-0 rounded-1 py-1.5 px-2 mb-1 d-flex align-items-center justify-content-between text-sm ${
              selectedCategories.length === 0 ? 'btn-mono-active text-white' : 'text-secondary hover-white'
            }`}
            onClick={() => setSelectedCategories([])}
          >
            <span className="d-flex align-items-center gap-2.5 fs-8">
              <Layers size={14} />
              <span>All Categories</span>
            </span>
            <span className="badge bg-mono-dark border border-mono-muted text-secondary font-mono fs-8">
              {totalNotesCount}
            </span>
          </button>

          {/* Individual Category Checklist */}
          {categories.filter(c => c.id !== 'all').map((cat) => {
            const isChecked = selectedCategories.includes(cat.id);
            return (
              <button
                key={cat.id}
                className={`list-group-item list-group-item-action bg-transparent border-0 rounded-1 py-1.5 px-2 mb-1 d-flex align-items-center justify-content-between text-sm ${
                  isChecked ? 'btn-mono-active text-white fw-medium' : 'text-secondary hover-white'
                }`}
                onClick={() => toggleCategory(cat.id)}
              >
                <span className="d-flex align-items-center gap-2.5 fs-8 text-capitalize">
                  {isChecked ? <CheckSquare size={14} /> : <Square size={14} />}
                  <span>{cat.name}</span>
                </span>
                <span className="badge bg-mono-dark border border-mono-muted text-secondary font-mono fs-8">
                  {cat.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Multi-Select Tag Cloud */}
      <div className="mb-3">
        <small className="text-uppercase text-secondary font-mono fs-8 fw-semibold d-flex align-items-center gap-2 mb-2">
          <Tag size={13} />
          <span>Tags</span>
        </small>

        <div className="d-flex flex-wrap gap-1.5">
          {allTags.map((tag) => {
            const isSelected = selectedTags.includes(tag);
            return (
              <button
                key={tag}
                className={`btn btn-sm py-1 px-2.5 rounded-pill font-mono fs-8 ${
                  isSelected ? 'badge-mono-active' : 'badge-mono hover-white'
                }`}
                onClick={() => toggleTag(tag)}
              >
                #{tag}
              </button>
            );
          })}
        </div>
      </div>

      {/* Clear All Multi-Select Filters */}
      {hasActiveFilters && (
        <div className="mt-auto pt-2 border-top border-mono-muted">
          <button
            className="btn btn-mono-outline btn-sm w-100 fs-8 text-secondary d-flex align-items-center justify-content-center gap-2"
            onClick={() => {
              setSelectedCategories([]);
              setSelectedTags([]);
              setSearchQuery('');
            }}
          >
            <X size={13} />
            <span>Reset All Filters</span>
          </button>
        </div>
      )}

    </aside>
  );
}
