import React, { useEffect, useState, useRef } from "react";
import { 
  Database, 
  Download, 
  Upload, 
  Trash2, 
  RefreshCw, 
  History, 
  HardDrive,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Clock
} from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

const BackupPage = () => {
  const { role } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState({ text: "", type: "" });
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await api.get("/backup/history");
      setHistory(response.data);
    } catch (err) {
      console.error(err);
      setMessage({ text: "Failed to load backup history.", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBackup = async () => {
    try {
      setActionLoading(true);
      const response = await api.post("/backup/create");
      setMessage({ text: response.data, type: "success" });
      fetchHistory();
    } catch (err) {
      setMessage({ text: err.response?.data || "Backup creation failed.", type: "error" });
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownload = async (fileName) => {
    try {
      const response = await api.get(`/backup/download/${fileName}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("Download failed");
    }
  };

  const handleRestore = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!window.confirm("WARNING: Restoring will overwrite the current database. All data created after this backup will be lost. Proceed?")) {
      e.target.value = null;
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setActionLoading(true);
      const response = await api.post("/backup/restore", formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setMessage({ text: response.data, type: "success" });
      e.target.value = null;
    } catch (err) {
      setMessage({ text: err.response?.data || "Restore failed.", type: "error" });
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async (fileName) => {
    if (!window.confirm(`Delete backup ${fileName}?`)) return;

    try {
      await api.delete(`/backup/${fileName}`);
      fetchHistory();
    } catch (err) {
      alert("Deletion failed");
    }
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (role !== "OWNER") {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 p-6">
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 text-center max-w-md">
          <AlertTriangle className="mx-auto text-red-500 mb-4" size={48} />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Access Denied</h2>
          <p className="text-slate-500">Backup and Restore tools are restricted to OWNER accounts only.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-slate-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <Database className="text-indigo-600" size={32} />
            Backup & Restore
          </h1>
          <p className="text-slate-500 mt-2">Maintain system integrity with database snapshots</p>
        </div>

        {message.text && (
          <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-300 ${
            message.type === "success" ? "bg-emerald-50 text-emerald-700 border border-emerald-100" : "bg-red-50 text-red-700 border border-red-100"
          }`}>
            {message.type === "success" ? <CheckCircle2 size={20} /> : <AlertTriangle size={20} />}
            <span className="font-medium">{message.text}</span>
            <button onClick={() => setMessage({text: "", type: ""})} className="ml-auto hover:opacity-70">&times;</button>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col items-center text-center group hover:border-indigo-200 transition-colors">
            <div className="p-4 rounded-2xl bg-indigo-50 text-indigo-600 mb-4 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
              <HardDrive size={40} />
            </div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">Create Instant Backup</h2>
            <p className="text-slate-500 mb-6 max-w-xs text-sm leading-relaxed">
              Generate a full snapshot of the database including all bills, users, companies, and vehicles.
            </p>
            <button 
              disabled={actionLoading}
              onClick={handleCreateBackup}
              className="w-full bg-indigo-600 text-white px-6 py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {actionLoading ? <Loader2 className="animate-spin" size={20} /> : <RefreshCw size={20} />}
              Start Backup Process
            </button>
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col items-center text-center group hover:border-amber-200 transition-colors">
            <div className="p-4 rounded-2xl bg-amber-50 text-amber-600 mb-4 group-hover:bg-amber-600 group-hover:text-white transition-colors">
              <Upload size={40} />
            </div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">Restore from File</h2>
            <p className="text-slate-500 mb-6 max-w-xs text-sm leading-relaxed">
              Upload a previously downloaded .sql file to restore the database state.
            </p>
            <input 
              type="file" 
              className="hidden" 
              ref={fileInputRef}
              accept=".sql"
              onChange={handleRestore}
            />
            <button 
              disabled={actionLoading}
              onClick={() => fileInputRef.current.click()}
              className="w-full bg-amber-600 text-white px-6 py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-amber-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {actionLoading ? <Loader2 className="animate-spin" size={20} /> : <Database size={20} />}
              Upload & Restore
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
            <h3 className="font-bold text-slate-800 flex items-center gap-2">
              <History size={18} />
              Recent Backup History
            </h3>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest bg-slate-100 px-2 py-1 rounded">
              Local Storage
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs font-bold tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-4">Backup Name</th>
                  <th className="px-6 py-4">Date & Time</th>
                  <th className="px-6 py-4">File Size</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan="4" className="px-6 py-12 text-center">
                      <Loader2 className="animate-spin mx-auto text-indigo-600 mb-2" size={32} />
                      <p className="text-slate-500 font-medium">Scanning backup directory...</p>
                    </td>
                  </tr>
                ) : history.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="px-6 py-12 text-center text-slate-500">
                      No backups found in local storage.
                    </td>
                  </tr>
                ) : (
                  history.map((item) => (
                    <tr key={item.fileName} className="hover:bg-slate-50 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3 font-medium text-slate-900">
                          <FileText className="text-slate-400" size={20} />
                          {item.fileName}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-sm">
                        <div className="flex items-center gap-2">
                          <Clock size={14} />
                          {new Date(item.createdAt).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-600 font-semibold text-sm">
                        {formatSize(item.fileSize)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button 
                            onClick={() => handleDownload(item.fileName)}
                            className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition"
                            title="Download SQL"
                          >
                            <Download size={18} />
                          </button>
                          <button 
                            onClick={() => handleDelete(item.fileName)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                            title="Delete"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackupPage;
