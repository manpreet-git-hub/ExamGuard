// src/pages/LiveMonitorPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Activity, AlertTriangle, Users, Shield, Loader2, WifiOff, RefreshCw } from 'lucide-react';
import Layout from '../components/shared/Layout';
import api, { getWsUrl } from '../utils/api';
import { parseApiDate } from '../utils/datetime';

function StudentCard({ student }) {
  const score = student.integrity_score ?? 100;
  const border = score >= 80 ? 'border-gray-700' : score >= 50 ? 'border-amber-500' : 'border-red-500';
  const bg     = score >= 80 ? '' : score >= 50 ? 'bg-amber-500/5' : 'bg-red-500/5';
  const color  = score >= 80 ? 'text-emerald-400' : score >= 50 ? 'text-amber-400' : 'text-red-400';
  const barColor = score >= 80 ? 'bg-emerald-500' : score >= 50 ? 'bg-amber-500' : 'bg-red-500';
  const lastSeen = student.last_violation_at
    ? parseApiDate(student.last_violation_at)?.toLocaleTimeString()
    : null;

  return (
    <div className={`card border-2 ${border} ${bg} p-3 transition-all duration-500`}>
      <div className="aspect-video bg-gray-800 rounded-lg mb-3 flex items-center justify-center relative overflow-hidden">
        <div className="text-center">
          <Users size={20} className="text-gray-700 mx-auto mb-1" />
          <p className="text-xs text-gray-600">{student.is_active ? 'Realtime telemetry' : 'Latest snapshot'}</p>
        </div>
        {student.last_violation && (
          <div className="absolute bottom-0 left-0 right-0 bg-red-600/80 text-white text-xs px-2 py-1 text-center truncate">
            ⚠ {student.last_violation.replace(/_/g, ' ')}
          </div>
        )}
      </div>

      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-white truncate">{student.student_name}</p>
          <p className="text-xs text-gray-500">{student.violations_count} violation{student.violations_count !== 1 ? 's' : ''}</p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className={`text-sm font-bold ${color}`}>{Math.round(score)}</p>
          <p className="text-xs text-gray-500">Integrity</p>
        </div>
      </div>

      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${barColor} transition-all duration-500`} style={{ width: `${score}%` }} />
      </div>

      <div className="mt-2 flex items-center justify-between">
        <span className={`badge text-xs ${student.is_active ? 'badge-blue' : score >= 80 ? 'badge-green' : score >= 50 ? 'badge-yellow' : 'badge-red'}`}>
          {student.is_active ? 'Active' : score >= 80 ? 'Low Risk' : score >= 50 ? 'Medium Risk' : 'High Risk'}
        </span>
        <span className="text-xs text-gray-600 font-mono">
          {student.is_submitted && student.percentage != null ? `${student.percentage.toFixed(0)}%` : lastSeen || '—'}
        </span>
      </div>
    </div>
  );
}

export default function LiveMonitorPage() {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [test, setTest]         = useState(null);
  const [students, setStudents] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [socketStatus, setSocketStatus] = useState('connecting');
  const pollRef = useRef(null);
  const socketRef = useRef(null);

  const mergeStudent = (existingStudents, incoming) => {
    const index = existingStudents.findIndex(student => student.student_id === incoming.student_id);
    const base = index >= 0
      ? existingStudents[index]
      : {
          student_id: incoming.student_id,
          student_name: incoming.student_name || `Student ${incoming.student_id}`,
          integrity_score: 100,
          violations_count: 0,
          percentage: null,
          last_violation: null,
          last_violation_at: null,
          is_active: true,
          is_submitted: false,
        };

    const nextStudent = {
      ...base,
      ...incoming,
      violations_count: incoming.violation_type
        ? (base.violations_count || 0) + 1
        : (incoming.violations_count ?? base.violations_count ?? 0),
      last_violation: incoming.violation_type ?? incoming.last_violation ?? base.last_violation,
      last_violation_at: incoming.timestamp ?? incoming.last_violation_at ?? base.last_violation_at,
      is_active: incoming.is_active ?? base.is_active,
      is_submitted: incoming.is_submitted ?? base.is_submitted,
    };

    if (index === -1) {
      return [nextStudent, ...existingStudents];
    }

    const nextStudents = [...existingStudents];
    nextStudents[index] = nextStudent;
    return nextStudents;
  };

  const fetchStudents = async () => {
    try {
      const r = await api.get(`/api/results/test/${testId}/monitor`);
      setTest(r.data.test);
      setStudents(r.data.students || []);
      setLastRefresh(new Date());
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    fetchStudents();
    pollRef.current = setInterval(fetchStudents, 15000);
    return () => clearInterval(pollRef.current);
  }, [testId]);

  useEffect(() => {
    const socket = new WebSocket(getWsUrl(`/ws/teacher/${testId}`));
    socketRef.current = socket;

    socket.addEventListener('open', () => setSocketStatus('live'));
    socket.addEventListener('close', () => setSocketStatus('offline'));
    socket.addEventListener('error', () => setSocketStatus('offline'));
    socket.addEventListener('message', event => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'heartbeat') return;
        setStudents(current => mergeStudent(current, payload));
        setLastRefresh(new Date());
      } catch {}
    });

    return () => {
      socketRef.current = null;
      socket.close();
    };
  }, [testId]);

  const avgIntegrity = students.length
    ? students.reduce((s, x) => s + x.integrity_score, 0) / students.length
    : 100;
  const highRisk = students.filter(s => s.integrity_score < 50).length;
  const activeStudents = students.filter(s => s.is_active).length;

  return (
    <Layout title="Live Monitor">
      <div className="flex items-center gap-2 mb-6 text-sm text-gray-500">
        <button onClick={() => navigate('/')} className="hover:text-white transition-colors flex items-center gap-1">
          <ArrowLeft size={14} /> Dashboard
        </button>
        <span>/</span>
        <span className="text-white">{test?.title || 'Test'}</span>
        <span>/</span>
        <span>Live Monitor</span>
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-4 mb-6 flex-wrap">
        <div className="flex items-center gap-2">
          {socketStatus === 'live' ? <div className="live-dot" /> : <WifiOff size={14} className="text-amber-400" />}
          <span className={`text-xs font-medium ${socketStatus === 'live' ? 'text-emerald-400' : 'text-amber-400'}`}>
            {socketStatus === 'live' ? 'Live websocket connected' : 'Realtime channel offline, using auto-refresh'}
          </span>
        </div>
        {lastRefresh && (
          <span className="text-xs text-gray-600">Last updated: {lastRefresh.toLocaleTimeString()}</span>
        )}
        <button onClick={fetchStudents} className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-white transition-colors ml-auto">
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {[
          { icon: Users,         label: 'Active Students', value: activeStudents,                color: 'text-white' },
          { icon: Shield,        label: 'Avg Integrity',   value: Math.round(avgIntegrity),       color: 'text-brand-400' },
          { icon: AlertTriangle, label: 'High Risk',       value: highRisk,                       color: 'text-red-400' },
        ].map((s, i) => (
          <div key={i} className="card p-4 flex items-center gap-3">
            <s.icon size={18} className={s.color} />
            <div>
              <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 size={28} className="animate-spin text-gray-600" />
        </div>
      ) : students.length === 0 ? (
        <div className="card p-12 text-center">
          <Activity size={28} className="text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No students have joined this exam yet.</p>
          <p className="text-gray-600 text-sm mt-1">Share the test link: <code className="text-brand-400 font-mono">{window.location.origin}/test/{test?.access_code}</code></p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {students
            .sort((a, b) => {
              if (a.is_active !== b.is_active) return a.is_active ? -1 : 1;
              return a.integrity_score - b.integrity_score;
            })
            .map(s => <StudentCard key={s.student_id} student={s} />)}
        </div>
      )}
    </Layout>
  );
}
