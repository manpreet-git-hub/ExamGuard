// src/pages/DashboardPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus, FileText, Users, BarChart2, Pencil, Trash2,
  Copy, Hash, Loader2, Activity, CheckCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import Layout from '../components/shared/Layout';
import CreateTestModal from '../components/teacher/CreateTestModal';
import api from '../utils/api';

function StatCard({ icon: Icon, label, value, color = 'brand' }) {
  const colors = {
    brand: 'bg-brand-500/10 text-brand-400',
    green: 'bg-emerald-500/10 text-emerald-400',
    amber: 'bg-amber-500/10 text-amber-400',
    red:   'bg-red-500/10 text-red-400',
  };
  return (
    <div className="card p-5">
      <div className="flex items-start gap-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${colors[color]}`}>
          <Icon size={20} />
        </div>
        <div>
          <p className="text-2xl font-bold text-white">{value}</p>
          <p className="text-sm text-gray-500 mt-0.5">{label}</p>
        </div>
      </div>
    </div>
  );
}

function TestCard({ test, onDelete, onRefresh }) {
  const navigate = useNavigate();
  const [deleting, setDeleting] = useState(false);

  const copyLink = (e) => {
    e.stopPropagation();
    const link = `${window.location.origin}/test/${test.access_code}`;
    navigator.clipboard.writeText(link);
    toast.success('Test link copied!');
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    if (!confirm(`Delete "${test.title}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await api.delete(`/api/tests/${test.id}`);
      toast.success('Test deleted');
      onRefresh();
    } catch {
      toast.error('Failed to delete test');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="card p-5 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {test.is_active
              ? <span className="badge-green">● Live</span>
              : <span className="badge-gray">Inactive</span>}
          </div>
          <h3 className="font-semibold text-white truncate">{test.title}</h3>
          {test.description && <p className="text-sm text-gray-500 truncate mt-0.5">{test.description}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        {[
          { label: 'Questions',   value: test.question_count  },
          { label: 'Submissions', value: test.submission_count },
          { label: 'Duration',    value: `${test.duration_mins} min` },
          { label: 'Total Marks', value: test.total_marks },
        ].map((s, i) => (
          <div key={i} className="bg-gray-800/50 rounded-lg p-2.5">
            <p className="text-xs text-gray-500">{s.label}</p>
            <p className="text-sm font-semibold text-white">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Access code row */}
      <div className="flex items-center gap-2 p-2 bg-gray-800 rounded-lg mb-4">
        <Hash size={13} className="text-gray-500 flex-shrink-0" />
        <code className="text-xs text-brand-400 font-mono flex-1 tracking-widest">{test.access_code}</code>
        <button onClick={copyLink} className="text-gray-500 hover:text-brand-400 transition-colors" title="Copy test link">
          <Copy size={13} />
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button onClick={() => navigate(`/tests/${test.id}/manage`)} className="btn-secondary flex-1 justify-center text-xs py-2">
          <Pencil size={13} /> Edit
        </button>
        <button onClick={() => navigate(`/tests/${test.id}/results`)} className="btn-secondary flex-1 justify-center text-xs py-2">
          <BarChart2 size={13} /> Results
        </button>
        <button onClick={() => navigate(`/tests/${test.id}/monitor`)} className="btn-secondary px-2 py-2" title="Live Monitor">
          <Activity size={14} className="text-emerald-400" />
        </button>
        <button onClick={handleDelete} disabled={deleting} className="btn-secondary px-2 py-2 hover:text-red-400 hover:border-red-500/30" title="Delete">
          {deleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
        </button>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [tests, setTests]           = useState([]);
  const [loading, setLoading]       = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const navigate = useNavigate();

  const fetchTests = async () => {
    try {
      const r = await api.get('/api/tests/');
      setTests(r.data);
    } catch {
      toast.error('Failed to load tests');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTests(); }, []);

  const stats = {
    total:       tests.length,
    active:      tests.filter(t => t.is_active).length,
    submissions: tests.reduce((s, t) => s + (t.submission_count || 0), 0),
    questions:   tests.reduce((s, t) => s + (t.question_count  || 0), 0),
  };

  return (
    <Layout title="Dashboard">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={FileText}    label="Total Tests"       value={stats.total}       color="brand" />
        <StatCard icon={CheckCircle} label="Active Tests"      value={stats.active}      color="green" />
        <StatCard icon={Users}       label="Total Submissions" value={stats.submissions} color="amber" />
        <StatCard icon={Hash}        label="Total Questions"   value={stats.questions}   color="brand" />
      </div>

      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-semibold text-white">Your Tests</h2>
          <p className="text-sm text-gray-500">{tests.length} test{tests.length !== 1 ? 's' : ''} created</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus size={16} /> New Test
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 size={28} className="animate-spin text-gray-600" />
        </div>
      ) : tests.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="w-12 h-12 rounded-2xl bg-gray-800 flex items-center justify-center mx-auto mb-4">
            <FileText size={22} className="text-gray-600" />
          </div>
          <p className="text-gray-400 font-medium">No tests yet</p>
          <p className="text-gray-600 text-sm mt-1">Create your first test to get started</p>
          <button onClick={() => setShowCreate(true)} className="btn-primary mt-4 mx-auto">
            <Plus size={16} /> Create Test
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {tests.map(t => <TestCard key={t.id} test={t} onRefresh={fetchTests} />)}
        </div>
      )}

      {showCreate && (
        <CreateTestModal
          onClose={() => setShowCreate(false)}
          onCreated={(test) => {
            setShowCreate(false);
            fetchTests();
            navigate(`/tests/${test.id}/manage`);
          }}
        />
      )}
    </Layout>
  );
}
