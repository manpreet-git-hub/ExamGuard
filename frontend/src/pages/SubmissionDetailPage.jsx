// src/pages/SubmissionDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, CheckCircle, XCircle, Shield, Camera, Loader2, FileText } from 'lucide-react';
import toast from 'react-hot-toast';
import Layout from '../components/shared/Layout';
import api from '../utils/api';
import { format } from 'date-fns';
import { parseApiDate } from '../utils/datetime';

const V_LABELS = {
  phone_detected: 'Phone Detected', tab_switched: 'Tab Switched',
  looking_away: 'Looking Away', multiple_faces: 'Multiple Faces',
  no_face: 'No Face Detected', talking: 'Talking Detected',
  eye_gaze_away: 'Eye Gaze Away', fullscreen_exit: 'Exited Fullscreen',
  copy_paste: 'Copy/Paste Attempt', network_disconnect: 'Network Disconnect',
  laptop_detected: 'Laptop Detected',
};

const V_STYLE = {
  phone_detected:    'bg-red-500/10 border-red-500/20 text-red-400',
  multiple_faces:    'bg-red-500/10 border-red-500/20 text-red-400',
  no_face:           'bg-red-500/10 border-red-500/20 text-red-400',
  tab_switched:      'bg-orange-500/10 border-orange-500/20 text-orange-400',
  fullscreen_exit:   'bg-orange-500/10 border-orange-500/20 text-orange-400',
  copy_paste:        'bg-orange-500/10 border-orange-500/20 text-orange-400',
  looking_away:      'bg-amber-500/10 border-amber-500/20 text-amber-400',
  eye_gaze_away:     'bg-amber-500/10 border-amber-500/20 text-amber-400',
  talking:           'bg-amber-500/10 border-amber-500/20 text-amber-400',
  network_disconnect:'bg-gray-700/50 border-gray-700 text-gray-400',
  laptop_detected:   'bg-blue-500/10 border-blue-500/20 text-blue-400',
};

export default function SubmissionDetailPage() {
  const { testId, submissionId } = useParams();
  const navigate = useNavigate();
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab]       = useState('violations');

  useEffect(() => {
    api.get(`/api/results/submission/${submissionId}/detail`)
      .then(r => setData(r.data))
      .catch(() => { toast.error('Failed to load submission'); navigate(`/tests/${testId}/results`); })
      .finally(() => setLoading(false));
  }, [submissionId]);

  if (loading) return (
    <Layout><div className="flex items-center justify-center h-48"><Loader2 size={28} className="animate-spin text-gray-600" /></div></Layout>
  );

  const { submission: sub, violations = [], answers = [] } = data || {};
  const evidenceItems = violations.filter(v => v.evidence_path);
  const riskColor = sub?.risk_level === 'Low' ? 'text-emerald-400' : sub?.risk_level === 'Medium' ? 'text-amber-400' : 'text-red-400';

  return (
    <Layout title="Submission Detail">
      <div className="flex items-center gap-2 mb-6 text-sm text-gray-500">
        <button onClick={() => navigate(`/tests/${testId}/results`)} className="hover:text-white flex items-center gap-1 transition-colors">
          <ArrowLeft size={14} /> Results
        </button>
        <span>/</span>
        <span className="text-white">{sub?.student_name}</span>
      </div>

      {/* Summary card */}
      <div className="card p-5 mb-6">
        <div className="flex items-start justify-between flex-wrap gap-4 mb-5">
          <div>
            <h2 className="text-lg font-semibold text-white">{sub?.student_name}</h2>
            <p className="text-sm text-gray-500">{sub?.student_email}</p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            {sub?.passed
              ? <span className="badge-green text-sm px-3 py-1"><CheckCircle size={13} /> Passed</span>
              : <span className="badge-red text-sm px-3 py-1"><XCircle size={13} /> Failed</span>}
            <span className={`badge text-sm px-3 py-1 ${sub?.risk_level === 'Low' ? 'badge-green' : sub?.risk_level === 'Medium' ? 'badge-yellow' : 'badge-red'}`}>
              <Shield size={13} /> {sub?.risk_level} Risk
            </span>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Score',         value: `${sub?.score}/${sub?.max_score}` },
            { label: 'Percentage',    value: `${(sub?.percentage || 0).toFixed(1)}%` },
            { label: 'Integrity',     value: Math.round(sub?.integrity_score ?? 100) },
            { label: 'Time Taken',    value: sub?.time_taken_secs ? `${Math.floor(sub.time_taken_secs/60)}m ${sub.time_taken_secs%60}s` : '—' },
          ].map((s, i) => (
            <div key={i} className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-500">{s.label}</p>
              <p className="text-base font-bold text-white mt-0.5">{s.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-5 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit">
        {[
          { key: 'violations', label: `Violations (${violations.length})`,   icon: AlertTriangle },
          { key: 'answers',    label: `Answers (${answers.length})`,          icon: FileText      },
          { key: 'evidence',   label: `Evidence (${evidenceItems.length})`,   icon: Camera        },
        ].map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${tab === key ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-300'}`}>
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* Violations timeline */}
      {tab === 'violations' && (
        <div className="card p-5">
          {violations.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle size={32} className="text-emerald-400 mx-auto mb-3" />
              <p className="text-white font-medium">No violations — clean exam</p>
            </div>
          ) : (
            <div className="relative pl-4 space-y-3">
              <div className="absolute left-2 top-2 bottom-2 w-px bg-gray-800" />
              {violations.map((v, i) => {
                const style = V_STYLE[v.violation_type] || 'bg-gray-800 border-gray-700 text-gray-400';
                return (
                  <div key={v.id || i} className={`relative flex gap-3 p-3 rounded-lg border ${style}`}>
                    <div className="absolute left-[-20px] w-3 h-3 rounded-full bg-gray-700 border-2 border-gray-600 mt-1" />
                    <AlertTriangle size={14} className="flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <span className="text-xs font-semibold">{V_LABELS[v.violation_type] || v.violation_type}</span>
                        <span className="text-xs text-gray-500 font-mono">{v.timestamp ? format(parseApiDate(v.timestamp), 'HH:mm:ss') : ''}</span>
                      </div>
                      {v.description && <p className="text-xs text-gray-500 mt-0.5">{v.description}</p>}
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-gray-600">Conf: {((v.confidence_score || 1) * 100).toFixed(0)}%</span>
                        {v.penalty_applied > 0 && <span className="text-xs text-red-400">−{v.penalty_applied} pts</span>}
                      </div>
                    </div>
                    {v.evidence_path && (
                      <a href={v.evidence_path} target="_blank" rel="noopener noreferrer" className="flex-shrink-0 text-gray-500 hover:text-brand-400 transition-colors">
                        <Camera size={14} />
                      </a>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Answers */}
      {tab === 'answers' && (
        <div className="space-y-3">
          {answers.length === 0 ? (
            <div className="card p-8 text-center text-gray-600 text-sm">No answer data</div>
          ) : answers.map((a, i) => (
            <div key={i} className={`card p-4 border-l-4 ${a.is_correct === true ? 'border-l-emerald-500' : a.is_correct === false ? 'border-l-red-500' : 'border-l-gray-700'}`}>
              <div className="flex items-start justify-between gap-3 mb-2">
                <span className="text-xs text-gray-500 font-medium">Q{i + 1} — {a.question_type?.replace('_', ' ')}</span>
                <div>
                  {a.is_correct === true  && <span className="badge-green text-xs">+{a.marks_awarded}/{a.max_marks}</span>}
                  {a.is_correct === false && <span className="badge-red text-xs">0/{a.max_marks}</span>}
                  {a.is_correct === null  && <span className="badge-gray text-xs">Manual grading</span>}
                </div>
              </div>
              <p className="text-sm text-white mb-2 whitespace-pre-wrap">{a.question_text}</p>
              {a.selected_options?.length > 0 && (
                <div className="text-xs bg-gray-800 rounded p-2 mb-1.5">
                  <span className="text-gray-500">Student answered: </span>
                  <span className="text-white">{a.selected_options.join(', ')}</span>
                </div>
              )}
              {a.answer_text && (
                <div className="text-xs bg-gray-800 rounded p-2 mb-1.5 whitespace-pre-wrap">
                  <span className="text-gray-500">Student answered: </span>
                  <span className="text-white">{a.answer_text}</span>
                </div>
              )}
              {!a.selected_options?.length && !a.answer_text && (
                <p className="text-xs text-gray-600 italic">Not answered</p>
              )}
              {a.correct_answer && a.is_correct === false && !['short_answer','coding'].includes(a.question_type) && (
                <div className="text-xs text-emerald-400 mt-1">
                  ✓ Correct: {Array.isArray(a.correct_answer) ? a.correct_answer.join(', ') : a.correct_answer}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Evidence */}
      {tab === 'evidence' && (
        <div>
          {evidenceItems.length === 0 ? (
            <div className="card p-10 text-center text-gray-600 text-sm">No evidence screenshots captured</div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {evidenceItems.map((v, i) => (
                <div key={i} className="card overflow-hidden">
                  <a href={v.evidence_path} target="_blank" rel="noopener noreferrer">
                    <img src={v.evidence_path} alt={v.violation_type}
                      className="w-full aspect-video object-cover bg-gray-800 hover:opacity-80 transition-opacity" />
                  </a>
                  <div className="p-2.5">
                    <p className="text-xs font-medium text-red-400 capitalize">{V_LABELS[v.violation_type] || v.violation_type}</p>
                    <p className="text-xs text-gray-500 font-mono">{v.timestamp ? format(parseApiDate(v.timestamp), 'HH:mm:ss') : ''}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}
