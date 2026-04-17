// src/pages/RegisterPage.jsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ShieldCheck, Loader2, Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: '', username: '', full_name: '',
    password: '', confirm_password: '', role: 'student'
  });
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm(p => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    if (form.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      const { confirm_password, ...payload } = form;
      await register(payload);
      toast.success('Account created! Please sign in.');
      navigate('/login');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed. Try a different email or username.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-gradient-to-br from-brand-900/20 via-gray-950 to-gray-950 pointer-events-none" />
      <div className="w-full max-w-md relative">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-brand-600 mb-4 shadow-lg">
            <ShieldCheck size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">ExamGuard</h1>
          <p className="text-gray-500 text-sm mt-1">Create your account</p>
        </div>

        <div className="card p-8">
          <h2 className="text-lg font-semibold text-white mb-6">Sign up</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Full Name *</label>
              <input className="input" placeholder="Jane Smith" value={form.full_name} onChange={set('full_name')} required />
            </div>
            <div>
              <label className="label">Username *</label>
              <input className="input" placeholder="janesmith" value={form.username} onChange={set('username')}
                required pattern="[a-zA-Z0-9_]+" title="Letters, numbers and underscores only" />
            </div>
            <div>
              <label className="label">Email Address *</label>
              <input className="input" type="email" placeholder="jane@example.com" value={form.email} onChange={set('email')} required />
            </div>
            <div>
              <label className="label">Password *</label>
              <div className="relative">
                <input className="input pr-10" type={showPwd ? 'text' : 'password'} placeholder="Min. 8 characters"
                  value={form.password} onChange={set('password')} required minLength={8} />
                <button type="button" onClick={() => setShowPwd(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                  {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <div>
              <label className="label">Confirm Password *</label>
              <input className="input" type="password" placeholder="Re-enter password"
                value={form.confirm_password} onChange={set('confirm_password')} required />
            </div>
            <div>
              <label className="label">Account Type *</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { value: 'student', label: '🎓 Student', desc: 'Take exams' },
                  { value: 'teacher', label: '👨‍🏫 Teacher', desc: 'Create & manage exams' },
                ].map(opt => (
                  <button key={opt.value} type="button"
                    onClick={() => setForm(p => ({ ...p, role: opt.value }))}
                    className={`p-3 rounded-lg border text-left transition-all ${form.role === opt.value ? 'border-brand-500 bg-brand-500/10' : 'border-gray-700 bg-gray-800 hover:border-gray-600'}`}>
                    <p className="text-sm font-medium text-white">{opt.label}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{opt.desc}</p>
                  </button>
                ))}
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-2.5 mt-2">
              {loading && <Loader2 size={16} className="animate-spin" />}
              {loading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-400 hover:text-brand-300 font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
