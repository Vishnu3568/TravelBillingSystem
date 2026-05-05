import React from 'react';
import { Outlet, useLocation, matchPath } from 'react-router-dom';
import Sidebar from './Sidebar.jsx';
import Header from './Header.jsx';
import AiAssistant from './AiAssistant.jsx';
import { useAuth } from '../context/AuthContext.jsx';

export default function MainLayout() {
  const { role } = useAuth();
  const location = useLocation();
  
  // Try to extract billId from routes like /bill-view/:id or /edit-bill/:id
  const match = matchPath({ path: "/bill-view/:id" }, location.pathname) 
             || matchPath({ path: "/edit-bill/:id" }, location.pathname);
  const billId = match?.params?.id;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
      {(role === 'OWNER' || role === 'MANAGER') && <AiAssistant billId={billId} />}
    </div>
  );
}
