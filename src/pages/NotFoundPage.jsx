// src/pages/NotFoundPage.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ShieldCheck, ArrowLeft, Home } from 'lucide-react';

export default function NotFoundPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const goHome = () => {
    if (!user) navigate('/login');
    else if (user.role === 'student') navigate('/student');
    else navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-gradient-to-br from-brand-900/10 via-transparent to-transparent pointer-events-none" />
      <div className="text-center relative">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gray-900 border border-gray-800 mb-8">
          <ShieldCheck size={32} className="text-gray-700" />
        </div>
        <h1 className="text-8xl font-bold text-gray-800 mb-4 tracking-tight">404</h1>
        <p className="text-xl text-gray-400 font-medium mb-2">Page not found</p>
        <p className="text-gray-600 text-sm mb-8 max-w-xs mx-auto">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex items-center gap-3 justify-center">
          <button onClick={() => navigate(-1)} className="btn-secondary">
            <ArrowLeft size={15} /> Go Back
          </button>
          <button onClick={goHome} className="btn-primary">
            <Home size={15} /> Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
