import api from "./api.js";

/**
 * AMIP Client Service.
 * Provides unified API methods for AMIP Mission Control, runtime monitoring,
 * workflow execution, distributed tracing, and human-in-the-loop overrides.
 */
export const amipService = {
  // 1. Health & Telemetry
  getHealth: async () => {
    const response = await api.get("/amip/health");
    return response.data;
  },

  getMetrics: async () => {
    const response = await api.get("/amip/metrics");
    return response.data;
  },

  getDiagnostics: async () => {
    const response = await api.get("/amip/diagnostics");
    return response.data;
  },

  // 2. Executions & Logs
  getExecutions: async (limit = 50) => {
    const response = await api.get(`/amip/executions?limit=${limit}`);
    return response.data;
  },

  getExecution: async (workflowId) => {
    const response = await api.get(`/amip/executions/${workflowId}`);
    return response.data;
  },

  getExecutionLogs: async (workflowId, level = null) => {
    const url = level
      ? `/amip/executions/${workflowId}/logs?level=${level}`
      : `/amip/executions/${workflowId}/logs`;
    const response = await api.get(url);
    return response.data;
  },

  // 3. Tracing
  getTraceInfo: async (traceId) => {
    const response = await api.get(`/amip/traces/${traceId}`);
    return response.data;
  },

  // 4. Workflow Lifecycle
  executeWorkflow: async (payload) => {
    const response = await api.post("/amip/workflows/execute", payload);
    return response.data;
  },

  cancelWorkflow: async (workflowId) => {
    const response = await api.post(`/amip/workflows/${workflowId}/cancel`);
    return response.data;
  },

  getAuditBundle: async (workflowId) => {
    const response = await api.get(`/amip/workflows/${workflowId}/audit`);
    return response.data;
  },

  // 5. Human-in-the-Loop (HITL)
  getPendingReviews: async () => {
    const response = await api.get("/amip/reviews/pending");
    return response.data;
  },

  submitOverride: async (workflowId, payload) => {
    const response = await api.post(`/amip/workflows/${workflowId}/override`, payload);
    return response.data;
  },
};

export default amipService;
