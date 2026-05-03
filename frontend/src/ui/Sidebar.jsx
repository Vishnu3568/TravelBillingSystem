import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Home, Building2, Truck, Users, BarChart2, 
  Database, ClipboardList, Settings, UploadCloud,
  PlusCircle, FileText, Car 
} from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx'; // Adjust import path to your auth context

import { routes } from '../constants/navigation.js';
import AiInsightsSidebar from './AiInsightsSidebar.jsx';

export default function Sidebar() {
  const { role } = useAuth(); // role string like 'OWNER', 'MANAGER', 'EMPLOYEE'
  return (
    <nav className="hidden md:flex flex-col w-64 shrink-0 bg-black text-slate-100 h-screen sticky top-0 p-6 shadow-2xl z-20">
      <div className="mb-10">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-8 h-8 bg-cyan-500 rounded-none flex items-center justify-center">
            <span className="font-bold text-black text-lg">T</span>
          </div>
          <span className="text-xl font-bold tracking-tight">Sri Tulja Bhavani</span>
        </div>
        <p className="text-[10px] uppercase tracking-[0.2em] text-cyan-500/80 font-bold ml-10">Travels & Logistics</p>
      </div>
      <ul className="flex-1 space-y-2">
        {routes
          .filter(r => !r.roles || r.roles.includes(role))
          .map(route => (
            <li key={route.to}>
              <NavLink
                to={route.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-none transition-colors ${
                    isActive ? 'bg-primary/20 text-primary' : 'hover:bg-slate-800'
                  }`
                }
              >
                <route.icon size={18} />
                {route.label}
              </NavLink>
            </li>
          ))}
      </ul>
      
      {role === 'OWNER' && <AiInsightsSidebar />}

      <div className="mt-4 text-xs text-slate-400">
        Logged in as <span className="font-medium">{role}</span>
      </div>
    </nav>
  );
}
