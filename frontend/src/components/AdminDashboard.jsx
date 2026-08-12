import React, { useState, useEffect } from 'react';
import { Sliders, Activity, ShieldCheck, Cpu, Package, RefreshCw, CheckCircle2, Settings, MessageSquareCode, RotateCcw, Save } from 'lucide-react';
import { fetchAudit, triggerBackup, setActiveModelApi, fetchPrompts, savePromptsApi, resetPromptsApi } from '../services/api';

export default function AdminDashboard({
  modelsData,
  activeModel,
  setActiveModel,
  activeEngine,
  setActiveEngine,
  auditData,
  metrics,
  onTriggerBackup,
}) {
  const [activeTab, setActiveTab] = useState('models'); // 'models' | 'prompts' | 'audit' | 'telemetry'

  const [auditResult, setAuditResult] = useState(auditData);
  const [isAuditing, setIsAuditing] = useState(false);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [backupMsg, setBackupMsg] = useState('');

  // Prompts State
  const [prompts, setPrompts] = useState({
    auto_suggest: '',
    auto_organize: '',
    smart_merge: '',
    graph_chat: '',
  });
  const [isSavingPrompts, setIsSavingPrompts] = useState(false);
  const [promptMsg, setPromptMsg] = useState('');

  useEffect(() => {
    if (auditData) setAuditResult(auditData);
  }, [auditData]);

  // Load prompts from backend API
  useEffect(() => {
    async function loadPromptsData() {
      const res = await fetchPrompts();
      if (res && res.prompts) {
        setPrompts(res.prompts);
      }
    }
    loadPromptsData();
  }, []);

  const handleAuditClick = async () => {
    setIsAuditing(true);
    try {
      const res = await fetchAudit(true, false);
      setAuditResult(res);
    } catch (err) {
      console.warn('Audit error:', err);
    } finally {
      setIsAuditing(false);
    }
  };

  const handleBackupClick = async () => {
    setIsBackingUp(true);
    setBackupMsg('');
    try {
      const res = await triggerBackup();
      if (onTriggerBackup) onTriggerBackup();
      setBackupMsg(res.message || 'Backup snapshot created successfully!');
    } catch (err) {
      console.warn('Backup error:', err);
    } finally {
      setIsBackingUp(false);
    }
  };

  const handleModelSelect = async (newModel) => {
    setActiveModel(newModel);
    await setActiveModelApi(newModel);
  };

  const handleSavePrompts = async () => {
    setIsSavingPrompts(true);
    setPromptMsg('');
    try {
      const res = await savePromptsApi(prompts);
      if (res.status === 'success') {
        if (res.prompts) setPrompts(res.prompts);
        setPromptMsg('Prompts successfully updated!');
      }
    } catch (err) {
      console.warn('Error saving prompts:', err);
    } finally {
      setIsSavingPrompts(false);
    }
  };

  const handleResetPrompts = async () => {
    setIsSavingPrompts(true);
    setPromptMsg('');
    try {
      const res = await resetPromptsApi();
      if (res.prompts) setPrompts(res.prompts);
      setPromptMsg('Prompts reset to factory defaults.');
    } catch (err) {
      console.warn('Error resetting prompts:', err);
    } finally {
      setIsSavingPrompts(false);
    }
  };

  return (
    <div className="d-flex flex-column h-100 bg-mono-dark p-4 overflow-auto">
      
      {/* Dashboard & Settings Header */}
      <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom border-mono flex-shrink-0">
        <div>
          <h2 className="h5 font-weight-bold mb-1 text-white d-flex align-items-center gap-2">
            <Settings size={20} />
            <span>Admin & Engine Workspace</span>
          </h2>
          <p className="text-secondary fs-8 font-mono mb-0">
            Configure LLM models, customize backend AI system prompts, run 3-way storage audits, and view system metrics.
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="d-flex align-items-center gap-2 mb-4 border-bottom border-mono pb-2 flex-shrink-0">
        <button
          className={`btn btn-sm font-mono fs-8 d-flex align-items-center gap-2 py-1.5 px-3 ${
            activeTab === 'models' ? 'btn-mono-primary' : 'btn-mono-outline text-secondary'
          }`}
          onClick={() => setActiveTab('models')}
        >
          <Cpu size={14} />
          <span>LLM Models & Framework</span>
        </button>

        <button
          className={`btn btn-sm font-mono fs-8 d-flex align-items-center gap-2 py-1.5 px-3 ${
            activeTab === 'prompts' ? 'btn-mono-primary' : 'btn-mono-outline text-secondary'
          }`}
          onClick={() => setActiveTab('prompts')}
        >
          <MessageSquareCode size={14} />
          <span>System Prompts Tuning</span>
        </button>

        <button
          className={`btn btn-sm font-mono fs-8 d-flex align-items-center gap-2 py-1.5 px-3 ${
            activeTab === 'audit' ? 'btn-mono-primary' : 'btn-mono-outline text-secondary'
          }`}
          onClick={() => setActiveTab('audit')}
        >
          <ShieldCheck size={14} />
          <span>Storage Audit & Backups</span>
        </button>

        <button
          className={`btn btn-sm font-mono fs-8 d-flex align-items-center gap-2 py-1.5 px-3 ${
            activeTab === 'telemetry' ? 'btn-mono-primary' : 'btn-mono-outline text-secondary'
          }`}
          onClick={() => setActiveTab('telemetry')}
        >
          <Activity size={14} />
          <span>Telemetry & Metrics</span>
        </button>
      </div>

      {/* Tab 1: Models & Framework Configuration */}
      {activeTab === 'models' && (
        <div className="card card-mono p-4">
          <div className="d-flex align-items-center justify-content-between mb-3 border-bottom border-mono-muted pb-2">
            <h3 className="h6 mb-0 text-light d-flex align-items-center gap-2">
              <Cpu size={16} />
              <span>Primary LLM & Model Engine Configuration</span>
            </h3>
            <span className="badge bg-mono-dark border border-mono text-white font-mono fs-8">
              Active: {activeModel}
            </span>
          </div>

          {/* Model Selector */}
          <div className="mb-4">
            <label className="form-label font-mono fs-8 text-secondary fw-medium">
              Active Generative LLM Model (Ollama & External APIs):
            </label>
            <select
              className="form-select form-select-mono mb-2"
              value={activeModel}
              onChange={(e) => handleModelSelect(e.target.value)}
            >
              {modelsData?.generative_models?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name || m.id} [{(m.provider || 'ollama').toUpperCase()}]
                </option>
              ))}
              {!modelsData?.generative_models?.some((m) => m.id === activeModel) && (
                <option value={activeModel}>{activeModel} [CUSTOM / OLLAMA]</option>
              )}
            </select>

            <div className="input-group input-group-sm mt-2">
              <span className="input-group-text bg-mono-dark border-mono text-secondary font-mono fs-8">
                Custom Ollama Model Name:
              </span>
              <input
                type="text"
                className="form-control form-control-mono font-mono fs-8 text-white bg-mono-dark"
                placeholder="e.g. llama3:8b, mistral, gpt-oss:120b-cloud..."
                value={activeModel}
                onChange={(e) => handleModelSelect(e.target.value)}
              />
            </div>
          </div>

          {/* Execution Framework */}
          <div className="mb-3">
            <label className="form-label font-mono fs-8 text-secondary fw-medium">
              Execution Framework / Agent Architecture:
            </label>
            <select
              className="form-select form-select-mono"
              value={activeEngine}
              onChange={(e) => setActiveEngine(e.target.value)}
            >
              <option value="standard">Standard Direct REST API (OpenAI / Ollama Direct)</option>
              <option value="langchain">LangChain Modular Chain Execution</option>
              <option value="langgraph">LangGraph Multi-Hop GraphRAG Agent Workflow</option>
            </select>
          </div>
        </div>
      )}

      {/* Tab 2: System Prompts Tuning */}
      {activeTab === 'prompts' && (
        <div className="card card-mono p-4">
          <div className="d-flex align-items-center justify-content-between mb-3 border-bottom border-mono-muted pb-2">
            <h3 className="h6 mb-0 text-light d-flex align-items-center gap-2">
              <MessageSquareCode size={16} />
              <span>Backend System Prompts & AI Templates</span>
            </h3>
            <span className="badge bg-mono-dark border border-mono text-secondary font-mono fs-8">
              Persistent JSON Config
            </span>
          </div>

          {promptMsg && (
            <div className="alert alert-dark border border-mono text-success py-1 px-2 font-mono fs-8 mb-3 d-flex align-items-center gap-1.5">
              <CheckCircle2 size={14} className="me-1" />
              <span>{promptMsg}</span>
            </div>
          )}

          <div className="row g-3 mb-4">
            
            {/* Auto Suggest Prompt */}
            <div className="col-12 col-md-6">
              <label className="form-label font-mono fs-8 text-secondary fw-semibold">
                AI Auto-Suggestion Prompt Template:
              </label>
              <textarea
                className="form-control form-control-mono bg-mono-dark text-light font-mono fs-8"
                rows={6}
                value={prompts.auto_suggest || ''}
                onChange={(e) => setPrompts({ ...prompts, auto_suggest: e.target.value })}
                placeholder="Auto-suggest prompt template..."
              />
              <small className="text-secondary fs-8 font-mono d-block mt-1">
                Supports placeables: <code>{'{title}'}</code>, <code>{'{content}'}</code>
              </small>
            </div>

            {/* Auto Organize Prompt */}
            <div className="col-12 col-md-6">
              <label className="form-label font-mono fs-8 text-secondary fw-semibold">
                Auto-Organize Note Prompt Template:
              </label>
              <textarea
                className="form-control form-control-mono bg-mono-dark text-light font-mono fs-8"
                rows={6}
                value={prompts.auto_organize || ''}
                onChange={(e) => setPrompts({ ...prompts, auto_organize: e.target.value })}
                placeholder="Auto-organize prompt template..."
              />
              <small className="text-secondary fs-8 font-mono d-block mt-1">
                Supports placeables: <code>{'{title}'}</code>, <code>{'{content}'}</code>, <code>{'{available_categories}'}</code>
              </small>
            </div>

            {/* Smart Merge Prompt */}
            <div className="col-12 col-md-6">
              <label className="form-label font-mono fs-8 text-secondary fw-semibold">
                Smart Merge Memory Prompt Template:
              </label>
              <textarea
                className="form-control form-control-mono bg-mono-dark text-light font-mono fs-8"
                rows={6}
                value={prompts.smart_merge || ''}
                onChange={(e) => setPrompts({ ...prompts, smart_merge: e.target.value })}
                placeholder="Smart merge prompt template..."
              />
            </div>

            {/* GraphRAG Companion Chat System Prompt */}
            <div className="col-12 col-md-6">
              <label className="form-label font-mono fs-8 text-secondary fw-semibold">
                GraphRAG Companion System Prompt:
              </label>
              <textarea
                className="form-control form-control-mono bg-mono-dark text-light font-mono fs-8"
                rows={6}
                value={prompts.graph_chat || ''}
                onChange={(e) => setPrompts({ ...prompts, graph_chat: e.target.value })}
                placeholder="GraphRAG chat system prompt..."
              />
            </div>
          </div>

          <div className="d-flex align-items-center gap-2">
            <button
              className="btn btn-mono-primary btn-sm font-mono d-flex align-items-center gap-2 py-1.5 px-3"
              onClick={handleSavePrompts}
              disabled={isSavingPrompts}
            >
              {isSavingPrompts ? (
                <span className="spinner-border spinner-border-sm text-light me-1" role="status" aria-hidden="true"></span>
              ) : (
                <Save size={14} />
              )}
              <span>Save Prompts Configuration</span>
            </button>

            <button
              className="btn btn-mono-outline btn-sm font-mono text-secondary d-flex align-items-center gap-2 py-1.5 px-3"
              onClick={handleResetPrompts}
              disabled={isSavingPrompts}
            >
              <RotateCcw size={14} />
              <span>Reset Factory Defaults</span>
            </button>
          </div>
        </div>
      )}

      {/* Tab 3: Storage Audit & Maintenance */}
      {activeTab === 'audit' && (
        <div className="row g-4">
          <div className="col-12 col-lg-6">
            <div className="card card-mono p-4 h-100">
              <div className="d-flex align-items-center justify-content-between mb-3 border-bottom border-mono-muted pb-2">
                <h3 className="h6 mb-0 text-light d-flex align-items-center gap-2">
                  <ShieldCheck size={16} />
                  <span>3-Way Storage Integrity Audit</span>
                </h3>
                <span className="badge bg-mono-dark text-success border border-mono fs-8 font-mono">
                  In-Sync
                </span>
              </div>

              <div className="row g-2 mb-3 text-center">
                <div className="col-4">
                  <div className="p-2 bg-mono-dark border border-mono-muted rounded">
                    <small className="text-secondary font-mono fs-8 d-block">Markdown Files</small>
                    <strong className="fs-6 text-light font-mono">{auditResult?.markdown_files_count || 0}</strong>
                  </div>
                </div>
                <div className="col-4">
                  <div className="p-2 bg-mono-dark border border-mono-muted rounded">
                    <small className="text-secondary font-mono fs-8 d-block">SQLite Records</small>
                    <strong className="fs-6 text-light font-mono">{auditResult?.sqlite_records_count || 0}</strong>
                  </div>
                </div>
                <div className="col-4">
                  <div className="p-2 bg-mono-dark border border-mono-muted rounded">
                    <small className="text-secondary font-mono fs-8 d-block">ChromaDB Chunks</small>
                    <strong className="fs-6 text-light font-mono">{auditResult?.chromadb_chunks_count || 0}</strong>
                  </div>
                </div>
              </div>

              <p className="fs-8 text-secondary font-mono mb-3">
                {auditResult?.message || 'Run 3-way audit to verify zero drift between Markdown files, SQLite DB, and ChromaDB vector store.'}
              </p>

              <button
                className="btn btn-mono-outline btn-sm font-mono mt-auto d-flex align-items-center justify-content-center gap-2"
                onClick={handleAuditClick}
                disabled={isAuditing}
              >
                {isAuditing ? (
                  <span className="spinner-border spinner-border-sm text-light me-1" role="status" aria-hidden="true"></span>
                ) : (
                  <RefreshCw size={14} className="me-1" />
                )}
                <span>{isAuditing ? 'Auditing...' : 'Run Integrity Audit'}</span>
              </button>
            </div>
          </div>

          <div className="col-12 col-lg-6">
            <div className="card card-mono p-4 h-100">
              <div className="d-flex align-items-center justify-content-between mb-3 border-bottom border-mono-muted pb-2">
                <h3 className="h6 mb-0 text-light d-flex align-items-center gap-2">
                  <Package size={16} />
                  <span>Snapshot Backup Maintenance</span>
                </h3>
              </div>

              {backupMsg && (
                <div className="alert alert-dark border border-mono text-success py-1 px-2 font-mono fs-8 mb-2 d-flex align-items-center gap-1.5">
                  <CheckCircle2 size={14} className="me-1" />
                  <span>{backupMsg}</span>
                </div>
              )}

              <p className="fs-8 text-secondary font-mono mb-3">
                Create compressed backups of Markdown memory files, SQLite database tables, and ChromaDB vector collections.
              </p>

              <button
                className="btn btn-mono-primary btn-sm font-mono mt-auto d-flex align-items-center justify-content-center gap-2"
                onClick={handleBackupClick}
                disabled={isBackingUp}
              >
                {isBackingUp ? (
                  <span className="spinner-border spinner-border-sm text-light me-1" role="status" aria-hidden="true"></span>
                ) : (
                  <Package size={14} />
                )}
                <span>{isBackingUp ? 'Creating Snapshot...' : 'Trigger Backup Snapshot'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Telemetry & Observability */}
      {activeTab === 'telemetry' && (
        <div className="card card-mono p-4">
          <div className="d-flex align-items-center justify-content-between mb-3 border-bottom border-mono-muted pb-2">
            <h3 className="h6 mb-0 text-light d-flex align-items-center gap-2">
              <Activity size={16} />
              <span>Telemetry & Observability Metrics</span>
            </h3>
            <span className="badge bg-mono-dark border border-mono text-secondary font-mono fs-8">
              System Telemetry
            </span>
          </div>

          <div className="row g-3 font-mono fs-8">
            <div className="col-12 col-md-3">
              <div className="p-3 bg-mono-dark border border-mono-muted rounded">
                <span className="text-secondary d-block mb-1">Tokens Processed</span>
                <strong className="fs-5 text-light">{metrics?.total_tokens_processed?.toLocaleString() || 0}</strong>
              </div>
            </div>
            <div className="col-12 col-md-3">
              <div className="p-3 bg-mono-dark border border-mono-muted rounded">
                <span className="text-secondary d-block mb-1">LLM Latency Avg</span>
                <strong className="fs-5 text-light">{metrics?.avg_llm_latency_ms || 0} ms</strong>
              </div>
            </div>
            <div className="col-12 col-md-3">
              <div className="p-3 bg-mono-dark border border-mono-muted rounded">
                <span className="text-secondary d-block mb-1">Vector Search Latency</span>
                <strong className="fs-5 text-light">{metrics?.vector_search_latency_ms || 0} ms</strong>
              </div>
            </div>
            <div className="col-12 col-md-3">
              <div className="p-3 bg-mono-dark border border-mono-muted rounded">
                <span className="text-secondary d-block mb-1">Embedding Model</span>
                <strong className="fs-5 text-light">{metrics?.active_embedding_model || 'nomic-embed-text'}</strong>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
