// src/pages/StudentHomePage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  ShieldCheck, LogOut, FileText, Clock, CheckCircle, XCircle,
  ChevronRight, Hash, Send, Loader2, BookOpen, Award, AlertTriangle,
  User, BarChart2, TrendingUp, Shield
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../utils/api';
import { format } from 'date-fns';
import { parseApiDate } from '../utils/datetime';

function StatCard({ icon: Icon, label, value, color = 'brand' }) {
  const colors = {
    brand: 'bg-brand-500/10 text-brand-400',
    green: 'bg-emerald-500/10 text-emerald-400',
    amber: 'bg-amber-500/10 text-amber-400',
    red:   'bg-red-500/10 text-red-400',
  };
  return (
    <div className="card p-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${colors[color]}`}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </div>
  );
}

export default function StudentHomePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading]         = useState(true);
  const [accessCode, setAccessCode]   = useState('');
  const [joining, setJoining]         = useState(false);

  useEffect(() => {
    api.get('/api/student/submissions')
      .then(r => setSubmissions(r.data))
      .catch(() => setSubmissions([]))
      .finally(() => setLoading(false));
  }, []);

  const handleJoinTest = async (e) => {
    e.preventDefault();
    if (!accessCode.trim()) return;
    setJoining(true);
    try {
      await api.get(`/api/tests/code/${accessCode.toUpperCase()}`);
      navigate(`/test/${accessCode.toUpperCase()}`);
    } catch {
      toast.error('Test not found. Check the access code and try again.');
    } finally {
      setJoining(false);
    }
  };

  const handleLogout = () => { logout(); navigate('/login'); };

  const passed   = submissions.filter(s => s.passed).length;
  const avgScore = submissions.length
    ? Math.round(submissions.reduce((s, x) => s + x.percentage, 0) / submissions.length)
    : 0;
  const avgIntegrity = submissions.length
    ? Math.round(submissions.reduce((s, x) => s + x.integrity_score, 0) / submissions.length)
    : 100;

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 lg:px-8 py-4 flex items-center gap-4 sticky top-0 z-30">
        <div className="flex items-center gap-3 flex-1">
          <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center">
            <ShieldCheck size={18} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">ExamGuard</p>
            <p className="text-xs text-gray-500">Student Portal</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800">
            <div className="w-6 h-6 rounded-full bg-brand-600 flex items-center justify-center">
              <User size={12} className="text-white" />
            </div>
            <span className="text-sm text-white">{user?.full_name}</span>
            <span className="badge-blue text-xs">Student</span>
          </div>
          <button onClick={handleLogout} className="btn-secondary text-xs py-1.5">
            <LogOut size={13} /> Logout
          </button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Welcome */}
        <div>
          <h1 className="text-2xl font-bold text-white">
            Welcome back, {user?.full_name?.split(' ')[0]}! 👋
          </h1>
          <p className="text-gray-500 mt-1">Enter an access code to start a test, or review your past results.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard icon={FileText}    label="Tests Taken"  value={submissions.length} color="brand" />
          <StatCard icon={CheckCircle} label="Passed"       value={passed}             color="green" />
          <StatCard icon={TrendingUp}  label="Avg Score"    value={`${avgScore}%`}     color="amber" />
          <StatCard icon={Shield}      label="Avg Integrity" value={avgIntegrity}      color={avgIntegrity >= 80 ? 'green' : avgIntegrity >= 50 ? 'amber' : 'red'} />
        </div>

        {/* Join Test Card */}
        <div className="card p-6">
          <h2 className="text-base font-semibold text-white mb-1 flex items-center gap-2">
            <Hash size={16} className="text-brand-400" /> Enter Test Access Code
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            Get the access code from your teacher or exam invitation link.
          </p>
          <form onSubmit={handleJoinTest} className="flex gap-3">
            <input
              className="input flex-1 uppercase tracking-widest font-mono text-lg text-brand-400 placeholder:normal-case placeholder:tracking-normal placeholder:font-sans placeholder:text-gray-500 placeholder:text-sm"
              placeholder="e.g. ABC12345"
              value={accessCode}
              onChange={e => setAccessCode(e.target.value.toUpperCase())}
              maxLength={12}
            />
            <button type="submit" disabled={joining || !accessCode.trim()} className="btn-primary px-6 py-2.5">
              {joining ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
              {joining ? 'Checking…' : 'Join Test'}
            </button>
          </form>
        </div>

        {/* Past Submissions */}
        <div>
          <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <BookOpen size={16} className="text-brand-400" /> Your Exam History
          </h2>

          {loading ? (
            <div className="card p-10 flex items-center justify-center">
              <Loader2 size={24} className="animate-spin text-gray-600" />
            </div>
          ) : submissions.length === 0 ? (
            <div className="card p-12 text-center">
              <div className="w-12 h-12 rounded-2xl bg-gray-800 flex items-center justify-center mx-auto mb-4">
                <FileText size={22} className="text-gray-600" />
              </div>
              <p className="text-gray-400 font-medium">No exams taken yet</p>
              <p className="text-gray-600 text-sm mt-1">Enter an access code above to take your first exam.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {submissions.map(sub => (
                <div key={sub.id} className="card p-4 flex items-center gap-4 hover:border-gray-700 transition-colors cursor-pointer"
                  onClick={() => navigate(`/student/result/${sub.id}`)}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${sub.passed ? 'bg-emerald-500/10' : 'bg-red-500/10'}`}>
                    {sub.passed
                      ? <CheckCircle size={20} className="text-emerald-400" />
                      : <XCircle    size={20} className="text-red-400" />}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-white truncate">{sub.test_title || 'Exam'}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {sub.submitted_at ? format(parseApiDate(sub.submitted_at), 'dd MMM yyyy, HH:mm') : 'In progress'}
                    </p>
                  </div>

                  <div className="flex items-center gap-4 flex-shrink-0">
                    <div className="text-right hidden sm:block">
                      <p className="text-sm font-bold text-white">{sub.score}/{sub.max_score}</p>
                      <p className="text-xs text-gray-500">{sub.percentage?.toFixed(1)}%</p>
                    </div>
                    <div className="text-right hidden md:block">
                      <p className={`text-sm font-bold ${sub.integrity_score >= 80 ? 'text-emerald-400' : sub.integrity_score >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                        {Math.round(sub.integrity_score)}
                      </p>
                      <p className="text-xs text-gray-500">Integrity</p>
                    </div>
                    <span className={`badge text-xs ${sub.risk_level === 'Low' ? 'badge-green' : sub.risk_level === 'Medium' ? 'badge-yellow' : 'badge-red'}`}>
                      {sub.risk_level}
                    </span>
                    <ChevronRight size={16} className="text-gray-600" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
