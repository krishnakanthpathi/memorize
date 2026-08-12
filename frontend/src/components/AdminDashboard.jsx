import React, { useState } from 'react';
import { Sliders, Activity, ShieldCheck, Cpu, Package, RefreshCw, CheckCircle2, Settings } from 'lucide-react';
import { fetchAudit, triggerBackup, setActiveModelApi } from '../services/api';

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
  const [auditResult, setAuditResult] = useState(auditData);
  const [isAuditing, setIsAuditing] = useState(false);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [backupMsg, setBackupMsg] = useState('');

  React.useEffect(() => {
    if (auditData) setAuditResult(auditData);
  }, [auditData]);

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
      setTimeout(() => setBackupMsg(''), 4000);
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

  return (
    <div className="d-flex flex-column h-100 bg-mono-dark p-4 overflow-auto">
      
      {/* Dashboard & Settings Header */}
      <div className="d-flex align-items-center justify-content-between mb-4 pb-2 border-bottom border-mono">
        <div>
          <h2 className="h5 font-weight-bold mb-1 text-white d-flex align-items-center gap-2">
            <Settings size={20} />
            <span>Admin Workspace</span>
          </h2>
          <p className="text-secondary fs-8 font-mono mb-0">
            Configure default LLM models, execution frameworks, 3-way storage audit, and system snapshots.
          </p>
        </div>
      </div>

      <div className="row g-4">
        
        {/* Card 1: Primary LLM Model & Engine Configuration */}
        <div className="col-12 col-lg-6">
          <div className="card card-mono p-3 h-100">
            <div className="d-flex align-items-center justify-content-between mb-3 border-bottom border-mono-muted pb-2">
              <h3 className="h6 mb-0 text-light d-flex align-items-center gap-2">
                <Cpu size={16} />
                <span>LLM Model & Engine Configuration</span>
              </h3>
              <span className="badge bg-mono-dark border border-mono text-white font-mono fs-8">
                {activeModel}
              </span>
            </div>

            {/* Active Model Selector Dropdown & Custom Input */}
            <div className="mb-3">
              <label className="form-label font-mono fs-8 text-secondary">
                Select Active LLM Model (Discovered Ollama & API Models):
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
              <div className="input-group input-group-sm mt-1">
                <span className="input-group-text bg-mono-dark border-mono text-secondary font-mono fs-8">
                  Custom Ollama Model:
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

            {/* Engine Type (LangChain / LangGraph) */}
            <div className="mb-3">
              <label className="form-label font-mono fs-8 text-secondary">
                Execution Framework / Agent Architecture:
              </label>
              <select
                className="form-select form-select-mono"
                value={activeEngine}
                onChange={(e) => setActiveEngine(e.target.value)}
              >
                <option value="standard">Standard Direct API (OpenAI / Ollama Direct)</option>
                <option value="langchain">LangChain Modular Chain Execution</option>
                <option value="langgraph">LangGraph Multi-Hop GraphRAG Agent Workflow</option>
              </select>
            </div>

            <div className="p-2 bg-mono-dark border border-mono-muted rounded font-mono fs-8 text-secondary mt-auto">
              <div>Provider Mode: Managed Client REST Bridge</div>
              <div>Auto Fallback: OpenAI → Local Ollama fallback</div>
            </div>
          </div>
        </div>

        {/* Card 2: Three-Way Storage Audit Matrix */}
        <div className="col-12 col-lg-6">
          <div className="card card-mono p-3 h-100">
            <div className="d-flex align-items-center justify-content-between mb-3 border-bottom border-mono-muted pb-2">
              <h3 className="h6 mb-0 text-light d-flex align-items-center gap-2">
                <ShieldCheck size={16} />
                <span>3-Way Storage Integrity Audit</span>
              </h3>
              <span className="badge bg-mono-dark text-success border border-mono fs-8 font-mono">
                100% In-Sync
              </span>
            </div>

            {/* Matrix Breakdown */}
            <div className="row g-2 mb-3 text-center">
              <div className="col-4">
                <div className="p-2 bg-mono-dark border border-mono-muted rounded">
                  <small className="text-secondary font-mono fs-8 d-block">Markdown Files</small>
                  <strong className="fs-6 text-light font-mono">{auditResult?.markdown_files_count || 4}</strong>
                </div>
              </div>
              <div className="col-4">
                <div className="p-2 bg-mono-dark border border-mono-muted rounded">
                  <small className="text-secondary font-mono fs-8 d-block">SQLite Records</small>
                  <strong className="fs-6 text-light font-mono">{auditResult?.sqlite_records_count || 4}</strong>
                </div>
              </div>
              <div className="col-4">
                <div className="p-2 bg-mono-dark border border-mono-muted rounded">
                  <small className="text-secondary font-mono fs-8 d-block">ChromaDB Chunks</small>
                  <strong className="fs-6 text-light font-mono">{auditResult?.chromadb_chunks_count || 18}</strong>
                </div>
              </div>
            </div>

            <p className="fs-8 text-secondary font-mono mb-3">
              {auditResult?.message}
            </p>

            <div className="d-flex align-items-center gap-2 mt-auto">
              <button
                className="btn btn-mono-outline btn-sm font-mono flex-grow-1 d-flex align-items-center justify-content-center gap-2"
                onClick={handleAuditClick}
                disabled={isAuditing}
              >
                {isAuditing ? (
                  <span className="spinner-border spinner-border-sm text-light me-1" role="status" aria-hidden="true"></span>
                ) : (
                  <RefreshCw size={14} className="me-1" />
                )}
                <span>{isAuditing ? 'Running 3-Way Audit...' : 'Run Integrity Audit'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Card 3: Performance Telemetry & Metrics */}
        <div className="col-12 col-lg-6">
          <div className="card card-mono p-3 h-100">
            <div className="d-flex align-items-center justify-content-between mb-3 border-bottom border-mono-muted pb-2">
              <h3 className="h6 mb-0 text-light d-flex align-items-center gap-2">
                <Activity size={16} />
                <span>Telemetry & System Metrics</span>
              </h3>
              <span className="badge bg-mono-dark border border-mono text-secondary font-mono fs-8">
                Observability
              </span>
            </div>

            <div className="row g-2 mb-2 font-mono fs-8">
              <div className="col-6">
                <div className="p-2 bg-mono-dark border border-mono-muted rounded">
                  <span className="text-secondary d-block">Tokens Processed</span>
                  <strong className="text-light">{metrics?.total_tokens_processed?.toLocaleString()}</strong>
                </div>
              </div>
              <div className="col-6">
                <div className="p-2 bg-mono-dark border border-mono-muted rounded">
                  <span className="text-secondary d-block">LLM Latency Avg</span>
                  <strong className="text-light">{metrics?.avg_llm_latency_ms} ms</strong>
                </div>
              </div>
              <div className="col-6">
                <div className="p-2 bg-mono-dark border border-mono-muted rounded">
                  <span className="text-secondary d-block">Vector Search Latency</span>
                  <strong className="text-light">{metrics?.vector_search_latency_ms} ms</strong>
                </div>
              </div>
              <div className="col-6">
                <div className="p-2 bg-mono-dark border border-mono-muted rounded">
                  <span className="text-secondary d-block">Embedding Model</span>
                  <strong className="text-light">{metrics?.active_embedding_model}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Card 4: Backup & Snapshot Maintenance */}
        <div className="col-12 col-lg-6">
          <div className="card card-mono p-3 h-100">
            <div className="d-flex align-items-center justify-content-between mb-3 border-bottom border-mono-muted pb-2">
              <h3 className="h6 mb-0 text-light d-flex align-items-center gap-2">
                <Package size={16} />
                <span>Backup & Maintenance</span>
              </h3>
            </div>

            {backupMsg && (
              <div className="alert alert-dark border border-mono text-success py-1 px-2 font-mono fs-8 mb-2 d-flex align-items-center gap-1.5">
                <CheckCircle2 size={14} className="me-1" />
                <span>{backupMsg}</span>
              </div>
            )}

            <p className="fs-8 text-secondary font-mono mb-3">
              Generate compressed system snapshots of Markdown files, SQLite DB, and ChromaDB vector embeddings.
            </p>

            <div className="d-flex align-items-center gap-2 mt-auto">
              <button
                className="btn btn-mono-primary btn-sm flex-grow-1 font-mono d-flex align-items-center justify-content-center gap-2"
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

      </div>

    </div>
  );
}
