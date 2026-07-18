import { create } from "zustand";

export interface ToolCall {
  tool: string;
  parameters: Record<string, any>;
}

export interface OperationPreview {
  operation: string;
  risk: string;
  summary: string;
  requires_confirmation: boolean;
  confirmation_token?: string;
  details?: Record<string, any>;
}

export interface OperationResult {
  operation_id: string;
  operation: string;
  status: string;
  summary: string;
  started_at: string;
  finished_at: string;
  data: Record<string, any>;
  undo_supported: boolean;
  undo_metadata?: Record<string, any>;
}

export interface ChatPlanResponse {
  explanation: string;
  steps: ToolCall[];
  previews: OperationPreview[];
  confirmation_token?: string;
}

interface AppState {
  allowedRoots: string[];
  geminiApiKey: string;
  geminiModel: string;
  history: OperationResult[];
  plan: ChatPlanResponse | null;
  loading: boolean;
  error: string | null;

  workspaceFiles: any[];
  loadWorkspaceFiles: () => Promise<void>;
  setSettings: (allowedRoots: string[], geminiApiKey: string, geminiModel: string) => void;
  loadSettings: () => Promise<void>;
  saveSettings: (allowedRoots: string[], geminiApiKey: string, geminiModel: string) => Promise<void>;

  loadHistory: () => Promise<void>;
  generatePlan: (message: string) => Promise<void>;
  executePlan: () => Promise<void>;
  cancelPlan: () => void;
  undoOperation: (operationId: string) => Promise<void>;
}

const API_BASE = "/api";

export const useStore = create<AppState>((set, get) => ({
  allowedRoots: [],
  geminiApiKey: localStorage.getItem("gemini_api_key") || "",
  geminiModel: "gemini-2.5-flash",
  history: [],
  workspaceFiles: [],
  plan: null,
  loading: false,
  error: null,

  loadWorkspaceFiles: async () => {
    try {
      const res = await fetch(`${API_BASE}/workspace/files`);
      if (res.ok) {
        const data = await res.json();
        set({ workspaceFiles: data });
      }
    } catch (err) {
      console.error("Failed to load workspace files:", err);
    }
  },

  setSettings: (allowedRoots, geminiApiKey, geminiModel) => {
    set({ allowedRoots, geminiApiKey, geminiModel });
  },

  loadSettings: async () => {
    try {
      const res = await fetch(`${API_BASE}/settings`);
      if (res.ok) {
        const data = await res.json();
        set({
          allowedRoots: data.allowed_roots,
          geminiModel: data.gemini_model,
        });
        await get().loadWorkspaceFiles();
      }
    } catch (err: any) {
      console.error("Failed to load settings:", err);
    }
  },

  saveSettings: async (allowedRoots, geminiApiKey, geminiModel) => {
    set({ loading: true, error: null });
    try {
      localStorage.setItem("gemini_api_key", geminiApiKey);
      const res = await fetch(`${API_BASE}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          allowed_roots: allowedRoots,
          gemini_api_key: geminiApiKey,
          gemini_model: geminiModel,
        }),
      });
      if (!res.ok) throw new Error("Failed to update settings in backend.");
      const data = await res.json();
      set({
        allowedRoots: data.allowed_roots,
        geminiApiKey,
        geminiModel: data.gemini_model,
        loading: false,
      });
      await get().loadWorkspaceFiles();
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },

  loadHistory: async () => {
    try {
      const res = await fetch(`${API_BASE}/operations/history`);
      if (res.ok) {
        const data = await res.json();
        set({ history: data });
      }
    } catch (err: any) {
      console.error("Failed to load history:", err);
    }
  },

  generatePlan: async (message) => {
    set({ loading: true, error: null, plan: null });
    const { geminiApiKey } = get();
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (geminiApiKey) {
        headers["X-Gemini-API-Key"] = geminiApiKey;
      }
      const res = await fetch(`${API_BASE}/chat/plan`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Planning failed with status ${res.status}`);
      }
      const data = await res.json();
      set({ plan: data, loading: false });
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },

  executePlan: async () => {
    const { plan } = get();
    if (!plan) return;
    set({ loading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/chat/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          steps: plan.steps,
          confirmation_token: plan.confirmation_token,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Execution failed with status ${res.status}`);
      }
      set({ plan: null, loading: false });
      await get().loadHistory();
      await get().loadWorkspaceFiles();
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },

  cancelPlan: () => {
    set({ plan: null, error: null });
  },

  undoOperation: async (operationId) => {
    set({ loading: true, error: null });
    try {
      // Get preview of undo
      const previewRes = await fetch(`${API_BASE}/operations/rename/${operationId}/undo/preview`, {
        method: "POST",
      });
      if (!previewRes.ok) {
        const body = await previewRes.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to generate undo preview.");
      }
      const preview = await previewRes.json();

      // Confirm with user
      if (!confirm(`${preview.summary}\n\nProceed?`)) {
        set({ loading: false });
        return;
      }

      // Execute undo
      const res = await fetch(`${API_BASE}/operations/rename/undo/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operation_id: operationId,
          confirmation_token: preview.confirmation_token,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to execute undo.");
      }
      set({ loading: false });
      await get().loadHistory();
      await get().loadWorkspaceFiles();
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },
}));
