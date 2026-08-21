import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Activity,
  Play,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
  Zap,
  Sliders,
  Cpu,
  Layers,
  FileText,
  Eye,
  StopCircle,
  HelpCircle,
  ChevronRight,
  Filter,
  Check,
  AlertOctagon,
  ArrowUpRight,
  Database,
  Terminal,
} from "lucide-react";
import { toast } from "sonner";
import amipService from "../services/amipService.js";

export default function AMIPControlCenterPage() {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState("overview");

  // Telemetry & Core States
  const [health, setHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [diagnostics, setDiagnostics] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [pendingReviews, setPendingReviews] = useState([]);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [traceIdInput, setTraceIdInput] = useState("");
  const [logs, setLogs] = useState([]);
  const [logFilterLevel, setLogFilterLevel] = useState("ALL");

  // Loading & Auto-refresh States
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState(5000); // 5s default
  const isFetchingRef = useRef(false);

  // Modals
  const [showTriggerModal, setShowTriggerModal] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [selectedReviewItem, setSelectedReviewItem] = useState(null);
  const [selectedAuditBundle, setSelectedAuditBundle] = useState(null);

  // Trigger Form State
  const [triggerForm, setTriggerForm] = useState({
    task_type: "DOCUMENT_IMPORT",
    priority: "NORMAL",
    summary: "Manual AMIP multi-agent execution",
    execution_mode: "SYNCHRONOUS",
    idempotency_key: "",
    input_payload: '{\n  "filename": "sample_invoice.docx",\n  "amount": 4500\n}',
  });

  // Override Form State
  const [overrideForm, setOverrideForm] = useState({
    action: "APPROVE",
    reason: "",
    notes: "",
  });

  // Main data fetch function
  const fetchAllData = useCallback(async (isManual = false) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    if (isManual) setRefreshing(true);

    try {
      const [hRes, mRes, dRes, eRes, rRes] = await Promise.allSettled([
        amipService.getHealth(),
        amipService.getMetrics(),
        amipService.getDiagnostics(),
        amipService.getExecutions(50),
        amipService.getPendingReviews(),
      ]);

      if (hRes.status === "fulfilled") setHealth(hRes.value);
      if (mRes.status === "fulfilled") setMetrics(mRes.value);
      if (dRes.status === "fulfilled") setDiagnostics(dRes.value);
      if (eRes.status === "fulfilled") setExecutions(eRes.value);
      if (rRes.status === "fulfilled") setPendingReviews(rRes.value);
    } catch (err) {
      console.error("Failed to load AMIP telemetry:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
      isFetchingRef.current = false;
    }
  }, []);

  // Initial mount & Polling Timer
  useEffect(() => {
    fetchAllData();

    if (autoRefreshInterval > 0) {
      const timer = setInterval(() => {
        fetchAllData();
      }, autoRefreshInterval);
      return () => clearInterval(timer);
    }
  }, [autoRefreshInterval, fetchAllData]);

  // Trigger Workflow handler
  const handleTriggerWorkflow = async (e) => {
    e.preventDefault();
    let parsedPayload = {};
    try {
      if (triggerForm.input_payload.trim()) {
        parsedPayload = JSON.parse(triggerForm.input_payload);
      }
    } catch (err) {
      toast.error("Invalid JSON in input payload");
      return;
    }

    try {
      const payload = {
        task_type: triggerForm.task_type,
        priority: triggerForm.priority,
        summary: triggerForm.summary,
        execution_mode: triggerForm.execution_mode,
        input_payload: parsedPayload,
      };
      if (triggerForm.idempotency_key.trim()) {
        payload.idempotency_key = triggerForm.idempotency_key.trim();
      }

      const res = await amipService.executeWorkflow(payload);

      toast.success(`Workflow '${res.workflow_id}' triggered: ${res.status}`);
      setShowTriggerModal(false);
      fetchAllData(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to trigger workflow");
    }
  };

  // Cancel Workflow handler
  const handleCancelWorkflow = async (workflowId) => {
    if (!window.confirm(`Are you sure you want to cancel workflow '${workflowId}'?`)) return;
    try {
      const res = await amipService.cancelWorkflow(workflowId);
      toast.success(res.message);
      fetchAllData(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to cancel workflow");
    }
  };

  // View Audit Bundle handler
  const handleViewAudit = async (workflowId) => {
    try {
      const bundle = await amipService.getAuditBundle(workflowId);
      setSelectedAuditBundle(bundle);
      setShowAuditModal(true);
    } catch (err) {
      toast.error("Failed to fetch workflow audit bundle");
    }
  };

  // View Trace handler
  const handleFetchTrace = async (traceId) => {
    const tid = traceId || traceIdInput;
    if (!tid) {
      toast.error("Please enter a Trace ID");
      return;
    }
    try {
      const trace = await amipService.getTraceInfo(tid);
      setSelectedTrace(trace);
      setActiveTab("traces");
    } catch (err) {
      toast.error(`Trace '${tid}' not found`);
    }
  };

  // Fetch workflow logs for selected execution
  const handleFetchLogs = async (workflowId) => {
    try {
      const level = logFilterLevel === "ALL" ? null : logFilterLevel;
      const logData = await amipService.getExecutionLogs(workflowId, level);
      setLogs(logData);
    } catch (err) {
      toast.error("Failed to fetch execution logs");
    }
  };

  // Open Override Modal
  const handleOpenOverride = (reviewItem) => {
    setSelectedReviewItem(reviewItem);
    setOverrideForm({
      action: "APPROVE",
      reason: "",
      notes: "",
    });
    setShowOverrideModal(true);
  };

  // Submit Override handler
  const handleSubmitOverride = async (e) => {
    e.preventDefault();
    if (!overrideForm.reason.trim()) {
      toast.error("Please provide an operator justification reason");
      return;
    }

    if (
      overrideForm.action === "REJECT" &&
      !window.confirm("Confirm: Are you sure you want to REJECT this workflow execution?")
    ) {
      return;
    }

    try {
      const res = await amipService.submitOverride(selectedReviewItem.workflow_id, {
        action: overrideForm.action,
        reason: overrideForm.reason,
        notes: overrideForm.notes,
      });

      toast.success(res.message);
      setShowOverrideModal(false);
      fetchAllData(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to submit override");
    }
  };

  // Status color helper
  const getStatusBadge = (status) => {
    switch (status) {
      case "HEALTHY":
      case "COMPLETED":
      case "APPROVED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-none">
            <CheckCircle2 size={13} /> {status}
          </span>
        );
      case "REVIEW_REQUIRED":
      case "DEGRADED":
      case "CANCELLING":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-none">
            <AlertTriangle size={13} /> {status}
          </span>
        );
      case "CRITICAL":
      case "FAILED":
      case "REJECTED":
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-none">
            <XCircle size={13} /> {status}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700 rounded-none">
            <Clock size={13} /> {status || "UNKNOWN"}
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8 space-y-8 font-sans">
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
              <Cpu className="text-cyan-400" size={24} />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
                AMIP Mission Control
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
              </h1>
              <p className="text-xs text-slate-400 font-medium">
                Autonomous Multi-Agent Intelligence Platform • Runtime Monitoring & HITL Dispatcher
              </p>
            </div>
          </div>
        </div>

        {/* Global Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Auto Refresh Interval */}
          <div className="flex items-center bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs text-slate-300">
            <Clock size={14} className="mr-2 text-cyan-400" />
            <span className="mr-2 text-slate-400">Polling:</span>
            <select
              value={autoRefreshInterval}
              onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
              className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
            >
              <option value={0} className="bg-slate-900">Off</option>
              <option value={3000} className="bg-slate-900">3s</option>
              <option value={5000} className="bg-slate-900">5s</option>
              <option value={10000} className="bg-slate-900">10s</option>
            </select>
          </div>

          {/* Refresh Button */}
          <button
            onClick={() => fetchAllData(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold transition"
          >
            <RefreshCw size={14} className={refreshing ? "animate-spin text-cyan-400" : "text-slate-300"} />
            Refresh
          </button>

          {/* Trigger Workflow Modal Opener */}
          <button
            onClick={() => setShowTriggerModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs tracking-wider uppercase transition shadow-lg shadow-cyan-500/20"
          >
            <Play size={14} />
            Dispatch Workflow
          </button>
        </div>
      </div>

      {/* Top Stat Cards (Platform Overview) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Health */}
        <div className="bg-slate-900/80 border border-slate-800 p-5 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Health Status</span>
            <Activity size={18} className="text-cyan-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-3">
            {getStatusBadge(health?.overall_status || "HEALTHY")}
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Active Workflows: <span className="text-white font-bold">{health?.active_workflows ?? 0}</span>
          </p>
        </div>

        {/* Card 2: Workflows Throughput */}
        <div className="bg-slate-900/80 border border-slate-800 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Executions</span>
            <Layers size={18} className="text-indigo-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-white">{metrics?.total_workflows_executed ?? executions.length}</span>
            <span className="text-xs text-slate-400">runs</span>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Avg Duration: <span className="text-white font-bold">{metrics?.average_execution_duration_ms?.toFixed(1) ?? 0} ms</span>
          </p>
        </div>

        {/* Card 3: Consensus Success Rate */}
        <div className="bg-slate-900/80 border border-slate-800 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Consensus Success</span>
            <ShieldCheck size={18} className="text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-emerald-400">{metrics?.success_rate?.toFixed(1) ?? 100}%</span>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Errors Logged: <span className="text-rose-400 font-bold">{metrics?.total_errors_logged ?? 0}</span>
          </p>
        </div>

        {/* Card 4: HITL Review Queue */}
        <div className="bg-slate-900/80 border border-slate-800 p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">HITL Review Queue</span>
            <AlertOctagon size={18} className={pendingReviews.length > 0 ? "text-amber-400 animate-pulse" : "text-slate-500"} />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className={`text-2xl font-black ${pendingReviews.length > 0 ? "text-amber-400" : "text-slate-400"}`}>
              {pendingReviews.length}
            </span>
            <span className="text-xs text-slate-400">pending</span>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Requires Human Intervention
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap border-b border-slate-800 gap-2">
        {[
          { id: "overview", label: "Subsystems", icon: Sliders },
          { id: "workflows", label: `Workflows (${executions.length})`, icon: Layers },
          { id: "hitl", label: `HITL Queue (${pendingReviews.length})`, icon: AlertTriangle, highlight: pendingReviews.length > 0 },
          { id: "traces", label: "Distributed Traces", icon: Zap },
          { id: "diagnostics", label: "Diagnostics & Logs", icon: Terminal },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition ${
              activeTab === tab.id
                ? "border-cyan-400 text-cyan-400 bg-cyan-500/5"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            } ${tab.highlight ? "text-amber-400" : ""}`}
          >
            <tab.icon size={15} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Subsystem Health Matrix */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 p-6">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
              <Cpu size={16} className="text-cyan-400" />
              Autonomous Agent Subsystem Heartbeat
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {health?.subsystems &&
                Object.entries(health.subsystems).map(([subsystemName, subState]) => (
                  <div key={subsystemName} className="bg-slate-950 border border-slate-800 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-xs text-white">{subsystemName}</span>
                      {getStatusBadge(subState.status)}
                    </div>
                    <p className="text-[11px] text-slate-400 mb-1">{subState.details}</p>
                    <p className="text-[10px] text-slate-500 font-mono">
                      Last Check: {new Date(subState.last_check).toLocaleTimeString()}
                    </p>
                  </div>
                ))}
            </div>
          </div>

          {/* System Runtime Diagnostics Overview */}
          {diagnostics && (
            <div className="bg-slate-900 border border-slate-800 p-6">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
                <Database size={16} className="text-indigo-400" />
                Runtime Performance & Diagnostics
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-950 border border-slate-800 p-4">
                  <span className="text-xs text-slate-400 block mb-1">Active Trace Count</span>
                  <span className="text-xl font-bold text-white">{diagnostics.active_traces_count ?? 0}</span>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-4">
                  <span className="text-xs text-slate-400 block mb-1">Total Spans Captured</span>
                  <span className="text-xl font-bold text-white">{diagnostics.total_spans_count ?? 0}</span>
                </div>
                <div className="bg-slate-950 border border-slate-800 p-4">
                  <span className="text-xs text-slate-400 block mb-1">Execution Snapshots In-Memory</span>
                  <span className="text-xl font-bold text-white">{diagnostics.snapshots_in_memory ?? 0}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Workflow History & Lifecycle */}
      {activeTab === "workflows" && (
        <div className="bg-slate-900 border border-slate-800 p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              Execution History & Runtime Snapshots
            </h2>
            <div className="text-xs text-slate-400">
              Total Recorded: <span className="text-white font-bold">{executions.length}</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider bg-slate-950">
                  <th className="p-3">Workflow ID</th>
                  <th className="p-3">Task Type</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Tasks Completed</th>
                  <th className="p-3">Duration</th>
                  <th className="p-3">Timestamp</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {executions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-6 text-center text-slate-500">
                      No workflow executions recorded yet. Click "Dispatch Workflow" to trigger one.
                    </td>
                  </tr>
                ) : (
                  executions.map((exec) => (
                    <tr key={exec.workflow_id} className="hover:bg-slate-800/40 transition font-mono">
                      <td className="p-3 text-cyan-400 font-semibold">{exec.workflow_id}</td>
                      <td className="p-3 text-slate-300 font-sans">{exec.task_type || "DOCUMENT_IMPORT"}</td>
                      <td className="p-3 font-sans">{getStatusBadge(exec.status)}</td>
                      <td className="p-3 text-slate-300">
                        {exec.completed_tasks?.length || 0} tasks
                      </td>
                      <td className="p-3 text-slate-400">{exec.duration_ms ? `${exec.duration_ms.toFixed(1)} ms` : "-"}</td>
                      <td className="p-3 text-slate-400">
                        {exec.timestamp ? new Date(exec.timestamp).toLocaleTimeString() : "-"}
                      </td>
                      <td className="p-3 text-right font-sans">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleViewAudit(exec.workflow_id)}
                            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] font-medium"
                            title="Inspect Audit Bundle"
                          >
                            <Eye size={12} className="inline mr-1" /> Audit
                          </button>
                          {exec.status === "RUNNING" && (
                            <button
                              onClick={() => handleCancelWorkflow(exec.workflow_id)}
                              className="px-2.5 py-1 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[11px] font-medium"
                              title="Cancel Workflow"
                            >
                              <StopCircle size={12} className="inline mr-1" /> Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: HITL Review Queue */}
      {activeTab === "hitl" && (
        <div className="bg-slate-900 border border-slate-800 p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-400" />
                Human-in-the-Loop Review Queue
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Workflows requiring manual verification due to divergent multi-agent consensus or low confidence.
              </p>
            </div>
            <span className="px-3 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-bold">
              {pendingReviews.length} Pending
            </span>
          </div>

          {pendingReviews.length === 0 ? (
            <div className="p-12 text-center border border-dashed border-slate-800 bg-slate-950">
              <CheckCircle2 size={32} className="mx-auto text-emerald-400 mb-3" />
              <h3 className="text-sm font-bold text-white">Review Queue Clean</h3>
              <p className="text-xs text-slate-500 mt-1">
                All multi-agent decisions met automated consensus thresholds. No pending manual reviews.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {pendingReviews.map((item) => (
                <div key={item.workflow_id} className="bg-slate-950 border border-amber-500/30 p-5 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-cyan-400 font-bold">{item.workflow_id}</span>
                      {getStatusBadge(item.status)}
                      <span className="text-xs text-slate-400 font-mono">Trace: {item.trace_id || "-"}</span>
                    </div>
                    <div className="text-xs text-slate-500">
                      Requested: {new Date(item.created_at || Date.now()).toLocaleTimeString()}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <span className="text-[11px] uppercase font-bold text-slate-400 block mb-1">Reason for Flagging</span>
                      <p className="text-xs text-slate-200 bg-slate-900 p-2.5 border border-slate-800">
                        {item.reason || "Conflicting agent votes detected during consensus decisioning."}
                      </p>
                    </div>
                    <div>
                      <span className="text-[11px] uppercase font-bold text-slate-400 block mb-1">Agent Participation & States</span>
                      <div className="flex flex-wrap gap-2">
                        {item.agent_states && Object.entries(item.agent_states).map(([agent, st]) => (
                          <span key={agent} className="px-2 py-1 bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
                            <span className="font-semibold text-white">{agent}</span>: {st}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end pt-2">
                    <button
                      onClick={() => handleOpenOverride(item)}
                      className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition"
                    >
                      Review & Submit Override
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Distributed Tracing */}
      {activeTab === "traces" && (
        <div className="bg-slate-900 border border-slate-800 p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Zap size={16} className="text-cyan-400" />
                Distributed Trace & Spans Explorer
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Inspect end-to-end multi-agent span hierarchies and task execution latencies.
              </p>
            </div>

            {/* Trace ID search input */}
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={traceIdInput}
                onChange={(e) => setTraceIdInput(e.target.value)}
                placeholder="Enter trace ID (trc-...)"
                className="bg-slate-950 border border-slate-700 px-3 py-1.5 text-xs text-white placeholder-slate-500 font-mono w-64 focus:outline-none focus:border-cyan-400"
              />
              <button
                onClick={() => handleFetchTrace()}
                className="px-3 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition"
              >
                Search
              </button>
            </div>
          </div>

          {selectedTrace ? (
            <div className="space-y-4">
              <div className="bg-slate-950 border border-slate-800 p-4 flex flex-wrap items-center justify-between gap-3">
                <div className="font-mono text-xs">
                  <span className="text-slate-400">Trace ID: </span>
                  <span className="text-cyan-400 font-bold">{selectedTrace.trace_id}</span>
                </div>
                <div className="text-xs text-slate-400">
                  Total Spans: <span className="text-white font-bold">{selectedTrace.spans?.length || 0}</span>
                </div>
              </div>

              {/* Waterfall Spans */}
              <div className="space-y-2">
                {selectedTrace.spans?.map((span, idx) => (
                  <div key={span.span_id || idx} className="bg-slate-950 border border-slate-800 p-3 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-200 font-mono flex items-center gap-2">
                        <ChevronRight size={14} className="text-cyan-400" />
                        {span.name}
                      </span>
                      <span className="text-slate-400 font-mono">
                        {span.duration_ms ? `${span.duration_ms.toFixed(1)} ms` : "in progress"}
                      </span>
                    </div>

                    {/* Visual Latency Bar */}
                    <div className="w-full bg-slate-900 h-1.5 overflow-hidden">
                      <div
                        className="bg-cyan-400 h-full transition-all"
                        style={{ width: `${Math.min(100, Math.max(10, (span.duration_ms || 10) / 2))}%` }}
                      ></div>
                    </div>

                    {span.metadata && Object.keys(span.metadata).length > 0 && (
                      <div className="text-[10px] text-slate-400 font-mono bg-slate-900 p-2 border border-slate-800/80">
                        {JSON.stringify(span.metadata)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-8 text-center border border-dashed border-slate-800 bg-slate-950">
              <Zap size={24} className="mx-auto text-slate-500 mb-2" />
              <p className="text-xs text-slate-400">
                Select a workflow from the Workflows tab or enter a Trace ID above to visualize the execution tree.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Diagnostics & Logs */}
      {activeTab === "diagnostics" && (
        <div className="bg-slate-900 border border-slate-800 p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Terminal size={16} className="text-cyan-400" />
                Structured Logs & Diagnostics Viewer
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Real-time structured telemetry stream for active and historical agent tasks.
              </p>
            </div>

            {/* Level Filter */}
            <div className="flex items-center gap-2 text-xs">
              <Filter size={14} className="text-slate-400" />
              <span className="text-slate-400">Filter Level:</span>
              <select
                value={logFilterLevel}
                onChange={(e) => setLogFilterLevel(e.target.value)}
                className="bg-slate-950 border border-slate-800 text-white px-2.5 py-1 text-xs focus:outline-none"
              >
                <option value="ALL">ALL LEVELS</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
              </select>
            </div>
          </div>

          {/* Workflow selector for logs */}
          <div className="bg-slate-950 border border-slate-800 p-4">
            <span className="text-xs text-slate-400 block mb-2">Select Workflow Execution for Detailed Logs:</span>
            <div className="flex flex-wrap gap-2">
              {executions.slice(0, 10).map((ex) => (
                <button
                  key={ex.workflow_id}
                  onClick={() => handleFetchLogs(ex.workflow_id)}
                  className="px-3 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-cyan-400"
                >
                  {ex.workflow_id}
                </button>
              ))}
            </div>
          </div>

          {/* Log Stream Output */}
          <div className="bg-slate-950 border border-slate-800 p-4 font-mono text-xs max-h-96 overflow-y-auto space-y-1.5">
            {logs.length === 0 ? (
              <div className="text-slate-500 text-center py-6">
                No logs loaded. Click a workflow above to stream its execution logs.
              </div>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-2 hover:bg-slate-900/50 p-1">
                  <span className="text-slate-500 shrink-0">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                  <span
                    className={`font-bold shrink-0 ${
                      log.level === "ERROR"
                        ? "text-rose-400"
                        : log.level === "WARNING"
                        ? "text-amber-400"
                        : "text-cyan-400"
                    }`}
                  >
                    {log.level}
                  </span>
                  <span className="text-slate-400 shrink-0">[{log.agent_name || "AMIP"}]</span>
                  <span className="text-slate-200">{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 1: TRIGGER WORKFLOW                                                  */}
      {/* ========================================================================= */}
      {showTriggerModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-lg p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
                <Play size={16} className="text-cyan-400" />
                Dispatch Autonomous Workflow
              </h3>
              <button onClick={() => setShowTriggerModal(false)} className="text-slate-400 hover:text-white">
                <XCircle size={18} />
              </button>
            </div>

            <form onSubmit={handleTriggerWorkflow} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-bold">Task Type</label>
                <select
                  value={triggerForm.task_type}
                  onChange={(e) => setTriggerForm({ ...triggerForm, task_type: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 focus:outline-none focus:border-cyan-400"
                >
                  <option value="DOCUMENT_IMPORT">DOCUMENT_IMPORT (DocIntel + Learning + Validation)</option>
                  <option value="VALIDATION_ENGINE">VALIDATION_ENGINE (Validation + Graph)</option>
                  <option value="REVIEW_CORRECTION">REVIEW_CORRECTION (Learning + Validation)</option>
                  <option value="COPILOT_CHAT">COPILOT_CHAT (Copilot Advisory)</option>
                  <option value="PREDICTIVE_FORECAST">PREDICTIVE_FORECAST (Risk & Anomaly)</option>
                  <option value="GRAPH_QUERY">GRAPH_QUERY (Knowledge Graph Topology)</option>
                  <option value="GENERAL_QUERY">GENERAL_QUERY (DocIntel + Validation)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-bold">Priority</label>
                  <select
                    value={triggerForm.priority}
                    onChange={(e) => setTriggerForm({ ...triggerForm, priority: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 focus:outline-none"
                  >
                    <option value="LOW">LOW</option>
                    <option value="NORMAL">NORMAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-bold">Execution Mode</label>
                  <select
                    value={triggerForm.execution_mode}
                    onChange={(e) => setTriggerForm({ ...triggerForm, execution_mode: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 focus:outline-none"
                  >
                    <option value="SYNCHRONOUS">SYNCHRONOUS</option>
                    <option value="ASYNCHRONOUS">ASYNCHRONOUS</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-bold">Summary / Description</label>
                  <input
                    type="text"
                    value={triggerForm.summary}
                    onChange={(e) => setTriggerForm({ ...triggerForm, summary: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-bold">Idempotency Key (Optional)</label>
                  <input
                    type="text"
                    value={triggerForm.idempotency_key}
                    onChange={(e) => setTriggerForm({ ...triggerForm, idempotency_key: e.target.value })}
                    placeholder="e.g. req-invoice-988"
                    className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 font-mono text-xs focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-bold">Input Payload (JSON)</label>
                <textarea
                  rows={4}
                  value={triggerForm.input_payload}
                  onChange={(e) => setTriggerForm({ ...triggerForm, input_payload: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 font-mono text-xs focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowTriggerModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 font-bold uppercase text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold uppercase text-xs tracking-wider"
                >
                  Dispatch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: HITL REVIEW & OVERRIDE                                            */}
      {/* ========================================================================= */}
      {showOverrideModal && selectedReviewItem && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-lg p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-400" />
                Human Operator Decision Override
              </h3>
              <button onClick={() => setShowOverrideModal(false)} className="text-slate-400 hover:text-white">
                <XCircle size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmitOverride} className="space-y-4 text-xs">
              <div className="bg-slate-950 border border-slate-800 p-3 space-y-1">
                <span className="text-slate-400 block">Workflow ID:</span>
                <span className="font-mono font-bold text-cyan-400">{selectedReviewItem.workflow_id}</span>
                <span className="text-slate-400 block mt-2">Current Reason:</span>
                <span className="text-slate-200">{selectedReviewItem.reason}</span>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-bold">Override Action</label>
                <div className="grid grid-cols-3 gap-2">
                  {["APPROVE", "REJECT", "ESCALATE"].map((act) => (
                    <button
                      key={act}
                      type="button"
                      onClick={() => setOverrideForm({ ...overrideForm, action: act })}
                      className={`py-2 px-3 text-xs font-bold uppercase tracking-wider border transition ${
                        overrideForm.action === act
                          ? act === "APPROVE"
                            ? "bg-emerald-500 text-slate-950 border-emerald-400"
                            : act === "REJECT"
                            ? "bg-rose-500 text-white border-rose-400"
                            : "bg-amber-500 text-slate-950 border-amber-400"
                          : "bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800"
                      }`}
                    >
                      {act}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-bold">Operator Justification Reason (Required)</label>
                <textarea
                  rows={3}
                  value={overrideForm.reason}
                  onChange={(e) => setOverrideForm({ ...overrideForm, reason: e.target.value })}
                  placeholder="State evidence or audit reasoning for overriding the multi-agent consensus..."
                  className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-bold">Additional Notes (Optional)</label>
                <input
                  type="text"
                  value={overrideForm.notes}
                  onChange={(e) => setOverrideForm({ ...overrideForm, notes: e.target.value })}
                  placeholder="Ticket ID or reference notes"
                  className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowOverrideModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 font-bold uppercase text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold uppercase text-xs tracking-wider"
                >
                  Submit Decision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 3: AUDIT BUNDLE VIEWER                                              */}
      {/* ========================================================================= */}
      {showAuditModal && selectedAuditBundle && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-2xl max-h-[85vh] overflow-y-auto p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
                <FileText size={16} className="text-cyan-400" />
                Workflow Audit Bundle ({selectedAuditBundle.workflow_id})
              </h3>
              <button onClick={() => setShowAuditModal(false)} className="text-slate-400 hover:text-white">
                <XCircle size={18} />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="bg-slate-950 border border-slate-800 p-4 grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-500 block">Status:</span>
                  {getStatusBadge(selectedAuditBundle.status)}
                </div>
                <div>
                  <span className="text-slate-500 block">Trace ID:</span>
                  <span className="font-mono text-cyan-400">{selectedAuditBundle.trace_id || "-"}</span>
                </div>
              </div>

              {/* Narrative Explanation */}
              {selectedAuditBundle.explanation_report && (
                <div className="bg-slate-950 border border-slate-800 p-4 space-y-2">
                  <span className="font-bold text-slate-300 block uppercase tracking-wider text-[11px]">
                    Explainability Narrative
                  </span>
                  <p className="text-slate-200 leading-relaxed">
                    {selectedAuditBundle.explanation_report.narrative}
                  </p>
                </div>
              )}

              {/* Timeline Events */}
              <div className="bg-slate-950 border border-slate-800 p-4 space-y-2">
                <span className="font-bold text-slate-300 block uppercase tracking-wider text-[11px]">
                  Execution Timeline Events
                </span>
                <div className="space-y-2">
                  {selectedAuditBundle.timeline_events?.map((ev, idx) => (
                    <div key={idx} className="flex items-start gap-2 border-b border-slate-900 pb-1.5">
                      <span className="text-slate-500 font-mono text-[10px]">[{new Date(ev.timestamp).toLocaleTimeString()}]</span>
                      <span className="font-bold text-cyan-400 font-mono text-[11px]">[{ev.agent_name}]</span>
                      <span className="text-slate-200 text-xs">{ev.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowAuditModal(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-bold uppercase text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
