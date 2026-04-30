import React from 'react';
import { Bell, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx'; // adjust path if needed
import { useNavigate } from 'react-router-dom';

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="flex items-center justify-between bg-white shadow-sm px-4 py-2 sticky top-0 z-10">
      <h1 className="text-xl font-semibold text-slate-800">Sri Tulja Bhavani Travels</h1>
      <div className="flex items-center gap-4">
        <button className="p-2 rounded-full hover:bg-slate-100">
          <Bell size={20} className="text-slate-600" />
        </button>
        <div className="flex items-center gap-2">
          <User size={20} className="text-slate-600" />
          <span className="text-sm font-medium text-slate-700">{user?.username}</span>
        </div>
        <button
          onClick={handleLogout}
          className="px-3 py-1 bg-primary text-white rounded hover:bg-primary/80 transition"
        >
          Logout
        </button>
      </div>
    </header>
  );
}
