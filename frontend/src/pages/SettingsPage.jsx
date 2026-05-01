import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext.jsx';
import { User, Lock, Trash2, Shield, Bell, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { username, role, logout } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [passwords, setPasswords] = useState({ current: 'admin123', next: '', confirm: '' });

  // Simulate fetching password from DB on mount
  React.useEffect(() => {
    // In a real app, you'd do: api.get('/user/profile').then(...)
    console.log("Fetching password from database... Done.");
  }, []);

  const handlePasswordChange = (e) => {
    e.preventDefault();
    if (!passwords.next || !passwords.confirm) {
      toast.error("Please enter a new password");
      return;
    }
    if (passwords.next !== passwords.confirm) {
      toast.error("Passwords do not match");
      return;
    }
    toast.success("Password updated successfully (Demo Mode)");
    setPasswords({ ...passwords, next: '', confirm: '' });
  };

  const handleDeleteAccount = () => {
    const confirmed = window.confirm("Are you absolutely sure you want to delete your account? This action cannot be undone.");
    if (confirmed) {
      toast.info("Account deletion simulated. Logging out...");
      setTimeout(() => logout(), 1500);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 text-black">
      <div className="mb-10">
        <h1 className="text-4xl font-bold tracking-tight">Settings</h1>
        <p className="mt-2 text-slate-500">Manage your account preferences and security settings.</p>
      </div>

      <div className="space-y-12">
        {/* Profile Section */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-12 border-b border-slate-200">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <User size={20} />
              Profile Information
            </h2>
            <p className="mt-2 text-sm text-slate-500">Update your account's profile information and role visibility.</p>
          </div>
          <div className="md:col-span-2 space-y-6">
            <div>
              <label className="block text-sm font-bold uppercase tracking-wider text-slate-700 mb-2">Username</label>
              <input
                type="text"
                value={username || ''}
                readOnly
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-none font-medium text-slate-500 cursor-not-allowed"
              />
              <p className="mt-2 text-xs text-slate-400">Username cannot be changed in this version.</p>
            </div>
            <div>
              <label className="block text-sm font-bold uppercase tracking-wider text-slate-700 mb-2">Assigned Role</label>
              <div className="inline-block px-3 py-1 bg-black text-white text-xs font-bold tracking-widest uppercase rounded-none">
                {role}
              </div>
            </div>
          </div>
        </section>

        {/* Security Section */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-12 border-b border-slate-200">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Lock size={20} />
              Security
            </h2>
            <p className="mt-2 text-sm text-slate-500">View your current password or set a new one to stay secure.</p>
          </div>
          <div className="md:col-span-2">
            <form onSubmit={handlePasswordChange} className="space-y-8">
              <div className="p-6 bg-slate-50 border border-slate-200 rounded-none">
                <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Current Password</label>
                <div className="flex items-center justify-between">
                  <span className="text-xl font-mono tracking-tighter">
                    {showPassword ? passwords.current : "••••••••••••"}
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="p-2 hover:bg-slate-200 rounded-none transition-colors text-slate-600"
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="text-sm font-bold uppercase tracking-wider text-slate-900 border-b border-slate-200 pb-2">Set New Password</h4>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">New Password</label>
                  <input
                    type="password"
                    value={passwords.next}
                    onChange={(e) => setPasswords({ ...passwords, next: e.target.value })}
                    className="w-full px-4 py-3 border border-slate-300 rounded-none focus:border-black focus:ring-0 transition-all outline-none"
                    placeholder="Enter new password"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">Confirm New Password</label>
                  <input
                    type="password"
                    value={passwords.confirm}
                    onChange={(e) => setPasswords({ ...passwords, confirm: e.target.value })}
                    className="w-full px-4 py-3 border border-slate-300 rounded-none focus:border-black focus:ring-0 transition-all outline-none"
                    placeholder="Repeat new password"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="bg-black text-white px-8 py-3 font-bold uppercase tracking-widest hover:bg-slate-800 transition-colors"
              >
                Update Password
              </button>
            </form>
          </div>
        </section>

        {/* Danger Zone */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h2 className="text-xl font-bold text-red-600 flex items-center gap-2">
              <Trash2 size={20} />
              Danger Zone
            </h2>
            <p className="mt-2 text-sm text-slate-500">Irreversible and destructive actions for your account.</p>
          </div>
          <div className="md:col-span-2">
            <div className="p-6 border border-red-200 bg-red-50 rounded-none">
              <h3 className="font-bold text-red-700 mb-2">Delete Account</h3>
              <p className="text-sm text-red-600 mb-4">
                Once you delete your account, there is no going back. Please be certain.
              </p>
              <button
                onClick={handleDeleteAccount}
                className="bg-red-600 text-white px-6 py-2 font-bold uppercase tracking-widest hover:bg-red-700 transition-colors"
              >
                Delete Account
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
