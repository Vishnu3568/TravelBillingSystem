import React, { useState } from 'react';
import { LogOut, ArrowLeft, Menu, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { routes } from '../constants/navigation.js';

export default function Header() {
  const { username, logout, role } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isDashboard = 
    location.pathname === '/' || 
    location.pathname.includes('dashboard');

  return (
    <header className="sticky top-0 z-30 flex flex-col">
      {/* Mobile Branding Bar (Shown ONLY on internal pages) */}
      {!isDashboard && (
        <div className="md:hidden bg-black px-5 py-3 border-b border-white/10 flex justify-center">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-cyan-500 flex items-center justify-center text-black font-black text-lg rounded-none shrink-0">
              T
            </div>
            <div>
              <h1 className="text-white font-black text-sm leading-none tracking-tight">Sri Tulja Bhavani</h1>
              <p className="text-cyan-500 font-bold text-[8px] uppercase tracking-wider mt-1">Travels & Logistics</p>
            </div>
          </div>
        </div>
      )}

      {/* Primary Header Controls */}
      <div className="flex items-center justify-between bg-white/80 backdrop-blur-md border-b border-slate-200 px-5 py-3 md:px-8">
        <div className="flex items-center gap-4">
          {isDashboard ? (
            /* Brand Logo for Home Page (Shown on mobile, hidden when sidebar appears) */
            <div className="flex items-center gap-3 md:hidden">
              <div className="w-8 h-8 bg-cyan-500 flex items-center justify-center text-black font-black text-sm rounded-none shrink-0">
                T
              </div>
              <div className="hidden min-[400px]:block">
                <h1 className="text-black font-black text-sm leading-none tracking-tight">Sri Tulja Bhavani</h1>
                <p className="text-cyan-600 font-bold text-[8px] uppercase tracking-wider mt-0.5">Travels & Logistics</p>
              </div>
            </div>
          ) : (
            /* Back Button for internal pages */
            <button 
              onClick={() => navigate(-1)}
              className="flex items-center gap-2 text-black hover:text-cyan-600 transition-colors font-black uppercase tracking-widest text-[11px] group"
            >
              <ArrowLeft size={16} strokeWidth={3} className="group-hover:-translate-x-1 transition-transform" />
              Back
            </button>
          )}
        </div>

        <div className="md:hidden absolute left-1/2 -translate-x-1/2 flex justify-center">
          <button 
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="p-2 text-black hover:text-cyan-600 transition-colors"
          >
            {isMenuOpen ? <X size={28} strokeWidth={3} /> : <Menu size={28} strokeWidth={3} />}
          </button>

          {/* Mobile Menu Dropdown */}
          {isMenuOpen && (
            <div className="absolute top-[120%] left-1/2 -translate-x-1/2 w-64 bg-black border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,229,255,1)] p-2 animate-in zoom-in-95 duration-200">
              <ul className="space-y-1">
                {routes
                  .filter(r => !r.roles || r.roles.includes(role))
                  .map(route => (
                    <li key={route.to}>
                      <Link
                        to={route.to}
                        onClick={() => setIsMenuOpen(false)}
                        className={`flex items-center gap-3 px-4 py-3 font-bold uppercase tracking-widest text-[10px] transition-all ${
                          location.pathname === route.to 
                            ? 'bg-cyan-500 text-black' 
                            : 'text-white hover:bg-slate-900 hover:text-cyan-500'
                        }`}
                      >
                        <route.icon size={14} strokeWidth={3} />
                        {route.label}
                      </Link>
                    </li>
                  ))}
              </ul>
            </div>
          )}
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-xs font-bold text-black leading-none">{username}</p>
              <p className="text-[10px] text-slate-400 font-medium mt-1 uppercase tracking-wider hidden sm:block">Administrator</p>
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
      </div>
    </header>
  );
}
