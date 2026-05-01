import React from 'react';
import { Bell, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import { useNavigate } from 'react-router-dom';

export default function Header() {
  const { username, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="flex items-center justify-between bg-white/80 backdrop-blur-md border-b border-slate-200 px-8 py-3 sticky top-0 z-30">
      <div className="flex items-center gap-4">
         <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-emerald-50 rounded-full text-[10px] font-bold text-emerald-600 border border-emerald-100">
             <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
             SYSTEM ACTIVE
          </div>
      </div>

      <div className="flex items-center gap-6">
        <button className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-all relative">
          <Bell size={20} />
          <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-rose-500 rounded-full border-2 border-white"></span>
        </button>

        <div className="h-6 w-px bg-slate-200"></div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-xs font-bold text-slate-900 leading-none">{username}</p>
            <p className="text-[10px] text-slate-400 font-medium mt-1 uppercase tracking-wider">Administrator</p>
          </div>
          <div className="w-9 h-9 rounded-xl bg-slate-950 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-slate-200">
            {username?.charAt(0).toUpperCase()}
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="p-2 rounded-xl text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
          title="Sign Out"
        >
          <LogOut size={20} />
        </button>
      </div>
    </header>
  );
}
