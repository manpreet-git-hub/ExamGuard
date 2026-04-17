// src/pages/ResultsPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, ChevronRight, AlertTriangle, CheckCircle, XCircle, Shield } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';
import toast from 'react-hot-toast';
import Layout from '../components/shared/Layout';
import api from '../utils/api';

function RiskBadge({ level }) {
  const map = { Low: 'badge-green', Medium: 'badge-yellow', High: 'badge-red' };
  return <span className={map[level] || 'badge-gray'}>{level || '—'}</span>;
}

export default function ResultsPage() {
  const { testId } = useParams();
  const navigate   = useNavigate();
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [sort, setSort]     = useState({ key: 'percentage', dir: 'desc' });
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.get(`/api/results/test/${testId}`)
      .then(r => setData(r.data))
      .catch(() => toast.error('Failed to load results'))
      .finally(() => setLoading(false));
  }, [testId]);

  if (loading) return (
    <Layout><div className="flex items-center justify-center h-48"><Loader2 size={28} className="animate-spin text-gray-600" /></div></Layout>
  );

  const { test, results = [], stats = {} } = data || {};

  const sorted = [...results]
    .filter(r => (r.student_name + r.student_email).toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      const v = sort.dir === 'asc' ? 1 : -1;
      if (a[sort.key] == null) return 1;
      if (b[sort.key] == null) return -1;
      return a[sort.key] > b[sort.key] ? v : -v;
    });

  const toggleSort = (key) => setSort(s => ({ key, dir: s.key === key && s.dir === 'desc' ? 'asc' : 'desc' }));

  const scoreDistribution = [
    { range: '0–20%',   count: results.filter(r => r.percentage < 20).length   },
    { range: '20–40%',  count: results.filter(r => r.percentage >= 20 && r.percentage < 40).length },
    { range: '40–60%',  count: results.filter(r => r.percentage >= 40 && r.percentage < 60).length },
    { range: '60–80%',  count: results.filter(r => r.percentage >= 60 && r.percentage < 80).length },
    { range: '80–100%', count: results.filter(r => r.percentage >= 80).length  },
  ];

  const riskData = [
    { name: 'Low Risk',    value: results.filter(r => r.risk_level === 'Low').length,    fill: '#10b981' },
    { name: 'Medium Risk', value: results.filter(r => r.risk_level === 'Medium').length, fill: '#f59e0b' },
    { name: 'High Risk',   value: results.filter(r => r.risk_level === 'High').length,   fill: '#ef4444' },
  ].filter(d => d.value > 0);

  const SortTh = ({ k, label }) => (
    <th onClick={() => toggleSort(k)} className="cursor-pointer select-none hover:text-white transition-colors">
      {label} {sort.key === k ? (sort.dir === 'asc' ? '↑' : '↓') : ''}
    </th>
  );

  return (
    <Layout title="Results">
      <div className="flex items-center gap-2 mb-6 text-sm text-gray-500">
        <button onClick={() => navigate('/')} className="hover:text-white transition-colors">Dashboard</button>
        <span>/</span>
        <span className="text-white">{test?.title}</span>
        <span>/</span>
        <span>Results</span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
        {[
          { label: 'Total Students', value: stats.total ?? 0,                             color: 'text-white' },
          { label: 'Passed',         value: stats.passed ?? 0,                            color: 'text-emerald-400' },
          { label: 'Avg Score',      value: `${(stats.avg_score || 0).toFixed(1)}%`,      color: 'text-brand-400' },
          { label: 'Avg Integrity',  value: `${Math.round(stats.avg_integrity || 100)}`,  color: 'text-amber-400' },
          { label: 'High Risk',      value: stats.high_risk ?? 0,                         color: 'text-red-400' },
        ].map((s, i) => (
          <div key={i} className="card p-4">
            <p className="text-xs text-gray-500">{s.label}</p>
            <p className={`text-xl font-bold mt-0.5 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      {results.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <div className="card p-4">
            <p className="text-sm font-semibold text-white mb-4">Score Distribution</p>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={scoreDistribution} barSize={28}>
                <XAxis dataKey="range" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#fff', fontSize: 12 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {scoreDistribution.map((_, i) => <Cell key={i} fill={i < 2 ? '#ef4444' : i < 3 ? '#f59e0b' : '#10b981'} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="card p-4">
            <p className="text-sm font-semibold text-white mb-4">Risk Level Distribution</p>
            {riskData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={riskData} cx="50%" cy="50%" outerRadius={65} dataKey="value" nameKey="name">
                    {riskData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Pie>
                  <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
                  <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[180px] flex items-center justify-center text-gray-600 text-sm">No data yet</div>
            )}
          </div>
        </div>
      )}

      {/* Results table */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <p className="text-sm font-semibold text-white">{results.length} Submission{results.length !== 1 ? 's' : ''}</p>
          <input className="input w-56 py-1.5 text-xs" placeholder="Search students…"
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>

        {results.length === 0 ? (
          <div className="p-12 text-center text-gray-600 text-sm">No submissions yet for this test.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <SortTh k="student_name" label="Student" />
                  <SortTh k="score"        label="Score" />
                  <SortTh k="percentage"   label="%" />
                  <th>Pass/Fail</th>
                  <SortTh k="integrity_score" label="Integrity" />
                  <SortTh k="risk_level"   label="Risk" />
                  <SortTh k="violations_count" label="Violations" />
                  <SortTh k="time_taken_secs"  label="Time" />
                  <th>Detail</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map(r => (
                  <tr key={r.submission_id}>
                    <td>
                      <p className="font-medium text-white text-sm">{r.student_name}</p>
                      <p className="text-xs text-gray-500">{r.student_email}</p>
                    </td>
                    <td className="font-mono font-semibold text-white text-sm">{r.score}/{r.max_score}</td>
                    <td className="font-mono text-sm">{(r.percentage || 0).toFixed(1)}%</td>
                    <td>
                      {r.passed
                        ? <span className="badge-green"><CheckCircle size={10} />Pass</span>
                        : <span className="badge-red"><XCircle size={10} />Fail</span>}
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                          <div className="h-full rounded-full"
                            style={{ width: `${r.integrity_score}%`, background: r.integrity_score >= 80 ? '#10b981' : r.integrity_score >= 50 ? '#f59e0b' : '#ef4444' }} />
                        </div>
                        <span className="text-xs font-mono" style={{ color: r.integrity_score >= 80 ? '#10b981' : r.integrity_score >= 50 ? '#f59e0b' : '#ef4444' }}>
                          {Math.round(r.integrity_score)}
                        </span>
                      </div>
                    </td>
                    <td><RiskBadge level={r.risk_level} /></td>
                    <td>
                      {r.violations_count > 0
                        ? <span className="flex items-center gap-1 text-red-400 text-xs"><AlertTriangle size={11} />{r.violations_count}</span>
                        : <span className="text-gray-600 text-xs">—</span>}
                    </td>
                    <td className="text-xs text-gray-500 font-mono">
                      {r.time_taken_secs ? `${Math.floor(r.time_taken_secs/60)}m ${r.time_taken_secs%60}s` : '—'}
                    </td>
                    <td>
                      <button onClick={() => navigate(`/tests/${testId}/results/${r.submission_id}`)}
                        className="text-brand-400 hover:text-brand-300 p-1 transition-colors">
                        <ChevronRight size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
