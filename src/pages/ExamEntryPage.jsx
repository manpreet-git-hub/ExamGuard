// src/pages/ExamEntryPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ShieldCheck, Camera, Mic, Clock, FileText, Users, CheckCircle, AlertCircle, Loader2, ChevronRight, LogIn, Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../utils/api';

function PermRow({ label, status, icon: Icon }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-800/50">
      <Icon size={16} className="text-gray-400 flex-shrink-0" />
      <span className="flex-1 text-sm text-gray-300">{label}</span>
      {status === 'granted' && <CheckCircle size={16} className="text-emerald-400" />}
      {status === 'denied'  && <AlertCircle size={16} className="text-red-400" />}
      {status === 'pending' && <div className="w-4 h-4 border-2 border-gray-600 rounded-full" />}
    </div>
  );
}

export default function ExamEntryPage() {
  const { accessCode } = useParams();
  const { user, login, logout } = useAuth();
  const navigate = useNavigate();

  const [test, setTest]         = useState(null);
  const [loading, setLoading]   = useState(true);
  const [step, setStep]         = useState('login');
  const [camStatus, setCamStatus] = useState('pending');
  const [micStatus, setMicStatus] = useState('pending');
  const [stream, setStream]     = useState(null);
  const videoRef = useRef(null);

  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [showPwd, setShowPwd]     = useState(false);
  const [loggingIn, setLoggingIn] = useState(false);

  useEffect(() => {
    api.get(`/api/tests/code/${accessCode}`)
      .then(r => { setTest(r.data); setLoading(false); })
      .catch(() => { toast.error('Test not found or inactive'); setLoading(false); });
  }, [accessCode]);

  useEffect(() => {
    if (!user) return;
    if (user.role === 'student') {
      setStep('instructions');
      return;
    }
    setStep('login');
    toast.error('Please sign in with a student account to take this exam.', { id: 'student-only-exam' });
  }, [user]);

  useEffect(() => {
    if (stream && videoRef.current) videoRef.current.srcObject = stream;
  }, [stream]);

  // Cleanup stream on unmount
  useEffect(() => () => { stream?.getTracks().forEach(t => t.stop()); }, [stream]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoggingIn(true);
    try {
      const loggedInUser = await login(loginForm.email, loginForm.password);
      if (loggedInUser.role !== 'student') {
        logout();
        toast.error('Only student accounts can take exams.');
        return;
      }
      setStep('instructions');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoggingIn(false);
    }
  };

  const requestPermissions = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setStream(s);
      setCamStatus('granted');
      setMicStatus('granted');
      setStep('ready');
    } catch (err) {
      setCamStatus('denied');
      setMicStatus('denied');
      toast.error('Camera & microphone access is required to take the exam.');
    }
  };

  const startExam = () => {
    if (camStatus !== 'granted') { toast.error('Camera permission required'); return; }
    stream?.getTracks().forEach(t => t.stop());
    navigate(`/exam/${test.id}`);
  };

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <Loader2 size={28} className="animate-spin text-gray-600" />
    </div>
  );

  if (!test) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center text-center p-4">
      <div>
        <p className="text-gray-400 text-lg font-medium">Test not found</p>
        <p className="text-gray-600 text-sm mt-2">Check the access code and try again.</p>
        <button onClick={() => navigate('/login')} className="btn-secondary mt-4 mx-auto">Go to Login</button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-gradient-to-br from-brand-900/10 via-transparent to-transparent pointer-events-none" />
      <div className="w-full max-w-md relative">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-brand-600 mb-3">
            <ShieldCheck size={22} className="text-white" />
          </div>
          <h1 className="text-xl font-bold text-white">ExamGuard</h1>
        </div>

        <div className="card overflow-hidden">
          {/* Test header */}
          <div className="bg-gray-800/50 p-5 border-b border-gray-800">
            <h2 className="text-base font-semibold text-white mb-1">{test.title}</h2>
            {test.description && <p className="text-sm text-gray-500">{test.description}</p>}
            <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
              <span className="flex items-center gap-1"><Clock size={12} />{test.duration_mins} min</span>
              <span className="flex items-center gap-1"><FileText size={12} />{test.question_count} questions</span>
              <span className="flex items-center gap-1"><Users size={12} />{test.total_marks} marks</span>
            </div>
          </div>

          <div className="p-6">
            {/* Step: Login */}
            {step === 'login' && (
              <div>
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <LogIn size={16} className="text-brand-400" /> Sign in to take this exam
                </h3>
                <form onSubmit={handleLogin} className="space-y-3">
                  <input className="input" type="email" placeholder="Email address"
                    value={loginForm.email} onChange={e => setLoginForm(p => ({...p, email: e.target.value}))} required />
                  <div className="relative">
                    <input className="input pr-10" type={showPwd ? 'text' : 'password'} placeholder="Password"
                      value={loginForm.password} onChange={e => setLoginForm(p => ({...p, password: e.target.value}))} required />
                    <button type="button" onClick={() => setShowPwd(p => !p)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                      {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  <button type="submit" disabled={loggingIn} className="btn-primary w-full justify-center">
                    {loggingIn && <Loader2 size={15} className="animate-spin" />}
                    {loggingIn ? 'Signing in…' : 'Sign In & Continue'}
                  </button>
                </form>
                <p className="text-xs text-gray-600 text-center mt-4">
                  Don't have an account?{' '}
                  <button onClick={() => navigate('/register')} className="text-brand-400 hover:text-brand-300">Register</button>
                </p>
              </div>
            )}

            {/* Step: Instructions */}
            {step === 'instructions' && (
              <div>
                <h3 className="text-sm font-semibold text-white mb-4">📋 Exam Instructions</h3>
                <ul className="space-y-2.5 mb-6">
                  {[
                    'Keep your face clearly visible in the webcam at all times',
                    'Do not switch browser tabs or minimize the window',
                    'No other people should be visible on camera',
                    'No mobile phones or secondary devices allowed',
                    `You have ${test.duration_mins} minutes to complete the exam`,
                    'Your answers are auto-saved every 30 seconds',
                    `Passing mark: ${test.passing_marks} out of ${test.total_marks}`,
                    'AI proctoring is active throughout the entire exam',
                  ].map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                      <CheckCircle size={14} className="text-brand-400 mt-0.5 flex-shrink-0" />{item}
                    </li>
                  ))}
                </ul>
                <button onClick={() => setStep('permissions')} className="btn-primary w-full justify-center">
                  I Understand — Continue <ChevronRight size={15} />
                </button>
              </div>
            )}

            {/* Step: Permissions */}
            {step === 'permissions' && (
              <div>
                <h3 className="text-sm font-semibold text-white mb-3">🎥 Camera & Microphone Access</h3>
                <p className="text-sm text-gray-500 mb-4">This exam requires camera and microphone access for AI proctoring.</p>
                <div className="space-y-2 mb-5">
                  <PermRow label="Camera (required for proctoring)" status={camStatus} icon={Camera} />
                  <PermRow label="Microphone (required)"            status={micStatus} icon={Mic} />
                </div>
                {camStatus === 'denied' && (
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg mb-4">
                    <p className="text-xs text-red-300">Permission denied. Please allow camera access in your browser settings and reload this page.</p>
                  </div>
                )}
                <button onClick={requestPermissions} className="btn-primary w-full justify-center">
                  <Camera size={15} /> Grant Camera & Microphone Access
                </button>
              </div>
            )}

            {/* Step: Ready */}
            {step === 'ready' && (
              <div>
                <h3 className="text-sm font-semibold text-white mb-3">✅ All Set! Camera Preview</h3>
                <div className="relative rounded-xl overflow-hidden bg-gray-800 mb-4 aspect-video">
                  <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
                  <div className="absolute top-2 right-2">
                    <div className="flex items-center gap-1.5 bg-black/60 rounded-full px-2 py-1">
                      <div className="live-dot" />
                      <span className="text-xs text-white font-medium">Camera ready</span>
                    </div>
                  </div>
                </div>
                <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg mb-4">
                  <p className="text-xs text-amber-300">⚠️ Once started, do not exit fullscreen, switch tabs, or look away for extended periods.</p>
                </div>
                <button onClick={startExam} className="btn-primary w-full justify-center text-base py-3 font-semibold">
                  🚀 Start Exam Now
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
