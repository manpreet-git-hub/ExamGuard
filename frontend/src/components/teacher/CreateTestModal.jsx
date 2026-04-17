// src/components/teacher/CreateTestModal.jsx
import React, { useState } from 'react';
import { X, Loader2, CalendarDays } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../../utils/api';

export default function CreateTestModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    title: '', description: '', duration_mins: 60,
    total_marks: 100, passing_marks: 40,
    start_time: '', end_time: '',
  });
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm(p => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (+form.passing_marks > +form.total_marks) {
      toast.error('Passing marks cannot be greater than total marks');
      return;
    }
    if (form.start_time && form.end_time && new Date(form.end_time) <= new Date(form.start_time)) {
      toast.error('End time must be later than start time');
      return;
    }
    setLoading(true);
    try {
      const payload = { ...form };
      if (!payload.start_time) delete payload.start_time;
      if (!payload.end_time)   delete payload.end_time;
      payload.duration_mins  = +payload.duration_mins;
      payload.total_marks    = +payload.total_marks;
      payload.passing_marks  = +payload.passing_marks;

      const r = await api.post('/api/tests/', payload);
      toast.success('Test created!');
      onCreated(r.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create test');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="card w-full max-w-lg relative animate-slide-in">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <h2 className="text-base font-semibold text-white">Create New Test</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="label">Test Title <span className="text-red-500">*</span></label>
            <input className="input" placeholder="e.g. Mathematics Midterm 2024" value={form.title} onChange={set('title')} required />
          </div>

          <div>
            <label className="label">Description</label>
            <textarea className="input resize-none" rows={2} placeholder="Brief description of the test…" value={form.description} onChange={set('description')} />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="label">Duration (min)</label>
              <input className="input" type="number" min={1} max={480} value={form.duration_mins} onChange={set('duration_mins')} required />
            </div>
            <div>
              <label className="label">Total Marks</label>
              <input className="input" type="number" min={1} value={form.total_marks} onChange={set('total_marks')} required />
            </div>
            <div>
              <label className="label">Passing Marks</label>
              <input className="input" type="number" min={0} value={form.passing_marks} onChange={set('passing_marks')} required />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Start Time (optional)</label>
              <input className="input" type="datetime-local" value={form.start_time} onChange={set('start_time')} />
            </div>
            <div>
              <label className="label">End Time (optional)</label>
              <input className="input" type="datetime-local" value={form.end_time} onChange={set('end_time')} />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
              {loading ? <Loader2 size={15} className="animate-spin" /> : null}
              {loading ? 'Creating…' : 'Create Test'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
