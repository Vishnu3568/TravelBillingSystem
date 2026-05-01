import React, { useEffect, useState } from "react";
import { 
  Users, 
  UserPlus, 
  Search, 
  Shield, 
  Mail, 
  Calendar, 
  MoreVertical, 
  Trash2, 
  Key, 
  UserCheck, 
  UserX,
  Loader2,
  AlertCircle
} from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

const UserManagementPage = () => {
  const { role: currentUserRole } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    fullName: "",
    email: "",
    role: "EMPLOYEE"
  });
  
  const [resetData, setResetData] = useState({ newPassword: "" });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get("/users");
      setUsers(response.data);
    } catch (err) {
      setError("Failed to fetch users. Access restricted to OWNER role.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await api.post("/users", formData);
      setIsModalOpen(false);
      setFormData({ username: "", password: "", fullName: "", email: "", role: "EMPLOYEE" });
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.message || "Error creating user");
    }
  };

  const handleUpdateStatus = async (user) => {
    try {
      await api.put(`/users/${user.id}`, { active: !user.active });
      fetchUsers();
    } catch (err) {
      alert("Error updating user status");
    }
  };

  const handleUpdateRole = async (user, newRole) => {
    try {
      await api.put(`/users/${user.id}`, { role: newRole });
      fetchUsers();
    } catch (err) {
      alert("Error updating user role");
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    try {
      await api.put(`/users/${selectedUser.id}/reset-password`, resetData);
      setIsResetModalOpen(false);
      setResetData({ newPassword: "" });
      alert("Password reset successfully");
    } catch (err) {
      alert("Error resetting password");
    }
  };

  const handleDeleteUser = async (id) => {
    if (window.confirm("Are you sure you want to disable this user?")) {
      try {
        await api.delete(`/users/${id}`);
        fetchUsers();
      } catch (err) {
        alert("Error deleting user");
      }
    }
  };

  const filteredUsers = users.filter(u => 
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    u.fullName.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  if (currentUserRole !== "OWNER") {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 p-6">
        <div className="bg-white p-8 rounded-none shadow-sm border border-slate-200 text-center max-w-md">
          <AlertCircle className="mx-auto text-red-500 mb-4" size={48} />
          <h2 className="text-2xl font-bold text-black mb-2">Access Denied</h2>
          <p className="text-slate-500">This module is reserved for OWNER accounts only. Please contact your administrator if you believe this is an error.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-slate-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-black flex items-center gap-3">
              <Users className="text-indigo-600" size={32} />
              User Management
            </h1>
            <p className="text-slate-500 mt-2">Manage team access, roles, and system security</p>
          </div>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="bg-indigo-600 text-white px-5 py-2.5 rounded-none font-semibold flex items-center gap-2 hover:bg-indigo-700 transition shadow-sm"
          >
            <UserPlus size={20} />
            Create New User
          </button>
        </div>

        <div className="bg-white rounded-none shadow-sm border border-slate-200 overflow-hidden mb-6">
          <div className="p-5 border-b border-slate-100 flex flex-col md:flex-row gap-4 items-center justify-between bg-slate-50/50">
            <div className="relative w-full md:w-96">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text"
                placeholder="Search by username, name or email..."
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="text-sm text-slate-500 font-medium">
              Showing {filteredUsers.length} total users
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50 text-slate-500 uppercase text-xs font-bold tracking-wider">
                <tr>
                  <th className="px-6 py-4">User</th>
                  <th className="px-6 py-4">Role</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Created At</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center">
                      <Loader2 className="animate-spin mx-auto text-indigo-600 mb-2" size={32} />
                      <p className="text-slate-500">Loading user database...</p>
                    </td>
                  </tr>
                ) : filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center text-slate-500">
                      No users found matching your search.
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((user) => (
                    <tr key={user.id} className="hover:bg-slate-50 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-none bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
                            {(user.fullName || user.username).charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-bold text-black">{user.fullName || user.username}</p>
                            <p className="text-sm text-slate-500">@{user.username}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <select 
                          className="bg-transparent border-none text-sm font-semibold text-slate-700 cursor-pointer focus:ring-0 outline-none p-0"
                          value={user.role}
                          onChange={(e) => handleUpdateRole(user, e.target.value)}
                        >
                          <option value="OWNER">OWNER</option>
                          <option value="MANAGER">MANAGER</option>
                          <option value="EMPLOYEE">EMPLOYEE</option>
                        </select>
                      </td>
                      <td className="px-6 py-4">
                        <button 
                          onClick={() => handleUpdateStatus(user)}
                          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-none text-xs font-bold transition ${
                            user.active 
                              ? "bg-emerald-50 text-emerald-700 hover:bg-emerald-100" 
                              : "bg-red-50 text-red-700 hover:bg-red-100"
                          }`}
                        >
                          {user.active ? <UserCheck size={14} /> : <UserX size={14} />}
                          {user.active ? "ACTIVE" : "INACTIVE"}
                        </button>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500">
                        <div className="flex items-center gap-1.5">
                          <Calendar size={14} />
                          {new Date(user.createdAt).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2 transition-opacity">
                          <button 
                            onClick={() => { setSelectedUser(user); setIsResetModalOpen(true); }}
                            className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-none transition"
                            title="Reset Password"
                          >
                            <Key size={18} />
                          </button>
                          <button 
                            onClick={(e) => { e.stopPropagation(); handleDeleteUser(user.id); }}
                            className="p-2 text-red-600 hover:bg-red-100 rounded-none transition"
                            title="Disable User"
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

      {/* Create User Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-none shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-xl font-bold text-black flex items-center gap-2">
                <UserPlus className="text-indigo-600" size={24} />
                Create New User
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition">&times;</button>
            </div>
            <form onSubmit={handleCreateUser} className="p-6 space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-bold text-slate-700">Full Name</label>
                <input 
                  required
                  type="text"
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                  placeholder="John Doe"
                  value={formData.fullName}
                  onChange={(e) => setFormData({...formData, fullName: e.target.value})}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-bold text-slate-700">Username</label>
                  <input 
                    required
                    type="text"
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                    placeholder="johndoe"
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-bold text-slate-700">Role</label>
                  <select 
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                  >
                    <option value="OWNER">OWNER</option>
                    <option value="MANAGER">MANAGER</option>
                    <option value="EMPLOYEE">EMPLOYEE</option>
                  </select>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-bold text-slate-700">Email Address</label>
                <input 
                  required
                  type="email"
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                  placeholder="john@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-bold text-slate-700">Password</label>
                <input 
                  required
                  type="password"
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                  placeholder="Minimum 6 characters"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                />
              </div>
              <div className="pt-4 flex gap-3">
                <button 
                  type="button" 
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 px-4 py-2.5 border border-slate-200 text-slate-600 font-bold rounded-none hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="flex-1 px-4 py-2.5 bg-indigo-600 text-white font-bold rounded-none hover:bg-indigo-700 transition shadow-sm"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reset Password Modal */}
      {isResetModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-none shadow-xl border border-slate-200 w-full max-w-sm overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6 border-b border-slate-100">
              <h3 className="text-xl font-bold text-black flex items-center gap-2">
                <Key className="text-indigo-600" size={24} />
                Reset Password
              </h3>
              <p className="text-sm text-slate-500 mt-1">For user: {selectedUser?.fullName || selectedUser?.username}</p>
            </div>
            <form onSubmit={handleResetPassword} className="p-6 space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-bold text-slate-700">New Password</label>
                <input 
                  required
                  type="password"
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-none outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                  placeholder="Enter new strong password"
                  value={resetData.newPassword}
                  onChange={(e) => setResetData({ newPassword: e.target.value })}
                />
              </div>
              <div className="pt-4 flex gap-3">
                <button 
                  type="button" 
                  onClick={() => setIsResetModalOpen(false)}
                  className="flex-1 px-4 py-2.5 border border-slate-200 text-slate-600 font-bold rounded-none hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="flex-1 px-4 py-2.5 bg-indigo-600 text-white font-bold rounded-none hover:bg-indigo-700 transition shadow-sm"
                >
                  Reset Now
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagementPage;
