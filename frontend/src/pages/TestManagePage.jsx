// src/pages/TestManagePage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Plus, Pencil, Trash2, GripVertical, Loader2,
  CheckSquare, AlignLeft, Code, CircleDot,
  Copy, BarChart2, Save, X, Activity
} from 'lucide-react';
import toast from 'react-hot-toast';
import Layout from '../components/shared/Layout';
import api from '../utils/api';

const Q_TYPES = [
  { value: 'mcq',              label: 'MCQ',          icon: CircleDot  },
  { value: 'multiple_correct', label: 'Multi-Select', icon: CheckSquare },
  { value: 'short_answer',     label: 'Short Answer', icon: AlignLeft  },
  { value: 'coding',           label: 'Coding',       icon: Code       },
];

const EMPTY = {
  question_text: '', question_type: 'mcq',
  options: ['', '', '', ''], correct_answer: null,
  marks: 1, explanation: '',
};

function QuestionForm({ testId, initial, onSaved, onCancel }) {
  const [form, setForm]     = useState(initial ? {
    ...initial,
    options: initial.options || ['', '', '', ''],
    correct_answer: initial.correct_answer || null,
  } : { ...EMPTY });
  const [loading, setLoading] = useState(false);
  const isEdit = !!initial?.id;

  const setField = (k, v) => setForm(p => ({ ...p, [k]: v }));
  const setOption = (i, v) => {
    const opts = [...(form.options || [])];
    const previous = opts[i];
    opts[i] = v;
    setForm(prev => {
      let nextCorrect = prev.correct_answer;
      if (prev.question_type === 'mcq' && prev.correct_answer === previous) {
        nextCorrect = v;
      }
      if (prev.question_type === 'multiple_correct' && Array.isArray(prev.correct_answer)) {
        nextCorrect = prev.correct_answer.map(item => item === previous ? v : item);
      }
      return { ...prev, options: opts, correct_answer: nextCorrect };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.question_text.trim()) { toast.error('Question text is required'); return; }
    setLoading(true);
    try {
      const payload = {
        question_text: form.question_text,
        question_type: form.question_type,
        marks: +form.marks || 1,
        explanation: form.explanation || '',
        correct_answer: form.correct_answer,
        options: ['mcq','multiple_correct'].includes(form.question_type)
          ? (form.options || []).filter(o => o.trim())
          : null,
      };

      let result;
      if (isEdit) {
        result = await api.put(`/api/questions/${initial.id}`, payload);
      } else {
        result = await api.post('/api/questions/', { ...payload, test_id: testId });
      }
      toast.success(isEdit ? 'Question updated!' : 'Question added!');
      onSaved(result.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save question');
    } finally {
      setLoading(false);
    }
  };

  const needsOptions = ['mcq', 'multiple_correct'].includes(form.question_type);

  return (
    <form onSubmit={handleSubmit} className="card p-5 space-y-4 border-brand-500/30">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">{isEdit ? 'Edit Question' : 'Add New Question'}</h3>
        <button type="button" onClick={onCancel} className="text-gray-500 hover:text-white"><X size={16} /></button>
      </div>

      {/* Type selector */}
      <div>
        <label className="label">Question Type</label>
        <div className="grid grid-cols-4 gap-2">
          {Q_TYPES.map(({ value, label, icon: Icon }) => (
            <button key={value} type="button" onClick={() => setField('question_type', value)}
              className={`flex flex-col items-center gap-1.5 p-2.5 rounded-lg border text-xs font-medium transition-all
                ${form.question_type === value
                  ? 'border-brand-500 bg-brand-500/10 text-brand-400'
                  : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'}`}>
              <Icon size={16} />{label}
            </button>
          ))}
        </div>
      </div>

      {/* Question text */}
      <div>
        <label className="label">Question Text *</label>
        <textarea className="input resize-none" rows={3} placeholder="Type your question here…"
          value={form.question_text} onChange={e => setField('question_text', e.target.value)} required />
      </div>

      {/* Options */}
      {needsOptions && (
        <div>
          <label className="label">
            Answer Options
            <span className="text-gray-500 font-normal ml-2">
              ({form.question_type === 'mcq' ? '● select one correct' : '☑ check all correct'})
            </span>
          </label>
          <div className="space-y-2">
            {(form.options || []).map((opt, i) => (
              <div key={i} className="flex items-center gap-2">
                {form.question_type === 'mcq' ? (
                  <input type="radio" name="correct" checked={form.correct_answer === opt && opt.trim() !== ''}
                    onChange={() => setField('correct_answer', opt)} className="accent-brand-500 flex-shrink-0" />
                ) : (
                  <input type="checkbox"
                    checked={Array.isArray(form.correct_answer) && form.correct_answer.includes(opt)}
                    onChange={e => {
                      const cur = Array.isArray(form.correct_answer) ? form.correct_answer : [];
                      setField('correct_answer', e.target.checked ? [...cur, opt] : cur.filter(c => c !== opt));
                    }}
                    className="accent-brand-500 flex-shrink-0" />
                )}
                <span className="text-xs text-gray-500 w-5 flex-shrink-0">{String.fromCharCode(65 + i)}.</span>
                <input className="input flex-1 py-2" placeholder={`Option ${String.fromCharCode(65 + i)}`}
                  value={opt} onChange={e => setOption(i, e.target.value)} />
                {(form.options || []).length > 2 && (
                  <button type="button" onClick={() => {
                    const removed = (form.options || [])[i];
                    const opts = (form.options || []).filter((_, idx) => idx !== i);
                    setForm(prev => {
                      let nextCorrect = prev.correct_answer;
                      if (prev.question_type === 'mcq' && prev.correct_answer === removed) {
                        nextCorrect = null;
                      }
                      if (prev.question_type === 'multiple_correct' && Array.isArray(prev.correct_answer)) {
                        nextCorrect = prev.correct_answer.filter(item => item !== removed);
                      }
                      return { ...prev, options: opts, correct_answer: nextCorrect };
                    });
                  }} className="text-gray-600 hover:text-red-400 flex-shrink-0"><X size={14} /></button>
                )}
              </div>
            ))}
            <button type="button" onClick={() => setField('options', [...(form.options || []), ''])}
              className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 mt-1">
              <Plus size={13} /> Add option
            </button>
          </div>
        </div>
      )}

      {/* Model answer for short/coding */}
      {['short_answer', 'coding'].includes(form.question_type) && (
        <div>
          <label className="label">Model Answer (optional)</label>
          <textarea className="input resize-none" rows={2} placeholder="Expected answer…"
            value={form.correct_answer || ''} onChange={e => setField('correct_answer', e.target.value)} />
        </div>
      )}

      <div className="flex items-end gap-3">
        <div className="w-24">
          <label className="label">Marks</label>
          <input className="input" type="number" min={1} value={form.marks}
            onChange={e => setField('marks', e.target.value)} />
        </div>
        <div className="flex-1">
          <label className="label">Explanation (optional)</label>
          <input className="input" placeholder="Why is this the correct answer?" value={form.explanation || ''}
            onChange={e => setField('explanation', e.target.value)} />
        </div>
      </div>

      <div className="flex gap-3 pt-1">
        <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
          {loading ? 'Saving…' : (isEdit ? 'Update Question' : 'Add Question')}
        </button>
      </div>
    </form>
  );
}

function QuestionCard({ question, index, onEdit, onDelete }) {
  const [deleting, setDeleting] = useState(false);
  const typeInfo = Q_TYPES.find(t => t.value === question.question_type) || Q_TYPES[0];
  const Icon = typeInfo.icon;

  const handleDelete = async () => {
    if (!confirm('Delete this question?')) return;
    setDeleting(true);
    try {
      await api.delete(`/api/questions/${question.id}`);
      toast.success('Deleted');
      onDelete(question.id);
    } catch {
      toast.error('Failed to delete');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="card p-4 group hover:border-gray-700 transition-colors">
      <div className="flex items-start gap-3">
        <div className="flex items-center gap-2 flex-shrink-0 mt-0.5">
          <GripVertical size={16} className="text-gray-700" />
          <span className="text-xs font-bold text-gray-600 w-5 text-center">{index + 1}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="badge-blue"><Icon size={10} />{typeInfo.label}</span>
            <span className="text-xs text-gray-500">{question.marks} mark{question.marks !== 1 ? 's' : ''}</span>
          </div>
          <p className="text-sm text-white line-clamp-2">{question.question_text}</p>
          {question.options?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {question.options.map((o, i) => {
                const isCorrect = question.question_type === 'mcq'
                  ? o === question.correct_answer
                  : Array.isArray(question.correct_answer) && question.correct_answer.includes(o);
                return (
                  <span key={i} className={`text-xs px-2 py-0.5 rounded ${isCorrect ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-800 text-gray-400'}`}>
                    {String.fromCharCode(65 + i)}. {o}
                  </span>
                );
              })}
            </div>
          )}
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
          <button onClick={() => onEdit(question)} className="p-1.5 rounded hover:bg-gray-800 text-gray-500 hover:text-white transition-colors">
            <Pencil size={14} />
          </button>
          <button onClick={handleDelete} disabled={deleting} className="p-1.5 rounded hover:bg-gray-800 text-gray-500 hover:text-red-400 transition-colors">
            {deleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function TestManagePage() {
  const { testId } = useParams();
  const navigate   = useNavigate();
  const [test, setTest]             = useState(null);
  const [questions, setQuestions]   = useState([]);
  const [loading, setLoading]       = useState(true);
  const [showForm, setShowForm]     = useState(false);
  const [editQuestion, setEditQuestion] = useState(null);

  useEffect(() => {
    Promise.all([
      api.get(`/api/tests/${testId}`),
      api.get(`/api/questions/test/${testId}`)
    ]).then(([t, q]) => {
      setTest(t.data);
      setQuestions(q.data.sort((a, b) => a.order_index - b.order_index));
    }).catch(() => toast.error('Failed to load test'))
      .finally(() => setLoading(false));
  }, [testId]);

  const copyLink = () => {
    navigator.clipboard.writeText(`${window.location.origin}/test/${test.access_code}`);
    toast.success('Test link copied!');
  };

  const handleSaved = (q) => {
    setQuestions(prev => {
      const exists = prev.find(p => p.id === q.id);
      return exists ? prev.map(p => p.id === q.id ? q : p) : [...prev, q];
    });
    setShowForm(false);
    setEditQuestion(null);
  };

  const handleDeleted = (id) => setQuestions(prev => prev.filter(q => q.id !== id));
  const handleEdit = (q) => { setEditQuestion(q); setShowForm(true); window.scrollTo({ top: 0, behavior: 'smooth' }); };

  if (loading) return (
    <Layout><div className="flex items-center justify-center h-48"><Loader2 size={28} className="animate-spin text-gray-600" /></div></Layout>
  );

  return (
    <Layout title={test?.title || 'Manage Test'}>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-6 text-sm text-gray-500">
        <button onClick={() => navigate('/')} className="hover:text-white transition-colors">Dashboard</button>
        <span>/</span>
        <span className="text-white">{test?.title}</span>
      </div>

      {/* Test info banner */}
      <div className="card p-4 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-4 flex-wrap">
            {[
              { label: 'Access Code', value: <code className="text-brand-400 font-mono font-bold tracking-widest">{test?.access_code}</code> },
              { label: 'Duration',    value: `${test?.duration_mins} min` },
              { label: 'Questions',   value: questions.length },
              { label: 'Total Marks', value: test?.total_marks },
              { label: 'Pass Marks',  value: test?.passing_marks },
            ].map((s, i) => (
              <React.Fragment key={i}>
                {i > 0 && <div className="h-8 w-px bg-gray-800 hidden sm:block" />}
                <div>
                  <p className="text-xs text-gray-500">{s.label}</p>
                  <p className="text-sm font-semibold text-white">{s.value}</p>
                </div>
              </React.Fragment>
            ))}
          </div>
          <div className="flex gap-2">
            <button onClick={copyLink} className="btn-secondary text-xs"><Copy size={13} /> Copy Link</button>
            <button onClick={() => navigate(`/tests/${testId}/results`)} className="btn-secondary text-xs"><BarChart2 size={13} /> Results</button>
            <button onClick={() => navigate(`/tests/${testId}/monitor`)} className="btn-secondary text-xs"><Activity size={13} className="text-emerald-400" /> Monitor</button>
          </div>
        </div>
      </div>

      {/* Add / Edit form */}
      {showForm ? (
        <div className="mb-6">
          <QuestionForm
            testId={+testId}
            initial={editQuestion}
            onSaved={handleSaved}
            onCancel={() => { setShowForm(false); setEditQuestion(null); }}
          />
        </div>
      ) : (
        <button onClick={() => { setShowForm(true); setEditQuestion(null); }} className="btn-primary mb-6">
          <Plus size={15} /> Add Question
        </button>
      )}

      {/* Questions list */}
      {questions.length === 0 ? (
        <div className="card p-10 text-center">
          <p className="text-gray-500">No questions yet. Add your first question above.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {questions.map((q, i) => (
            <QuestionCard key={q.id} question={q} index={i} onEdit={handleEdit} onDelete={handleDeleted} />
          ))}
          <p className="text-xs text-gray-600 text-center pt-2">{questions.length} question{questions.length !== 1 ? 's' : ''} • {questions.reduce((s, q) => s + q.marks, 0)} total marks</p>
        </div>
      )}
    </Layout>
  );
}
