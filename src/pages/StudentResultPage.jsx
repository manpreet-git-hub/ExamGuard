// src/pages/StudentResultPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, CheckCircle, XCircle, Shield, Clock,
  AlertTriangle, Loader2, Award
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../utils/api';
import { format } from 'date-fns';
import { parseApiDate } from '../utils/datetime';

const VIOLATION_LABELS = {
  phone_detected:     'Phone Detected',
  tab_switched:       'Tab Switched',
  looking_away:       'Looking Away',
  multiple_faces:     'Multiple Faces',
  no_face:            'No Face Detected',
  talking:            'Talking Detected',
  eye_gaze_away:      'Eye Gaze Away',
  fullscreen_exit:    'Exited Fullscreen',
  copy_paste:         'Copy/Paste Attempted',
  network_disconnect: 'Network Disconnect',
  laptop_detected:    'Laptop Detected',
};

export default function StudentResultPage() {
  const { submissionId } = useParams();
  const navigate = useNavigate();
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab]       = useState('answers');

  useEffect(() => {
    api.get(`/api/student/result/${submissionId}`)
      .then(r => setData(r.data))
      .catch(() => {
        toast.error('Could not load result');
        navigate('/student');
      })
      .finally(() => setLoading(false));
  }, [submissionId]);

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <Loader2 size={28} className="animate-spin text-gray-600" />
    </div>
  );

  if (!data) return null;

  const { submission: sub, answers = [], violations = [] } = data;
  const riskColor = sub?.risk_level === 'Low' ? 'text-emerald-400' : sub?.risk_level === 'Medium' ? 'text-amber-400' : 'text-red-400';
  const scorePercent = sub?.percentage || 0;

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 lg:px-8 py-4 flex items-center gap-4 sticky top-0 z-30">
        <button onClick={() => navigate('/student')} className="flex items-center gap-2 text-gray-400 hover:text-white text-sm transition-colors">
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
        <span className="text-gray-700">/</span>
        <span className="text-white text-sm font-medium truncate">{sub?.test_title || 'Result'}</span>
      </header>

      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Hero result card */}
        <div className="card p-8 text-center">
          <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 ${sub?.passed ? 'bg-emerald-500/10' : 'bg-red-500/10'}`}>
            {sub?.passed
              ? <Award size={40} className="text-emerald-400" />
              : <XCircle size={40} className="text-red-400" />}
          </div>
          <h1 className="text-3xl font-bold text-white mb-1">
            {sub?.passed ? '🎉 Passed!' : '❌ Failed'}
          </h1>
          <p className="text-gray-500 text-sm mb-6">{sub?.test_title}</p>

          <div className="flex items-center justify-center gap-8 flex-wrap mb-6">
            <div>
              <p className="text-4xl font-bold text-white">
                {sub?.score}<span className="text-xl text-gray-500">/{sub?.max_score}</span>
              </p>
              <p className="text-sm text-gray-500 mt-1">Score</p>
            </div>
            <div className="h-12 w-px bg-gray-800 hidden sm:block" />
            <div>
              <p className="text-4xl font-bold text-brand-400">{scorePercent.toFixed(1)}%</p>
              <p className="text-sm text-gray-500 mt-1">Percentage</p>
            </div>
            <div className="h-12 w-px bg-gray-800 hidden sm:block" />
            <div>
              <p className={`text-4xl font-bold ${riskColor}`}>{Math.round(sub?.integrity_score)}</p>
              <p className="text-sm text-gray-500 mt-1">Integrity</p>
            </div>
          </div>

          <div className="max-w-sm mx-auto">
            <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-1000 ${sub?.passed ? 'bg-emerald-500' : 'bg-red-500'}`}
                style={{ width: `${scorePercent}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0%</span>
              <span className="text-amber-400">Pass: {sub?.passing_marks}/{sub?.max_score}</span>
              <span>100%</span>
            </div>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Time Taken',  value: sub?.time_taken_secs ? `${Math.floor(sub.time_taken_secs/60)}m ${sub.time_taken_secs%60}s` : '—', icon: Clock          },
            { label: 'Violations',  value: violations.length,   icon: AlertTriangle },
            { label: 'Risk Level',  value: sub?.risk_level || '—', icon: Shield       },
            { label: 'Submitted',   value: sub?.submitted_at ? format(parseApiDate(sub.submitted_at), 'HH:mm') : '—', icon: CheckCircle },
          ].map((s, i) => (
            <div key={i} className="card p-3 text-center">
              <s.icon size={16} className="text-gray-500 mx-auto mb-1" />
              <p className="text-base font-bold text-white">{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit">
          {[
            { key: 'answers',    label: `Answer Review (${answers.length})` },
            { key: 'violations', label: `Violations (${violations.length})`  },
          ].map(({ key, label }) => (
            <button key={key} onClick={() => setTab(key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === key ? 'bg-gray-800 text-white' : 'text-gray-500 hover:text-gray-300'}`}>
              {label}
            </button>
          ))}
        </div>

        {/* Answer Review */}
        {tab === 'answers' && (
          <div className="space-y-3">
            {answers.length === 0 ? (
              <div className="card p-8 text-center text-gray-600 text-sm">No answer data available</div>
            ) : answers.map((a, i) => (
              <div key={i} className={`card p-4 border-l-4 ${
                a.is_correct === true  ? 'border-l-emerald-500' :
                a.is_correct === false ? 'border-l-red-500' : 'border-l-gray-700'
              }`}>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <span className="text-xs text-gray-500 font-medium">Q{i + 1}</span>
                  <div>
                    {a.is_correct === true  && <span className="badge-green text-xs">+{a.marks_awarded} marks</span>}
                    {a.is_correct === false && <span className="badge-red text-xs">0 marks</span>}
                    {a.is_correct === null  && <span className="badge-gray text-xs">Manual grading</span>}
                  </div>
                </div>
                <p className="text-sm text-white mb-2 whitespace-pre-wrap">{a.question_text}</p>
                {a.selected_options?.length > 0 && (
                  <p className="text-xs text-gray-400">Your answer: <span className="text-white">{a.selected_options.join(', ')}</span></p>
                )}
                {a.answer_text && (
                  <p className="text-xs text-gray-400">Your answer: <span className="text-white">{a.answer_text}</span></p>
                )}
                {!a.selected_options?.length && !a.answer_text && (
                  <p className="text-xs text-gray-600 italic">Not answered</p>
                )}
                {a.correct_answer && a.is_correct === false && !['short_answer','coding'].includes(a.question_type) && (
                  <p className="text-xs text-emerald-400 mt-1">
                    ✓ Correct: {Array.isArray(a.correct_answer) ? a.correct_answer.join(', ') : a.correct_answer}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Violations */}
        {tab === 'violations' && (
          <div className="card p-5">
            {violations.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle size={32} className="text-emerald-400 mx-auto mb-3" />
                <p className="text-white font-medium">Clean exam — no violations!</p>
                <p className="text-gray-500 text-sm mt-1">You maintained a perfect integrity score.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {violations.map((v, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-red-500/5 border border-red-500/15">
                    <AlertTriangle size={14} className="text-red-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm text-red-300 font-medium">
                        {VIOLATION_LABELS[v.violation_type] || v.violation_type.replace(/_/g, ' ')}
                      </p>
                      {v.description && <p className="text-xs text-gray-500 mt-0.5">{v.description}</p>}
                      <p className="text-xs text-gray-600 mt-1 font-mono">
                        {v.timestamp ? format(parseApiDate(v.timestamp), 'HH:mm:ss') : ''}
                      </p>
                    </div>
                    {v.penalty_applied > 0 && (
                      <span className="text-xs text-red-400 font-semibold">−{v.penalty_applied} pts</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
