import React, { useEffect, useState } from "react";
import { 
  ClipboardList, 
  Search, 
  Filter, 
  Calendar, 
  User, 
  Activity, 
  Shield, 
  Globe,
  ArrowRight,
  ArrowLeft,
  Loader2,
  AlertCircle,
  Clock
} from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

const AuditLogPage = () => {
  const { role } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [totalElements, setTotalElements] = useState(0);
  
  const [filters, setFilters] = useState({
    username: "",
    action: "",
    startDate: "",
    endDate: ""
  });

  useEffect(() => {
    fetchLogs();
  }, [page]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        size: 20,
        username: filters.username || undefined,
        action: filters.action || undefined,
        startDate: filters.startDate ? filters.startDate + "T00:00:00" : undefined,
        endDate: filters.endDate ? filters.endDate + "T23:59:59" : undefined
      };
      
      const response = await api.get("/audit-logs", { params });
      setLogs(response.data.content);
      setTotalPages(response.data.totalPages);
      setTotalElements(response.data.totalElements);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(0);
    fetchLogs();
  };

  const clearFilters = () => {
    setFilters({ username: "", action: "", startDate: "", endDate: "" });
    setPage(0);
    // fetchLogs will be triggered by the state update if we use a watcher, 
    // but here we just call it manually after state clear
    setTimeout(fetchLogs, 0);
  };

  const getActionColor = (action) => {
    if (action.includes("CREATE")) return "bg-emerald-50 text-emerald-700 border-emerald-100";
    if (action.includes("DELETE")) return "bg-red-50 text-red-700 border-red-100";
    if (action.includes("UPDATE")) return "bg-amber-50 text-amber-700 border-amber-100";
    if (action.includes("LOGIN")) return "bg-indigo-50 text-indigo-700 border-indigo-100";
    if (action.includes("BACKUP") || action.includes("RESTORE")) return "bg-purple-50 text-purple-700 border-purple-100";
    return "bg-slate-50 text-slate-700 border-slate-100";
  };

  if (role !== "OWNER") {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 p-6">
        <div className="bg-white p-8 rounded-none shadow-sm border border-slate-200 text-center max-w-md">
          <AlertCircle className="mx-auto text-red-500 mb-4" size={48} />
          <h2 className="text-2xl font-bold text-black mb-2">Access Denied</h2>
          <p className="text-slate-500">Audit logs are reserved for OWNER accounts only.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-slate-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-black flex items-center gap-3">
              <ClipboardList className="text-indigo-600" size={32} />
              Audit Logs
            </h1>
            <p className="text-slate-500 mt-2">Track every administrative action across the system</p>
          </div>
          <div className="bg-indigo-600/10 text-indigo-700 px-4 py-2 rounded-none border border-indigo-100 flex items-center gap-2 font-semibold">
            <Activity size={18} />
            Total Events: {totalElements}
          </div>
        </div>

        <div className="bg-white p-6 rounded-none shadow-sm border border-slate-200 mb-8">
          <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                <input 
                  type="text"
                  placeholder="Filter by user..."
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                  value={filters.username}
                  onChange={(e) => setFilters({...filters, username: e.target.value})}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700">Action Type</label>
              <select 
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                value={filters.action}
                onChange={(e) => setFilters({...filters, action: e.target.value})}
              >
                <option value="">All Actions</option>
                <option value="LOGIN">LOGIN</option>
                <option value="CREATE_BILL">CREATE_BILL</option>
                <option value="UPDATE_BILL">UPDATE_BILL</option>
                <option value="DELETE_BILL">DELETE_BILL</option>
                <option value="CREATE_USER">CREATE_USER</option>
                <option value="UPDATE_USER">UPDATE_USER</option>
                <option value="RESET_PASSWORD">RESET_PASSWORD</option>
                <option value="BACKUP_CREATED">BACKUP_CREATED</option>
                <option value="RESTORE_DONE">RESTORE_DONE</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700">From Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                <input 
                  type="date"
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                  value={filters.startDate}
                  onChange={(e) => setFilters({...filters, startDate: e.target.value})}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700">To Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                <input 
                  type="date"
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                  value={filters.endDate}
                  onChange={(e) => setFilters({...filters, endDate: e.target.value})}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button 
                type="submit"
                className="flex-1 bg-indigo-600 text-white font-bold py-2 rounded-none hover:bg-indigo-700 transition flex items-center justify-center gap-2"
              >
                <Filter size={18} />
                Filter
              </button>
              <button 
                type="button"
                onClick={clearFilters}
                className="p-2 border border-slate-200 text-slate-500 hover:bg-slate-50 rounded-none transition"
              >
                Reset
              </button>
            </div>
          </form>
        </div>

        <div className="bg-white rounded-none shadow-sm border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs font-bold tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-4 whitespace-nowrap">Timestamp</th>
                  <th className="px-6 py-4">User</th>
                  <th className="px-6 py-4">Action</th>
                  <th className="px-6 py-4">Module</th>
                  <th className="px-6 py-4">Description</th>
                  <th className="px-6 py-4">IP Address</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center">
                      <Loader2 className="animate-spin mx-auto text-indigo-600 mb-2" size={32} />
                      <p className="text-slate-500">Retrieving security logs...</p>
                    </td>
                  </tr>
                ) : logs.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-slate-500">
                      No logs found matching your criteria.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                        <div className="flex flex-col">
                          <span className="font-medium text-black">{new Date(log.createdAt).toLocaleDateString()}</span>
                          <span className="flex items-center gap-1"><Clock size={12}/>{new Date(log.createdAt).toLocaleTimeString()}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-none bg-slate-100 text-slate-600 flex items-center justify-center text-xs font-bold">
                            {log.username.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-bold text-black text-sm">{log.username}</p>
                            <p className="text-xs text-indigo-600 font-semibold">{log.role}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 rounded-none text-[10px] font-bold border ${getActionColor(log.action)}`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-none">
                          {log.module}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-slate-600 max-w-xs">{log.description}</p>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                          <Globe size={14} />
                          {log.ipAddress}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="p-4 border-t border-slate-100 bg-slate-50/30 flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Showing <span className="font-bold text-black">{logs.length}</span> of <span className="font-bold text-black">{totalElements}</span> logs
            </p>
            <div className="flex gap-2">
              <button 
                disabled={page === 0 || loading}
                onClick={() => setPage(p => p - 1)}
                className="p-2 border border-slate-200 rounded-none hover:bg-white transition disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ArrowLeft size={18} />
              </button>
              <div className="flex items-center px-4 text-sm font-bold text-slate-700 bg-white border border-slate-200 rounded-none">
                Page {page + 1} of {totalPages || 1}
              </div>
              <button 
                disabled={page >= totalPages - 1 || loading}
                onClick={() => setPage(p => p + 1)}
                className="p-2 border border-slate-200 rounded-none hover:bg-white transition disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuditLogPage;
