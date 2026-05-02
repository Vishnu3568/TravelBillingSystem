import React from 'react';
import { LogOut, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import { useNavigate, useLocation } from 'react-router-dom';

export default function Header() {
  const { username, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isDashboard = 
    location.pathname === '/' || 
    location.pathname.includes('dashboard');

  return (
    <header className="flex items-center justify-between bg-white/80 backdrop-blur-md border-b border-slate-200 px-8 py-3 sticky top-0 z-30">
      <div className="flex items-center gap-4">
        {!isDashboard && (
          <button 
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-black hover:text-cyan-600 transition-colors font-black uppercase tracking-widest text-[11px] group"
          >
            <ArrowLeft size={16} strokeWidth={3} className="group-hover:-translate-x-1 transition-transform" />
            Back
          </button>
        )}
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-xs font-bold text-black leading-none">{username}</p>
            <p className="text-[10px] text-slate-400 font-medium mt-1 uppercase tracking-wider">Administrator</p>
          </div>
          <div className="w-9 h-9 rounded-none bg-black flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-slate-200 border border-slate-100">
            {username?.charAt(0).toUpperCase()}
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="p-2 rounded-none text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all border border-transparent hover:border-red-100"
          title="Sign Out"
        >
          <LogOut size={20} />
        </button>
      </div>
    </header>
  );
}
