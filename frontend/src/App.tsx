import React, { useEffect, useState } from "react";
import {
  Settings as SettingsIcon,
  Play,
  X,
  Undo2,
  RefreshCw,
  Search,
  FileCode,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  Folder,
  File,
  Terminal,
  Activity,
  Lock,
} from "lucide-react";
import { useStore } from "./store";

interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  children?: FileNode[];
}

function FileExplorerNode({ node, onSelectFile }: { node: FileNode; onSelectFile: (path: string) => void }) {
  const [isOpen, setIsOpen] = useState(true);

  if (node.is_dir) {
    return (
      <div className="pl-3 select-none">
        <div
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center space-x-1.5 py-1 text-muted hover:text-text cursor-pointer transition font-semibold text-[13px]"
        >
          <span className="text-muted/60">
            {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </span>
          <Folder className="w-4 h-4 text-accent/80" />
          <span className="truncate">{node.name}</span>
        </div>
        {isOpen && node.children && (
          <div className="border-l border-line/40 ml-2 pl-1 space-y-0.5">
            {node.children.length === 0 ? (
              <div className="pl-5 py-0.5 text-xs text-muted/50 italic">Empty folder</div>
            ) : (
              node.children.map((child, i) => (
                <FileExplorerNode key={i} node={child} onSelectFile={onSelectFile} />
              ))
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      onClick={() => onSelectFile(node.path)}
      className="pl-5 py-1 flex items-center space-x-1.5 text-muted hover:text-accent cursor-pointer transition text-[12px] font-mono group"
      title="Click to paste path to chat input"
    >
      <File className="w-3.5 h-3.5 text-muted/60 group-hover:text-accent/80" />
      <span className="truncate group-hover:underline">{node.name}</span>
    </div>
  );
}

function App() {
  const {
    allowedRoots,
    geminiApiKey,
    geminiModel,
    history,
    plan,
    workspaceFiles,
    loading,
    error,
    loadSettings,
    saveSettings,
    loadHistory,
    loadWorkspaceFiles,
    generatePlan,
    executePlan,
    cancelPlan,
    undoOperation,
  } = useStore();

  const [inputMessage, setInputMessage] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [settingsRoots, setSettingsRoots] = useState("");
  const [settingsKey, setSettingsKey] = useState("");
  const [settingsModel, setSettingsModel] = useState("gemini-2.5-flash");
  const [expandedStep, setExpandedStep] = useState<number | null>(0);

  useEffect(() => {
    loadSettings();
    loadHistory();
    loadWorkspaceFiles();
  }, []);

  useEffect(() => {
    setSettingsRoots(allowedRoots.join(", "));
    setSettingsKey(geminiApiKey);
    setSettingsModel(geminiModel);
  }, [allowedRoots, geminiApiKey, geminiModel, showSettings]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;
    generatePlan(inputMessage);
    setInputMessage("");
  };

  const handleSelectFile = (filePath: string) => {
    // Append or insert file path into text area
    setInputMessage((prev) => {
      if (!prev) return filePath;
      if (prev.endsWith(" ")) return prev + filePath;
      return prev + " " + filePath;
    });
  };

  const handleSaveSettings = async () => {
    const rootsArray = settingsRoots
      .split(",")
      .map((r) => r.trim())
      .filter((r) => r.length > 0);
    await saveSettings(rootsArray, settingsKey, settingsModel);
    setShowSettings(false);
  };

  const getRiskBadgeColor = (risk: string) => {
    switch (risk) {
      case "read_only":
        return "bg-teal-500/10 text-teal-300 border-teal-500/30";
      case "reversible":
        return "bg-amber-500/10 text-amber-300 border-amber-500/30";
      case "external":
        return "bg-indigo-500/10 text-indigo-300 border-indigo-500/30";
      case "destructive":
        return "bg-rose-500/10 text-rose-300 border-rose-500/30";
      default:
        return "bg-gray-500/10 text-gray-300 border-gray-500/30";
    }
  };

  const getToolIcon = (tool: string) => {
    if (tool.includes("search") || tool.includes("duplicate")) return <Search className="w-4 h-4" />;
    if (tool.includes("project") || tool.includes("readme") || tool.includes("git")) return <FileCode className="w-4 h-4" />;
    return <Folder className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen text-text flex flex-col antialiased">
      {/* Header */}
      <header className="border-b border-line/45 bg-panel/30 backdrop-blur-xl sticky top-0 z-30 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-accent/15 p-2 rounded-xl border border-accent/25 text-accent shadow-[0_0_15px_-3px_rgba(102,227,186,0.2)]">
            <ShieldCheck className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-text via-text to-accent bg-clip-text text-transparent">
              AI OS Assistant
            </h1>
            <p className="text-xs text-muted flex items-center space-x-1">
              <Lock className="w-3 h-3 text-accent" />
              <span>Safe Natural Language Interface</span>
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowSettings(true)}
            className="p-2 text-muted hover:text-text bg-panel/40 hover:bg-line/40 border border-line/50 rounded-xl transition shadow-inner"
            title="Settings"
          >
            <SettingsIcon className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">

        {/* Column 1: Workspace File Explorer */}
        <section className="lg:col-span-3 flex flex-col h-[calc(100vh-120px)]">
          <div className="glass-panel rounded-2xl p-5 flex-1 flex flex-col overflow-hidden shadow-2xl">
            <div className="flex justify-between items-center border-b border-line/40 pb-3 mb-4">
              <h2 className="text-md font-semibold tracking-wide flex items-center space-x-2 text-muted uppercase">
                <Terminal className="w-4 h-4 text-accent" />
                <span>Workspace Explorer</span>
              </h2>
              <button
                onClick={loadWorkspaceFiles}
                className="text-muted hover:text-accent p-1 hover:bg-line/25 rounded-lg transition"
                title="Refresh Workspace Explorer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-1 pr-1">
              {workspaceFiles.length === 0 ? (
                <div className="text-center text-muted/60 text-xs py-12 italic border border-dashed border-line/30 rounded-xl bg-bg/10">
                  No roots mapped. Go to settings.
                </div>
              ) : (
                workspaceFiles.map((root, i) => (
                  <FileExplorerNode key={i} node={root} onSelectFile={handleSelectFile} />
                ))
              )}
            </div>
          </div>
        </section>


        {/* Column 2: Planner (Chat & execution timeline) */}
        <section className="lg:col-span-5 flex flex-col space-y-6 h-[calc(100vh-120px)] overflow-y-auto pr-1">
          {/* Chat Panel */}
          <div className="glass-panel rounded-2xl p-5 shadow-2xl relative overflow-hidden">
            <h2 className="text-md font-semibold tracking-wide flex items-center space-x-2 mb-3 text-muted uppercase">
              <Activity className="w-4 h-4 text-accent" />
              <span>Ask Assistant</span>
            </h2>
            <form onSubmit={handleSend} className="space-y-3">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="e.g., rename draft.txt to final.txt or scaffold a React project..."
                className="w-full bg-bg/70 border border-line/50 focus:border-accent focus:ring-1 focus:ring-accent outline-none text-text p-3.5 rounded-xl min-h-[95px] resize-none placeholder-muted/65 text-sm transition"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend(e);
                  }
                }}
              />
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted/60">💡 Click explorer files to paste their paths.</span>
                <button
                  type="submit"
                  disabled={loading || !inputMessage.trim()}
                  className="bg-accent hover:bg-accent/90 disabled:opacity-50 text-bg font-bold px-4 py-2 rounded-xl text-sm transition flex items-center space-x-2 shadow-[0_0_15px_-3px_rgba(102,227,186,0.4)]"
                >
                  {loading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <span>Plan workflow</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Workflow Timeline Nodes */}
          {plan && (
            <div className="glass-panel rounded-2xl p-5 shadow-2xl flex flex-col space-y-4 animate-fadeIn">
              <div className="flex justify-between items-center border-b border-line/40 pb-3">
                <div>
                  <h3 className="font-semibold text-lg text-accent">Proposed Workflow Plan</h3>
                  <p className="text-xs text-muted mt-1 leading-relaxed">{plan.explanation}</p>
                </div>
                <button
                  onClick={cancelPlan}
                  className="text-muted hover:text-text p-1 hover:bg-line/25 rounded-lg transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Steps Graph/Timeline */}
              <div className="relative pl-6 border-l border-line/50 ml-3 space-y-6 my-4">
                {plan.steps.map((step, idx) => {
                  const preview = plan.previews[idx];
                  const isExpanded = expandedStep === idx;

                  return (
                    <div key={idx} className="relative group">
                      {/* Timeline Dot Indicator */}
                      <span className="absolute -left-[31px] top-1 bg-panel border-2 border-accent w-4 h-4 rounded-full flex items-center justify-center group-hover:scale-110 transition shadow-[0_0_8px_rgba(102,227,186,0.6)]" />

                      <div className="border border-line/50 rounded-xl bg-bg/40 overflow-hidden text-sm transition hover:border-line">
                        <div
                          onClick={() => setExpandedStep(isExpanded ? null : idx)}
                          className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-line/10 transition"
                        >
                          <div className="flex items-center space-x-3">
                            <span className="bg-line/60 px-2 py-0.5 rounded text-xs font-mono text-accent">
                              Step {idx + 1}
                            </span>
                            <span className="text-text flex items-center space-x-1.5 font-bold">
                              {getToolIcon(step.tool)}
                              <span>{step.tool}</span>
                            </span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span
                              className={`border text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full ${getRiskBadgeColor(
                                preview?.risk || "reversible"
                              )}`}
                            >
                              {preview?.risk || "reversible"}
                            </span>
                            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="p-4 border-t border-line/45 bg-panel/20 space-y-3">
                            <p className="text-muted/90 font-medium text-xs leading-relaxed">
                              {preview?.summary}
                            </p>
                            <div className="bg-bg/80 border border-line/40 p-3 rounded-lg font-mono text-xs overflow-x-auto shadow-inner">
                              <span className="text-muted/50">// Parameters</span>
                              <pre className="text-accent/90 mt-1.5 leading-relaxed">
                                {JSON.stringify(step.parameters, null, 2)}
                              </pre>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Execution Actions */}
              <div className="flex space-x-3 border-t border-line/40 pt-3.5 mt-2">
                <button
                  onClick={executePlan}
                  disabled={loading}
                  className="flex-1 bg-accent hover:bg-accent/90 disabled:opacity-50 text-bg font-bold py-3 rounded-xl transition flex items-center justify-center space-x-2 shadow-[0_4px_20px_-3px_rgba(102,227,186,0.3)]"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>Confirm and Execute</span>
                </button>
                <button
                  onClick={cancelPlan}
                  className="bg-line/40 hover:bg-line/60 text-text font-semibold px-5 py-3 rounded-xl transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-danger/10 border border-danger/25 text-danger rounded-2xl p-4 text-sm animate-shake">
              <span className="font-semibold">Workflow Error:</span> {error}
            </div>
          )}
        </section>

        {/* Column 3: Terminal Journal Log */}
        <section className="lg:col-span-4 flex flex-col h-[calc(100vh-120px)]">
          <div className="glass-panel rounded-2xl p-5 shadow-2xl flex-1 flex flex-col overflow-hidden">
            <div className="flex justify-between items-center border-b border-line/40 pb-3 mb-4">
              <h2 className="text-md font-semibold tracking-wide flex items-center space-x-2 text-muted uppercase">
                <Activity className="w-4 h-4 text-accent" />
                <span>Operation Journal</span>
              </h2>
              <button
                onClick={loadHistory}
                className="text-muted hover:text-accent p-1 hover:bg-line/25 rounded-lg transition"
                title="Refresh History"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3.5 pr-1">
              {history.length === 0 ? (
                <div className="text-center text-muted/50 text-xs py-16 italic border border-dashed border-line/30 rounded-xl bg-bg/10">
                  No operations logged yet.
                </div>
              ) : (
                history.map((op) => (
                  <div
                    key={op.operation_id}
                    className="border border-line/40 rounded-xl bg-bg/25 p-3.5 flex flex-col justify-between hover:bg-line/10 transition space-y-3 relative group"
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-bold text-text/95 leading-snug">{op.summary}</span>
                      <span className="text-[10px] text-muted/60 whitespace-nowrap ml-3 font-mono mt-0.5">
                        {new Date(op.finished_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <div className="flex justify-between items-center text-xs mt-1 border-t border-line/20 pt-2">
                      <span className="text-accent/65 font-mono text-[11px] bg-line/25 px-2 py-0.5 rounded">
                        {op.operation}
                      </span>
                      {op.undo_supported && (
                        <button
                          onClick={() => undoOperation(op.operation_id)}
                          className="flex items-center space-x-1 border border-danger/45 hover:bg-danger/15 hover:border-danger/60 text-danger px-2.5 py-1 rounded-lg transition text-[11px] font-bold"
                        >
                          <Undo2 className="w-3 h-3" />
                          <span>Undo</span>
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </main>

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-bg/80 backdrop-blur-md animate-fadeIn">
          <div className="glass-panel rounded-2xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col border border-line">
            <div className="px-6 py-4 border-b border-line/40 flex justify-between items-center bg-panel/30">
              <h3 className="text-lg font-semibold tracking-wide">Assistant Settings</h3>
              <button
                onClick={() => setShowSettings(false)}
                className="text-muted hover:text-text transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4 flex-1">
              <div>
                <label className="block text-xs font-bold text-muted/80 uppercase tracking-wider mb-2">
                  Allowed Roots (comma-separated paths)
                </label>
                <input
                  type="text"
                  value={settingsRoots}
                  onChange={(e) => setSettingsRoots(e.target.value)}
                  placeholder="/Users/username/Documents, /Users/username/Projects"
                  className="w-full bg-bg/70 border border-line/50 focus:border-accent outline-none text-text p-2.5 rounded-xl text-sm transition"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-muted/80 uppercase tracking-wider mb-2">
                  Gemini API Key
                </label>
                <input
                  type="password"
                  value={settingsKey}
                  onChange={(e) => setSettingsKey(e.target.value)}
                  placeholder="Enter API key"
                  className="w-full bg-bg/70 border border-line/50 focus:border-accent outline-none text-text p-2.5 rounded-xl text-sm transition"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-muted/80 uppercase tracking-wider mb-2">
                  Gemini Model
                </label>
                <select
                  value={settingsModel}
                  onChange={(e) => setSettingsModel(e.target.value)}
                  className="w-full bg-bg/70 border border-line/50 focus:border-accent outline-none text-text p-2.5 rounded-xl text-sm transition"
                >
                  <option value="gemini-2.5-flash">gemini-2.5-flash (Fast & lightweight)</option>
                  <option value="gemini-2.5-pro">gemini-2.5-pro (Precise planning)</option>
                </select>
              </div>
            </div>
            <div className="px-6 py-4 bg-bg/40 border-t border-line/45 flex justify-end space-x-3">
              <button
                onClick={() => setShowSettings(false)}
                className="px-4 py-2.5 bg-line/40 hover:bg-line/60 text-text text-sm font-semibold rounded-xl transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSettings}
                className="px-4 py-2.5 bg-accent hover:bg-accent/90 text-bg text-sm font-bold rounded-xl transition shadow-[0_0_15px_-3px_rgba(102,227,186,0.3)]"
              >
                Save Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
