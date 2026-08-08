import React, { useState, useEffect } from 'react';
import {
  Brain,
  Search,
  Plus,
  Bot,
  Database,
  Shield,
  Trash2,
  ExternalLink,
  RefreshCw,
  Folder,
  Tag,
  CheckCircle2,
  FileText,
  X,
  Send,
  Sparkles,
  Lock,
  Layers,
  Maximize2,
  Minimize2
} from 'lucide-react';
import {
  fetchMemories,
  fetchCategories,
  fetchMemoryDetail,
  createOrUpdateMemory,
  deleteMemory,
  searchMemories,
  getBackupStatus,
  triggerBackup,
  sendChatMessage,
  purgeAllData,
  syncMemories,
  fetchMemoryVersions,
  revertMemory,
} from './services/api';

function parseGitHubMarkdown(rawText) {
  if (!rawText) return '';

  let processed = rawText
    .replace(/^>\s*\[!NOTE\]\s*(.*)$/gim, '<div class="border-l-4 border-blue-500 bg-blue-950/30 text-blue-200 p-3 rounded-r-lg my-2.5 font-sans"><strong>ℹ️ NOTE:</strong> $1</div>')
    .replace(/^>\s*\[!TIP\]\s*(.*)$/gim, '<div class="border-l-4 border-emerald-500 bg-emerald-950/30 text-emerald-200 p-3 rounded-r-lg my-2.5 font-sans"><strong>💡 TIP:</strong> $1</div>')
    .replace(/^>\s*\[!IMPORTANT\]\s*(.*)$/gim, '<div class="border-l-4 border-purple-500 bg-purple-950/30 text-purple-200 p-3 rounded-r-lg my-2.5 font-sans"><strong>⚡ IMPORTANT:</strong> $1</div>')
    .replace(/^>\s*\[!WARNING\]\s*(.*)$/gim, '<div class="border-l-4 border-amber-500 bg-amber-950/30 text-amber-200 p-3 rounded-r-lg my-2.5 font-sans"><strong>⚠️ WARNING:</strong> $1</div>')
    .replace(/^>\s*\[!CAUTION\]\s*(.*)$/gim, '<div class="border-l-4 border-red-500 bg-red-950/30 text-red-200 p-3 rounded-r-lg my-2.5 font-sans"><strong>🚨 CAUTION:</strong> $1</div>');

  if (window.marked) {
    try {
      window.marked.setOptions({ gfm: true, breaks: true });
      return window.marked.parse(processed);
    } catch (e) {
      return processed;
    }
  }
  return processed;
}

export default function App() {

  const [memories, setMemories] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(null);
  const [showChatDrawer, setShowChatDrawer] = useState(false);
  const [showBackupModal, setShowBackupModal] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(true);
  const [docMode, setDocMode] = useState('read'); // 'read' | 'edit'



  // Form state
  const [formTitle, setFormTitle] = useState('');
  const [formCategory, setFormCategory] = useState('personal');
  const [formTags, setFormTags] = useState('');
  const [formContent, setFormContent] = useState('');
  const [editingId, setEditingId] = useState(null);

  // Chat state
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'assistant',
      text: 'Hello! I am your AI Memory Companion. Ask me anything about your saved personal memories, projects, achievements, or technical notes!',
      sources: []
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Backup & Sync state
  const [readmeText, setReadmeText] = useState('');
  const [syncing, setSyncing] = useState(false);

  const handleSyncFiles = async () => {
    setSyncing(true);
    try {
      const res = await syncMemories();
      await loadData();
      alert(`Files Synced Successfully! Total ${res.total_memories || 0} memories indexed (${res.added || 0} added, ${res.updated || 0} updated).`);
    } catch (err) {
      console.error(err);
      alert('Failed to sync markdown files.');
    } finally {
      setSyncing(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadData();
  }, [activeCategory]);

  const loadData = async () => {
    setLoading(true);
    try {
      const catRes = await fetchCategories();
      setCategories(catRes.categories || []);

      const memRes = await fetchMemories(
        activeCategory === 'all' ? null : activeCategory
      );
      setMemories(memRes.memories || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      loadData();
      return;
    }
    setLoading(true);
    try {
      const searchRes = await searchMemories(
        searchQuery,
        activeCategory === 'all' ? null : activeCategory
      );
      setMemories(searchRes.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Version history state
  const [docVersions, setDocVersions] = useState([]);

  const handleRevertVersion = async (versionNum = null) => {
    if (!showDetailModal) return;
    try {
      const res = await revertMemory(showDetailModal.id, versionNum);
      alert(`Memory reverted to version ${res.version_number || 'previous'}!`);
      const detailRes = await fetchMemoryDetail(showDetailModal.id);
      if (detailRes && detailRes.status === 'success') {
        const fullContent = detailRes.content || detailRes.raw_file_text;
        setShowDetailModal((prev) => ({
          ...prev,
          content: fullContent,
        }));
        setFormContent(fullContent);
      }
      const verRes = await fetchMemoryVersions(showDetailModal.id);
      setDocVersions(verRes.versions || []);
      loadData();
    } catch (err) {
      console.error(err);
      alert('Failed to revert memory version.');
    }
  };

  const handleOpenDocument = async (memory, initialMode = 'read') => {
    setIsFullScreen(true);
    setDocMode(initialMode);
    setEditingId(memory.id);
    setFormTitle(memory.title || '');
    setFormCategory(memory.category || 'personal');
    setFormTags(Array.isArray(memory.tags) ? memory.tags.join(', ') : '');
    setFormContent(memory.content || memory.snippet || '');
    setShowDetailModal(memory);
    setDocVersions([]);

    try {
      const detailRes = await fetchMemoryDetail(memory.id);
      if (detailRes && detailRes.status === 'success') {
        const fullContent = detailRes.content || detailRes.raw_file_text || memory.content || memory.snippet;
        setShowDetailModal((prev) => ({
          ...prev,
          content: fullContent,
          file_path: detailRes.file_path,
          content_hash: detailRes.content_hash,
        }));
        setFormContent(fullContent);
      }
      const verRes = await fetchMemoryVersions(memory.id);
      setDocVersions(verRes.versions || []);
    } catch (err) {
      console.error('Error fetching untruncated memory detail or versions:', err);
    }
  };

  const handleOpenCreate = () => {
    setIsFullScreen(true);
    setDocMode('edit');
    setEditingId(null);
    setFormTitle('');
    setFormCategory('personal');
    setFormTags('');
    setFormContent('');
    setShowCreateModal(true);
  };

  const handleSaveMemory = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!formTitle.trim() || !formContent.trim()) return;

    const tagsList = formTags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    try {
      await createOrUpdateMemory({
        title: formTitle,
        category: formCategory,
        tags: tagsList,
        content: formContent,
        action: editingId ? 'update' : 'auto',
        memory_id: editingId,
      });

      setShowCreateModal(false);
      setShowDetailModal((prev) => prev ? {
        ...prev,
        title: formTitle,
        category: formCategory,
        tags: tagsList,
        content: formContent
      } : null);

      setDocMode('read');
      loadData();
    } catch (err) {
      alert(err.message || 'Error saving memory');
    }
  };

  const handleDeleteMemory = async (memoryId) => {
    if (!confirm('Are you sure you want to delete this memory?')) return;
    try {
      await deleteMemory(memoryId);
      loadData();
    } catch (err) {
      alert(err.message || 'Error deleting memory');
    }
  };

  const handleOpenBackup = async () => {
    try {
      const res = await getBackupStatus();
      setReadmeText(res.readme_text || '');
      setShowBackupModal(true);
    } catch (err) {
      alert('Error fetching backup status');
    }
  };

  const handleTriggerBackup = async () => {
    try {
      await triggerBackup();
      const res = await getBackupStatus();
      setReadmeText(res.readme_text || '');
      alert('Backup snapshot created successfully!');
    } catch (err) {
      alert('Backup failed');
    }
  };

  const handlePurgingSystem = async () => {
    if (!confirm('CAUTION: This will purge all memories, vector DB chunks, and backup files. Continue?')) return;
    try {
      await purgeAllData();
      loadData();
      alert('System purged successfully.');
    } catch (err) {
      alert('Purge failed');
    }
  };

  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userText = chatInput;
    setChatInput('');
    setChatMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setChatLoading(true);

    try {
      const res = await sendChatMessage(userText);
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: res.reply || 'No response generated.',
          sources: res.memories_used || []
        }
      ]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { sender: 'assistant', text: 'Error connecting to memory AI service.' }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans">
      {/* HEADER BAR */}
      <header className="border-b border-zinc-800 bg-zinc-900/60 backdrop-blur sticky top-0 z-30 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-zinc-800 rounded-lg border border-zinc-700/50">
            <Brain className="w-5 h-5 text-zinc-100" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-zinc-100 tracking-tight text-base">Memorize</span>
              <span className="text-xs font-mono bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded border border-zinc-700/40">
                v1.0.0 MCP
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono">Personal Memory Engine & AI Friend Service</p>
          </div>
        </div>

        {/* Global Search Bar */}
        <form onSubmit={handleSearch} className="flex-1 max-w-md mx-8 relative">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search memories by keyword, text, or vector similarity..."
            value={searchQuery}
            onChange={(e) => {
              const val = e.target.value;
              setSearchQuery(val);
              if (!val.trim()) {
                loadData();
              }
            }}
            className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-9 pr-16 py-1.5 text-xs text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-zinc-600 transition"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                loadData();
              }}
              className="absolute right-12 top-1/2 -translate-y-1/2 text-[10px] text-zinc-500 hover:text-zinc-300 px-1"
              title="Clear search"
            >
              ✕
            </button>
          )}
          <button
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-mono text-zinc-400 bg-zinc-800 border border-zinc-700 px-1.5 py-0.5 rounded hover:text-zinc-200"
          >
            Search
          </button>
        </form>

        {/* Header Actions & Health Badges */}
        <div className="flex items-center gap-2.5">
          <div className="hidden lg:flex items-center gap-2 border-r border-zinc-800 pr-3 mr-1 text-xs font-mono text-zinc-400">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> SQLite DB
            </span>
            <span className="flex items-center gap-1">
              <Shield className="w-3.5 h-3.5 text-zinc-300" /> Rematerializer Active
            </span>
          </div>

          <button
            onClick={() => handleOpenCreate()}
            className="bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" /> New Memory
          </button>

          <button
            onClick={() => setShowChatDrawer(true)}
            className="bg-zinc-900 hover:bg-zinc-850 text-zinc-100 border border-zinc-800 text-xs font-medium px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition"
          >
            <Bot className="w-3.5 h-3.5 text-zinc-400" /> AI Friend
          </button>

          <button
            onClick={handleSyncFiles}
            disabled={syncing}
            className="bg-zinc-900 hover:bg-zinc-850 text-zinc-300 border border-zinc-800 text-xs font-medium px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 transition disabled:opacity-50"
            title="Scan and Sync Markdown Files from Disk to Database"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-zinc-400 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync Disk Files'}
          </button>

          <button
            onClick={handleOpenBackup}
            className="bg-zinc-900 hover:bg-zinc-850 text-zinc-300 border border-zinc-800 text-xs font-medium px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 transition"
            title="View Backups & README"
          >
            <Database className="w-3.5 h-3.5 text-zinc-400" /> Backup Index
          </button>
        </div>
      </header>

      {/* MAIN CONTAINER */}
      <div className="flex-1 flex overflow-hidden">
        {/* SIDEBAR */}
        <aside className="w-64 border-r border-zinc-800 bg-zinc-950 p-4 flex flex-col gap-6 overflow-y-auto">
          <div>
            <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 font-semibold mb-2.5 px-2">
              Categories
            </div>
            <nav className="flex flex-col gap-1">
              <button
                onClick={() => setActiveCategory('all')}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium flex items-center justify-between transition ${
                  activeCategory === 'all'
                    ? 'bg-zinc-800 text-zinc-100 border border-zinc-700/50'
                    : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
                }`}
              >
                <span className="flex items-center gap-2">
                  <Layers className="w-3.5 h-3.5" /> All Memories
                </span>
                <span className="font-mono text-[10px] bg-zinc-900 text-zinc-400 px-1.5 py-0.5 rounded border border-zinc-800">
                  {memories.length}
                </span>
              </button>

              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium capitalize flex items-center justify-between transition ${
                    activeCategory === cat
                      ? 'bg-zinc-800 text-zinc-100 border border-zinc-700/50'
                      : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <Folder className="w-3.5 h-3.5 text-zinc-400" /> {cat}
                  </span>
                </button>
              ))}
            </nav>
          </div>

          {/* System Control Block */}
          <div className="mt-auto border-t border-zinc-800/80 pt-4 px-2 flex flex-col gap-1.5">
            <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 font-semibold mb-1">
              System Control
            </div>
            <button
              onClick={handleSyncFiles}
              disabled={syncing}
              className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-zinc-300 hover:bg-zinc-900 border border-zinc-800/80 flex items-center gap-2 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-zinc-400 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing...' : 'Sync Disk Files'}
            </button>
            <button
              onClick={handlePurgingSystem}
              className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-red-400 hover:bg-red-950/30 hover:border-red-900/40 border border-transparent flex items-center gap-2 transition"
            >
              <Trash2 className="w-3.5 h-3.5" /> Purge Memory Store
            </button>
          </div>
        </aside>

        {/* CONTENT FEED */}
        <main className="flex-1 overflow-y-auto p-6 bg-zinc-950">
          <div className="max-w-6xl mx-auto flex flex-col gap-6">
            {/* Feed Header */}
            <div className="flex items-center justify-between pb-4 border-b border-zinc-800">
              <div>
                <h1 className="text-xl font-bold text-zinc-100 capitalize flex items-center gap-2">
                  {activeCategory === 'all' ? 'All Memories' : `${activeCategory} Category`}
                </h1>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Full content stored in SQLite database with automatic disk file re-materialization.
                </p>
              </div>
              <div className="text-xs font-mono text-zinc-400 bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-lg">
                {memories.length} items loaded
              </div>
            </div>

            {/* Empty State */}
            {!loading && memories.length === 0 && (
              <div className="border border-dashed border-zinc-800 rounded-xl p-12 text-center flex flex-col items-center justify-center my-8">
                <div className="p-3 bg-zinc-900 rounded-full border border-zinc-800 mb-3">
                  <Brain className="w-6 h-6 text-zinc-500" />
                </div>
                <h3 className="text-sm font-semibold text-zinc-200">No Memories Found</h3>
                <p className="text-xs text-zinc-500 max-w-sm mt-1 mb-4">
                  There are no stored memories matching this view. Add a new memory or use the AI Friend companion to import context!
                </p>
                <button
                  onClick={() => handleOpenCreate()}
                  className="bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 transition"
                >
                  <Plus className="w-3.5 h-3.5" /> Create First Memory
                </button>
              </div>
            )}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex items-center justify-center py-12 text-xs font-mono text-zinc-400 gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-zinc-400" /> Loading memories from SQLite & ChromaDB...
              </div>
            )}

            {/* Memories Grid */}
            {!loading && memories.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {memories.map((mem) => (
                  <div
                    key={mem.id}
                    className="bg-zinc-900/80 border border-zinc-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-zinc-700 transition group shadow-sm"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <span className="text-xs font-mono uppercase bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded border border-zinc-700/50">
                          {mem.category || 'personal'}
                        </span>
                        <span className="text-[10px] font-mono text-zinc-500">
                          {mem.id}
                        </span>
                      </div>

                      <h3 className="text-sm font-semibold text-zinc-100 tracking-tight group-hover:text-white transition line-clamp-1 mb-1.5">
                        {mem.title || 'Untitled Memory'}
                      </h3>

                      <p className="text-xs text-zinc-400 line-clamp-3 leading-relaxed mb-4">
                        {mem.snippet || mem.content || 'No content snippet available.'}
                      </p>
                    </div>

                    <div>
                      {/* Tags */}
                      {Array.isArray(mem.tags) && mem.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-3">
                          {mem.tags.slice(0, 3).map((t, idx) => (
                            <span key={idx} className="text-[10px] font-mono text-zinc-400 bg-zinc-950 px-1.5 py-0.5 rounded border border-zinc-800">
                              #{t}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Card Footer Controls */}
                      <div className="border-t border-neutral-800 pt-3 flex items-center justify-between text-xs">
                        <button
                          onClick={() => handleOpenDocument(mem, 'read')}
                          className="text-white hover:text-neutral-200 text-xs font-semibold flex items-center gap-1.5 bg-neutral-800 hover:bg-neutral-700 px-3 py-1.5 rounded-xl transition border border-neutral-700"
                        >
                          <FileText className="w-3.5 h-3.5 text-neutral-300" /> Open Document
                        </button>

                        <div className="flex items-center gap-2.5">
                          <button
                            onClick={() => handleOpenDocument(mem, 'edit')}
                            className="text-neutral-400 hover:text-white text-xs transition"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteMemory(mem.id)}
                            className="text-neutral-500 hover:text-red-400 text-xs transition"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>

      {/* CREATE / EDIT MODAL (Full-Width Editor & Optional GitHub Rendered Tab) */}
      {showCreateModal && (
        <div className={`fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center ${isFullScreen ? 'p-0' : 'p-4'}`}>
          <div className={`bg-neutral-900 border border-neutral-800 shadow-2xl flex flex-col gap-4 transition-all duration-200 ${
            isFullScreen
              ? 'w-screen h-screen rounded-none p-6 bg-black flex flex-col justify-between'
              : 'max-w-4xl w-full p-6 rounded-2xl max-h-[90vh] overflow-y-auto'
          }`}>
            <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-white" />
                <h2 className="text-base font-bold text-white tracking-tight">
                  {editingId ? 'Edit Memory Document' : 'Create Memory Document'}
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsFullScreen(!isFullScreen)}
                  className="p-1.5 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition"
                  title={isFullScreen ? "Exit Fullscreen" : "Fullscreen Mode"}
                >
                  {isFullScreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                </button>
                <button onClick={() => { setShowCreateModal(false); setIsFullScreen(false); }} className="p-1.5 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <form onSubmit={handleSaveMemory} className={`flex flex-col gap-4 text-xs ${isFullScreen ? 'flex-1 min-h-0' : ''}`}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="md:col-span-1">
                  <label className="block font-mono text-neutral-400 mb-1">Title</label>
                  <input
                    type="text"
                    required
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    placeholder="Memory title or topic..."
                    className="w-full bg-black border border-neutral-800 rounded-xl p-2.5 text-white placeholder:text-neutral-600 focus:outline-none focus:border-neutral-600 font-medium"
                  />
                </div>

                <div>
                  <label className="block font-mono text-neutral-400 mb-1">Category</label>
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full bg-black border border-neutral-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-neutral-600 capitalize font-medium"
                  >
                    {['personal', 'development', 'projects', 'achievements', 'education', 'job', 'integration', 'media', 'finance', 'gaming', 'others'].map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-mono text-neutral-400 mb-1">Tags (Comma separated)</label>
                  <input
                    type="text"
                    value={formTags}
                    onChange={(e) => setFormTags(e.target.value)}
                    placeholder="react, python, routine"
                    className="w-full bg-black border border-neutral-800 rounded-xl p-2.5 text-white placeholder:text-neutral-600 focus:outline-none focus:border-neutral-600 font-medium"
                  />
                </div>
              </div>

              {/* Full-Width Markdown Editor Container */}
              <div className={`border border-neutral-800 rounded-2xl bg-black overflow-hidden flex flex-col ${isFullScreen ? 'flex-1 min-h-0' : ''}`}>
                <div className="bg-neutral-900 px-4 py-2.5 border-b border-neutral-800 flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-mono text-xs">
                    <span className="text-neutral-400 font-semibold mr-2">Tools:</span>
                    <button
                      type="button"
                      onClick={() => setFormContent((prev) => prev + '\n### ')}
                      className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700 font-mono"
                    >
                      H3
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormContent((prev) => prev + ' **bold** ')}
                      className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700 font-bold"
                    >
                      B
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormContent((prev) => prev + ' *italic* ')}
                      className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700 italic"
                    >
                      I
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormContent((prev) => prev + '\n```python\n# Code snippet\n```\n')}
                      className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700 font-mono"
                    >
                      Code
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormContent((prev) => prev + '\n- Item 1\n- Item 2\n')}
                      className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700"
                    >
                      List
                    </button>
                    <button
                      type="button"
                      onClick={() => setFormContent((prev) => prev + '\n> Blockquote text...\n')}
                      className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700"
                    >
                      Quote
                    </button>
                  </div>
                  <span className="text-[11px] font-mono text-neutral-500">Full-Width Markdown Textarea</span>
                </div>

                {/* Full Width Textarea without side preview */}
                <div className={`p-4 flex flex-col ${isFullScreen ? 'flex-1 min-h-0' : 'min-h-[320px]'}`}>
                  <textarea
                    required
                    value={formContent}
                    onChange={(e) => setFormContent(e.target.value)}
                    placeholder="# Enter Full Markdown Document..."
                    className="w-full flex-1 h-full bg-transparent text-white font-mono text-xs focus:outline-none resize-none leading-relaxed p-1"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-neutral-800">
                <button
                  type="button"
                  onClick={() => { setShowCreateModal(false); setIsFullScreen(false); }}
                  className="px-4 py-2 bg-neutral-800 text-neutral-300 rounded-xl hover:bg-neutral-700 font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-white text-black font-semibold rounded-xl hover:bg-neutral-200 transition shadow"
                >
                  Save Memory
                </button>
              </div>
            </form>
          </div>
        </div>
      )}


      {/* UNIFIED FULL-SCREEN MEMORY DOCUMENT WINDOW (WITH IN-WINDOW READ/EDIT MODE TOGGLER) */}
      {showDetailModal && (
        <div className={`fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center ${isFullScreen ? 'p-0' : 'p-4'}`}>
          <div className={`bg-neutral-900 border border-neutral-800 shadow-2xl flex flex-col gap-4 transition-all duration-200 ${
            isFullScreen
              ? 'w-screen h-screen rounded-none p-6 bg-black flex flex-col justify-between'
              : 'max-w-5xl w-full p-6 rounded-2xl max-h-[90vh] overflow-y-auto'
          }`}>
            {/* Window Header with Mode Toggler */}
            <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-mono uppercase bg-neutral-800 text-neutral-200 px-2.5 py-1 rounded-md border border-neutral-700 font-semibold">
                  {showDetailModal.category}
                </span>
                <h2 className="text-base font-bold text-white tracking-tight">
                  {showDetailModal.title}
                </h2>
              </div>

              <div className="flex items-center gap-3">
                {/* Segmented Mode Toggler Control */}
                <div className="bg-black p-1 rounded-xl border border-neutral-800 flex items-center gap-1 font-mono text-xs">
                  <button
                    type="button"
                    onClick={() => setDocMode('read')}
                    className={`px-3 py-1 rounded-lg flex items-center gap-1.5 transition font-semibold ${
                      docMode === 'read'
                        ? 'bg-neutral-800 text-white shadow border border-neutral-700'
                        : 'text-neutral-400 hover:text-white'
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5" /> Read
                  </button>
                  <button
                    type="button"
                    onClick={() => setDocMode('edit')}
                    className={`px-3 py-1 rounded-lg flex items-center gap-1.5 transition font-semibold ${
                      docMode === 'edit'
                        ? 'bg-white text-black shadow font-bold'
                        : 'text-neutral-400 hover:text-white'
                    }`}
                  >
                    ✏️ Edit
                  </button>
                </div>

                {/* Version Control / Revert Dropdown */}
                {docVersions.length > 0 && (
                  <div className="flex items-center gap-1.5 font-mono text-xs bg-black px-2 py-1 rounded-xl border border-neutral-800">
                    <span className="text-neutral-400 font-semibold text-[11px]">vHistory:</span>
                    <select
                      onChange={(e) => {
                        if (e.target.value) {
                          if (confirm(`Revert this memory to version ${e.target.value}?`)) {
                            handleRevertVersion(parseInt(e.target.value));
                          }
                          e.target.value = '';
                        }
                      }}
                      defaultValue=""
                      className="bg-neutral-900 border border-neutral-700 text-neutral-200 rounded px-1.5 py-0.5 text-[11px] font-mono focus:outline-none"
                    >
                      <option value="" disabled>Restore version...</option>
                      {docVersions.map((ver) => (
                        <option key={ver.version_number} value={ver.version_number}>
                          v{ver.version_number} ({new Date(ver.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setIsFullScreen(!isFullScreen)}
                    className="p-1.5 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition"
                    title={isFullScreen ? "Exit Fullscreen" : "Fullscreen Mode"}
                  >
                    {isFullScreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                  </button>
                  <button onClick={() => { setShowDetailModal(null); setIsFullScreen(false); }} className="p-1.5 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Window Content Body */}
            {docMode === 'read' ? (
              /* READ MODE: GitHub Flavored Markdown Content Container */
              <div className={`bg-black border border-neutral-800 rounded-2xl shadow-inner flex flex-col ${isFullScreen ? 'flex-1 overflow-y-auto p-8' : 'p-6'}`}>
                <div className="text-xs font-mono text-neutral-400 uppercase tracking-wider mb-4 pb-2 border-b border-neutral-800 flex items-center justify-between">
                  <span className="flex items-center gap-2 font-semibold">
                    <FileText className="w-3.5 h-3.5 text-white" /> GitHub Markdown Viewer
                  </span>
                  <button
                    onClick={() => setDocMode('edit')}
                    className="text-xs bg-neutral-800 hover:bg-neutral-700 text-neutral-200 px-3 py-1 rounded-lg border border-neutral-700 transition flex items-center gap-1"
                  >
                    ✏️ Edit This Document
                  </button>
                </div>

                <div
                  className="text-xs text-neutral-200 leading-relaxed font-sans space-y-3 flex-1"
                  dangerouslySetInnerHTML={{
                    __html: parseGitHubMarkdown(showDetailModal.content || showDetailModal.snippet || formContent || 'No text content available.')
                  }}
                />
              </div>
            ) : (
              /* EDIT MODE: Full-Width Markdown Form Editor */
              <form onSubmit={handleSaveMemory} className={`flex flex-col gap-4 text-xs ${isFullScreen ? 'flex-1 min-h-0' : ''}`}>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="md:col-span-1">
                    <label className="block font-mono text-neutral-400 mb-1">Title</label>
                    <input
                      type="text"
                      required
                      value={formTitle}
                      onChange={(e) => setFormTitle(e.target.value)}
                      placeholder="Memory title or topic..."
                      className="w-full bg-black border border-neutral-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-neutral-600 font-medium"
                    />
                  </div>

                  <div>
                    <label className="block font-mono text-neutral-400 mb-1">Category</label>
                    <select
                      value={formCategory}
                      onChange={(e) => setFormCategory(e.target.value)}
                      className="w-full bg-black border border-neutral-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-neutral-600 capitalize font-medium"
                    >
                      {['personal', 'development', 'projects', 'achievements', 'education', 'job', 'integration', 'media', 'finance', 'gaming', 'others'].map((cat) => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block font-mono text-neutral-400 mb-1">Tags (Comma separated)</label>
                    <input
                      type="text"
                      value={formTags}
                      onChange={(e) => setFormTags(e.target.value)}
                      placeholder="react, python, routine"
                      className="w-full bg-black border border-neutral-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-neutral-600 font-medium"
                    />
                  </div>
                </div>

                <div className={`border border-neutral-800 rounded-2xl bg-black overflow-hidden flex flex-col ${isFullScreen ? 'flex-1 min-h-0' : ''}`}>
                  <div className="bg-neutral-900 px-4 py-2.5 border-b border-neutral-800 flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-mono text-xs">
                      <span className="text-neutral-400 font-semibold mr-2">Tools:</span>
                      <button
                        type="button"
                        onClick={() => setFormContent((prev) => prev + '\n### ')}
                        className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700 font-mono"
                      >
                        H3
                      </button>
                      <button
                        type="button"
                        onClick={() => setFormContent((prev) => prev + ' **bold** ')}
                        className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700 font-bold"
                      >
                        B
                      </button>
                      <button
                        type="button"
                        onClick={() => setFormContent((prev) => prev + ' *italic* ')}
                        className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700 italic"
                      >
                        I
                      </button>
                      <button
                        type="button"
                        onClick={() => setFormContent((prev) => prev + '\n```python\n# Code snippet\n```\n')}
                        className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700 font-mono"
                      >
                        Code
                      </button>
                      <button
                        type="button"
                        onClick={() => setFormContent((prev) => prev + '\n- Item 1\n- Item 2\n')}
                        className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700"
                      >
                        List
                      </button>
                      <button
                        type="button"
                        onClick={() => setFormContent((prev) => prev + '\n> Blockquote text...\n')}
                        className="px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700"
                      >
                        Quote
                      </button>
                    </div>
                  </div>

                  <div className={`p-4 flex flex-col ${isFullScreen ? 'flex-1 min-h-0' : 'min-h-[300px]'}`}>
                    <textarea
                      required
                      value={formContent}
                      onChange={(e) => setFormContent(e.target.value)}
                      placeholder="# Enter Full Markdown Document..."
                      className="w-full flex-1 h-full bg-transparent text-white font-mono text-xs focus:outline-none resize-none leading-relaxed p-1"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-neutral-800">
                  <button
                    type="button"
                    onClick={() => setDocMode('read')}
                    className="px-4 py-2 bg-neutral-800 text-neutral-300 rounded-xl hover:bg-neutral-700 font-medium transition"
                  >
                    Cancel Editing
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 bg-white text-black font-semibold rounded-xl hover:bg-neutral-200 transition shadow"
                  >
                    💾 Save Memory Changes
                  </button>
                </div>
              </form>
            )}

            <div className="text-[11px] font-mono text-neutral-500 flex flex-col gap-1 border-t border-neutral-800 pt-3">
              <div>File Path: <span className="text-neutral-300">{showDetailModal.file_path || 'Stored in SQLite'}</span></div>
              <div>Memory ID: <span className="text-neutral-300">{showDetailModal.id}</span></div>
              <div>Content Hash: <span className="text-neutral-300">{showDetailModal.content_hash || 'N/A'}</span></div>
            </div>
          </div>
        </div>
      )}




      {/* AI COMPANION CHAT DRAWER */}
      {showChatDrawer && (
        <div className="fixed inset-y-0 right-0 w-96 bg-zinc-900 border-l border-zinc-800 z-50 flex flex-col shadow-2xl">
          <div className="p-4 border-b border-zinc-800 flex items-center justify-between bg-zinc-950">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-zinc-300" />
              <span className="font-semibold text-xs text-zinc-100">AI Memory Friend</span>
            </div>
            <button onClick={() => setShowChatDrawer(false)} className="text-zinc-400 hover:text-zinc-200">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3 text-xs">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`p-3 rounded-xl max-w-[85%] ${
                  msg.sender === 'user'
                    ? 'bg-zinc-800 text-zinc-100 ml-auto border border-zinc-700/50'
                    : 'bg-zinc-950 text-zinc-300 border border-zinc-800 mr-auto'
                }`}
              >
                <div className="leading-relaxed whitespace-pre-wrap">{msg.text}</div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-zinc-800/80 text-[10px] font-mono text-zinc-500 flex flex-col gap-0.5">
                    <span className="text-zinc-400">Sources retrieved:</span>
                    {msg.sources.map((s, idx) => (
                      <span key={idx}>• {s.title} ({s.category})</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {chatLoading && (
              <div className="text-[11px] font-mono text-zinc-500 flex items-center gap-2 p-2">
                <Sparkles className="w-3.5 h-3.5 animate-spin text-zinc-400" /> Searching memories...
              </div>
            )}
          </div>

          <form onSubmit={handleSendChat} className="p-3 border-t border-zinc-800 bg-zinc-950 flex gap-2">
            <input
              type="text"
              placeholder="Ask your AI friend..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:outline-none focus:border-zinc-700"
            />
            <button
              type="submit"
              disabled={chatLoading}
              className="bg-zinc-100 hover:bg-white text-zinc-950 px-3 py-1.5 rounded-lg text-xs font-semibold"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      )}

      {/* BACKUP & README INDEX MODAL */}
      {showBackupModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl max-w-3xl w-full p-6 shadow-2xl flex flex-col gap-4 max-h-[85vh]">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-zinc-300" />
                <h2 className="text-base font-bold text-zinc-100">Backup Repository & README Index</h2>
              </div>
              <button onClick={() => setShowBackupModal(false)} className="text-zinc-400 hover:text-zinc-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <p className="text-xs text-zinc-400">
                SQLite database snapshot copy maintained at <code className="font-mono text-zinc-200">data/backups/memorize_backup.db</code>
              </p>
              <button
                onClick={handleTriggerBackup}
                className="bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-xs px-3 py-1.5 rounded-lg font-mono flex items-center gap-1.5 border border-zinc-700"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Create Snapshot Backup
              </button>
            </div>

            <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 font-mono text-xs text-zinc-300 overflow-y-auto flex-1 whitespace-pre">
              {readmeText || 'No backup README snapshot available.'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
