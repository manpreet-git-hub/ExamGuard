// src/components/shared/Layout.jsx
import React, { useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  ShieldCheck, LayoutDashboard, LogOut,
  Menu, X, User, FileText, BarChart2, Activity, ChevronRight
} from 'lucide-react';

export default function Layout({ children, title }) {
  const { user, logout } = useAuth();
  const location         = useLocation();
  const navigate         = useNavigate();
  const params           = useParams();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => { logout(); navigate('/login'); };

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  // Dynamic nav — add test sub-pages when inside a test
  const testId = params.testId;
  const baseNav = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  ];
  const testNav = testId ? [
    { to: `/tests/${testId}/manage`,  icon: FileText,   label: 'Questions' },
    { to: `/tests/${testId}/results`, icon: BarChart2,  label: 'Results'   },
    { to: `/tests/${testId}/monitor`, icon: Activity,   label: 'Monitor'   },
  ] : [];
  const navItems = [...baseNav, ...testNav];

  const SidebarContent = ({ mobile = false }) => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-gray-800 flex-shrink-0">
        <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center flex-shrink-0">
          <ShieldCheck size={18} className="text-white" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-bold text-white">ExamGuard</p>
          <p className="text-xs text-gray-500">AI Proctoring</p>
        </div>
        {mobile && (
          <button onClick={() => setSidebarOpen(false)} className="ml-auto text-gray-400 hover:text-white flex-shrink-0">
            <X size={20} />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label, exact }) => {
          const active = exact ? location.pathname === to : isActive(to);
          return (
            <Link key={to} to={to} onClick={() => setSidebarOpen(false)}
              className={`sidebar-link ${active ? 'active' : ''}`}>
              <Icon size={17} />
              <span>{label}</span>
            </Link>
          );
        })}

        {testId && testNav.length > 0 && (
          <div className="pt-2 mt-2 border-t border-gray-800">
            <p className="text-xs text-gray-600 px-3 pb-1 uppercase tracking-wider">Current Test</p>
          </div>
        )}
      </nav>

      {/* User */}
      <div className="p-3 border-t border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-gray-800/50">
          <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center flex-shrink-0">
            <User size={14} className="text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
            <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
          </div>
          <button onClick={handleLogout}
            className="text-gray-500 hover:text-red-400 transition-colors flex-shrink-0" title="Logout">
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-950 flex">
      {/* Desktop sidebar */}
      <aside className="hidden lg:block w-56 flex-shrink-0 bg-gray-900 border-r border-gray-800">
        <SidebarContent />
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-56 bg-gray-900 border-r border-gray-800">
            <SidebarContent mobile />
          </aside>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-gray-900/80 backdrop-blur border-b border-gray-800 px-4 lg:px-6 py-3 flex items-center gap-3 sticky top-0 z-30">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-gray-400 hover:text-white transition-colors">
            <Menu size={20} />
          </button>
          {title && <h1 className="text-base font-semibold text-white">{title}</h1>}
        </header>
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
