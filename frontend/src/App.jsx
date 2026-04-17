import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import TestManagePage from './pages/TestManagePage';
import ResultsPage from './pages/ResultsPage';
import SubmissionDetailPage from './pages/SubmissionDetailPage';
import ExamEntryPage from './pages/ExamEntryPage';
import ExamPage from './pages/ExamPage';
import LiveMonitorPage from './pages/LiveMonitorPage';
import StudentHomePage from './pages/StudentHomePage';
import StudentResultPage from './pages/StudentResultPage';
import NotFoundPage from './pages/NotFoundPage';

function Spinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function RequireTeacher({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'student') return <Navigate to="/student" replace />;
  return children;
}

function RequireStudent({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'student') return <Navigate to="/" replace />;
  return children;
}

function Home() {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'student') return <Navigate to="/student" replace />;
  return <DashboardPage />;
}

function AppRoutes() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/login"    element={user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/register" element={user ? <Navigate to="/" replace /> : <RegisterPage />} />
      <Route path="/" element={<Home />} />
      <Route path="/dashboard" element={<RequireTeacher><DashboardPage /></RequireTeacher>} />
      <Route path="/tests/:testId/manage"                element={<RequireTeacher><TestManagePage /></RequireTeacher>} />
      <Route path="/tests/:testId/results"               element={<RequireTeacher><ResultsPage /></RequireTeacher>} />
      <Route path="/tests/:testId/results/:submissionId" element={<RequireTeacher><SubmissionDetailPage /></RequireTeacher>} />
      <Route path="/tests/:testId/monitor"               element={<RequireTeacher><LiveMonitorPage /></RequireTeacher>} />
      <Route path="/student"                             element={<RequireStudent><StudentHomePage /></RequireStudent>} />
      <Route path="/student/result/:submissionId"        element={<RequireStudent><StudentResultPage /></RequireStudent>} />
      <Route path="/test/:accessCode" element={<ExamEntryPage />} />
      <Route path="/exam/:testId"     element={<RequireStudent><ExamPage /></RequireStudent>} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
        <Toaster position="top-right" toastOptions={{
          style: { background: '#1f2937', color: '#f9fafb', border: '1px solid #374151' },
          success: { iconTheme: { primary: '#10b981', secondary: '#fff' } },
          error:   { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
        }} />
      </BrowserRouter>
    </AuthProvider>
  );
}
