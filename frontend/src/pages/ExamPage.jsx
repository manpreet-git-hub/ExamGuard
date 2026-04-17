// src/pages/ExamPage.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Clock, AlertTriangle, ChevronLeft, ChevronRight,
  Send, Flag, Camera, Loader2, ShieldCheck, Eye
} from 'lucide-react';
import toast from 'react-hot-toast';
import api, { getWsUrl } from '../utils/api';
import { parseApiDate } from '../utils/datetime';

// ── Proctoring hook ────────────────────────────────────────────────────────────
function getRiskLevel(score) {
  if (score >= 80) return 'Low';
  if (score >= 50) return 'Medium';
  return 'High';
}

function useProctoring({ submissionId, initialIntegrityScore = 100, onViolation, onBroadcast }) {
  const [integrityScore, setIntegrityScore] = useState(initialIntegrityScore);
  const [violations, setViolations]         = useState([]);
  const [activeViolations, setActiveViolations] = useState(new Set());
  const tabHiddenTime = useRef(null);
  const submissionIdRef = useRef(submissionId);
  const integrityRef = useRef(100);
  const seenViolationIdsRef = useRef(new Set());

  useEffect(() => { submissionIdRef.current = submissionId; }, [submissionId]);
  useEffect(() => {
    integrityRef.current = initialIntegrityScore;
    setIntegrityScore(initialIntegrityScore);
    setViolations([]);
    setActiveViolations(new Set());
    seenViolationIdsRef.current = new Set();
  }, [initialIntegrityScore, submissionId]);

  const registerViolationEvent = useCallback((event, nextIntegrity) => {
    if (!event) return;
    if (event.id && seenViolationIdsRef.current.has(event.id)) return;
    if (event.id) {
      seenViolationIdsRef.current.add(event.id);
    }

    if (typeof nextIntegrity === 'number') {
      integrityRef.current = nextIntegrity;
      setIntegrityScore(nextIntegrity);
    }

    setViolations(prev => [event, ...prev].slice(0, 30));
    setActiveViolations(prev => new Set([...prev, event.violation_type]));
    onViolation?.(event.violation_type, event.description, event);
    onBroadcast?.({
      type: 'violation',
      submission_id: submissionIdRef.current,
      student_id: event.student_id,
      test_id: event.test_id,
      violation_type: event.violation_type,
      description: event.description,
      timestamp: event.timestamp,
      integrity_score: typeof nextIntegrity === 'number' ? nextIntegrity : integrityRef.current,
      risk_level: getRiskLevel(typeof nextIntegrity === 'number' ? nextIntegrity : integrityRef.current),
      is_active: true,
      is_submitted: false,
    });
    setTimeout(() => {
      setActiveViolations(prev => {
        const next = new Set(prev);
        next.delete(event.violation_type);
        return next;
      });
    }, 5000);
  }, [onBroadcast, onViolation]);

  const logViolation = useCallback(async (type, description) => {
    const sid = submissionIdRef.current;
    if (!sid) return;
    try {
      const r = await api.post('/api/proctoring/violation', {
        submission_id: sid,
        violation_type: type,
        description,
        confidence_score: 1.0,
      });
      const penalty = r.data.penalty_applied || 0;
      const nextIntegrity = Math.max(0, integrityRef.current - penalty);
      registerViolationEvent(r.data, nextIntegrity);
    } catch {}
  }, [registerViolationEvent]);

  const applyRemoteViolations = useCallback((events, nextIntegrity) => {
    if (!Array.isArray(events) || events.length === 0) {
      if (typeof nextIntegrity === 'number') {
        integrityRef.current = nextIntegrity;
        setIntegrityScore(nextIntegrity);
      }
      return;
    }

    events.forEach(event => registerViolationEvent(event, nextIntegrity));
  }, [registerViolationEvent]);

  // Tab / window visibility
  useEffect(() => {
    const onHide = () => { tabHiddenTime.current = Date.now(); };
    const onShow = () => {
      if (tabHiddenTime.current) {
        const secs = ((Date.now() - tabHiddenTime.current) / 1000).toFixed(1);
        logViolation('tab_switched', `Tab hidden for ${secs}s`);
        tabHiddenTime.current = null;
      }
    };
    const onBlur = () => logViolation('tab_switched', 'Window lost focus');
    const onVisibilityChange = () => {
      if (document.hidden) onHide();
      else onShow();
    };
    document.addEventListener('visibilitychange', onVisibilityChange);
    window.addEventListener('blur', onBlur);
    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange);
      window.removeEventListener('blur', onBlur);
    };
  }, [logViolation]);

  // Block copy/paste
  useEffect(() => {
    const block = (e) => {
      e.preventDefault();
      logViolation('copy_paste', `${e.type} attempted`);
      toast.error('Copy/paste is not allowed during the exam', { id: 'copypaste' });
    };
    document.addEventListener('copy',  block);
    document.addEventListener('paste', block);
    document.addEventListener('cut',   block);
    return () => {
      document.removeEventListener('copy',  block);
      document.removeEventListener('paste', block);
      document.removeEventListener('cut',   block);
    };
  }, [logViolation]);

  // Fullscreen
  useEffect(() => {
    const tryFullscreen = () => {
      document.documentElement.requestFullscreen?.().catch(() => {});
    };
    const onFSChange = () => {
      if (!document.fullscreenElement) {
        logViolation('fullscreen_exit', 'Exited fullscreen mode');
        setTimeout(tryFullscreen, 2000);
      }
    };
    tryFullscreen();
    document.addEventListener('fullscreenchange', onFSChange);
    return () => document.removeEventListener('fullscreenchange', onFSChange);
  }, [logViolation]);

  // Network
  useEffect(() => {
    const onOffline = () => logViolation('network_disconnect', 'Network disconnected');
    window.addEventListener('offline', onOffline);
    return () => window.removeEventListener('offline', onOffline);
  }, [logViolation]);

  return { integrityScore, violations, activeViolations, logViolation, applyRemoteViolations };
}

// ── Webcam panel ───────────────────────────────────────────────────────────────
function WebcamPanel({ stream, activeViolations, aiStatus }) {
  const videoRef  = useRef(null);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.srcObject = stream || null;
    }
  }, [stream]);

  const hasAlert = activeViolations.size > 0;
  const camOk = Boolean(stream);

  return (
    <div className={`relative rounded-xl overflow-hidden border-2 transition-all duration-300 ${hasAlert ? 'border-red-500' : 'border-gray-700'}`}>
      {camOk ? (
        <video ref={videoRef} autoPlay muted playsInline className="w-full aspect-video object-cover bg-gray-800" />
      ) : (
        <div className="aspect-video bg-gray-800 flex flex-col items-center justify-center gap-2">
          <Camera size={20} className="text-gray-600" />
          <p className="text-xs text-gray-500">Camera unavailable</p>
        </div>
      )}
      <div className="absolute top-2 left-2">
        <div className={`flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-medium ${hasAlert ? 'bg-red-900/80 text-red-300' : 'bg-black/60 text-white'}`}>
          <div className={hasAlert ? 'w-2 h-2 rounded-full bg-red-400 animate-pulse' : 'live-dot'} />
          {hasAlert ? 'ALERT' : 'Proctored'}
        </div>
      </div>
      {aiStatus?.mode && (
        <div className="absolute bottom-2 left-2 right-2">
          <div className={`rounded-md px-2 py-1 text-[11px] ${aiStatus.mode === 'error' ? 'bg-red-950/80 text-red-300' : aiStatus.mode === 'warning' ? 'bg-amber-950/80 text-amber-200' : 'bg-black/60 text-gray-200'}`}>
            {aiStatus.label}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Timer ──────────────────────────────────────────────────────────────────────
function ExamTimer({ durationMins, startedAt, onExpired }) {
  const [remaining, setRemaining] = useState(null);
  const expiredRef = useRef(false);

  useEffect(() => {
    if (!startedAt) return;
    expiredRef.current = false;
    const startedAtDate = parseApiDate(startedAt);
    if (!startedAtDate) return;
    const endTime = startedAtDate.getTime() + durationMins * 60 * 1000;
    const tick = () => {
      const left = Math.max(0, endTime - Date.now());
      setRemaining(left);
      if (left === 0 && !expiredRef.current) {
        expiredRef.current = true;
        onExpired?.();
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startedAt, durationMins, onExpired]);

  if (remaining === null) return null;
  const total = Math.floor(remaining / 1000);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const label = h > 0
    ? `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
    : `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  const isLow = total < 300;

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-mono text-sm font-bold ${isLow ? 'bg-red-500/20 text-red-400 timer-warning' : 'bg-gray-800 text-white'}`}>
      <Clock size={14} />{label}
    </div>
  );
}

// ── Question display ───────────────────────────────────────────────────────────
function QuestionPanel({ question, answer, onAnswerChange, index, total }) {
  if (!question) return (
    <div className="flex items-center justify-center h-48 text-gray-600">
      <p>No question selected</p>
    </div>
  );

  const typeLabels = { mcq: 'MCQ', multiple_correct: 'Multiple Correct', short_answer: 'Short Answer', coding: 'Coding' };

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xs font-semibold text-gray-500">Q{index + 1} of {total}</span>
        <span className="badge-blue text-xs">{typeLabels[question.question_type] || question.question_type}</span>
        <span className="text-xs text-gray-500 ml-auto">{question.marks} mark{question.marks !== 1 ? 's' : ''}</span>
      </div>

      <p className="text-white text-base leading-relaxed mb-6 whitespace-pre-wrap">{question.question_text}</p>

      {/* MCQ */}
      {question.question_type === 'mcq' && (
        <div className="space-y-2">
          {(question.options || []).map((opt, i) => (
            <label key={i} className={`flex items-center gap-3 p-3.5 rounded-lg border cursor-pointer transition-all ${
              answer?.selected_options?.[0] === opt
                ? 'border-brand-500 bg-brand-500/10'
                : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
            }`}>
              <input type="radio" name={`q_${question.id}`} value={opt}
                checked={answer?.selected_options?.[0] === opt}
                onChange={() => onAnswerChange({ selected_options: [opt] })}
                className="accent-brand-500" />
              <span className="text-xs font-bold text-gray-500 w-5 flex-shrink-0">{String.fromCharCode(65 + i)}</span>
              <span className="text-sm text-gray-200">{opt}</span>
            </label>
          ))}
        </div>
      )}

      {/* Multiple correct */}
      {question.question_type === 'multiple_correct' && (
        <div className="space-y-2">
          <p className="text-xs text-gray-500 mb-3">Select all that apply</p>
          {(question.options || []).map((opt, i) => {
            const selected = answer?.selected_options || [];
            const isChecked = selected.includes(opt);
            return (
              <label key={i} className={`flex items-center gap-3 p-3.5 rounded-lg border cursor-pointer transition-all ${
                isChecked ? 'border-brand-500 bg-brand-500/10' : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
              }`}>
                <input type="checkbox" checked={isChecked}
                  onChange={e => {
                    const cur = [...selected];
                    onAnswerChange({ selected_options: e.target.checked ? [...cur, opt] : cur.filter(c => c !== opt) });
                  }}
                  className="accent-brand-500" />
                <span className="text-xs font-bold text-gray-500 w-5 flex-shrink-0">{String.fromCharCode(65 + i)}</span>
                <span className="text-sm text-gray-200">{opt}</span>
              </label>
            );
          })}
        </div>
      )}

      {/* Short answer */}
      {question.question_type === 'short_answer' && (
        <textarea className="input w-full resize-none" rows={6}
          placeholder="Type your answer here…"
          value={answer?.answer_text || ''}
          onChange={e => onAnswerChange({ answer_text: e.target.value })}
        />
      )}

      {/* Coding */}
      {question.question_type === 'coding' && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Write your code below:</p>
          <textarea
            className="w-full font-mono text-sm resize-none rounded-lg p-4 focus:outline-none focus:ring-2 focus:ring-brand-500 border border-gray-700"
            style={{ background: '#0d1117', color: '#e6edf3', minHeight: '240px' }}
            rows={12}
            placeholder="// Write your code here…"
            value={answer?.answer_text || ''}
            onChange={e => onAnswerChange({ answer_text: e.target.value })}
          />
        </div>
      )}
    </div>
  );
}

// ── Main ExamPage ──────────────────────────────────────────────────────────────
export default function ExamPage() {
  const { testId }  = useParams();
  const { user }    = useAuth();
  const navigate    = useNavigate();

  const [test, setTest]           = useState(null);
  const [questions, setQuestions] = useState([]);
  const [submission, setSubmission] = useState(null);
  const [answers, setAnswers]     = useState({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [flagged, setFlagged]     = useState(new Set());
  const [loading, setLoading]     = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [violationBanner, setViolationBanner] = useState(null);
  const [cameraStream, setCameraStream] = useState(null);
  const [aiStatus, setAiStatus] = useState({ mode: 'info', label: 'Starting camera…' });

  const autoSaveRef = useRef(null);
  const submissionRef = useRef(null);
  const socketRef = useRef(null);
  const submitLockRef = useRef(false);

  useEffect(() => { submissionRef.current = submission; }, [submission]);

  const sendRealtimeEvent = useCallback((payload) => {
    const socket = socketRef.current;
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  }, []);

  const handleViolationBanner = useCallback((type, desc) => {
    setViolationBanner({ type, desc });
    setTimeout(() => setViolationBanner(null), 5000);
  }, []);

  // Load exam data
  useEffect(() => {
    const load = async () => {
      try {
        const [testRes, qRes] = await Promise.all([
          api.get(`/api/tests/${testId}`),
          api.get(`/api/questions/student/test/${testId}`),
        ]);
        setTest(testRes.data);
        setQuestions(qRes.data.sort((a, b) => a.order_index - b.order_index));

        const subRes = await api.post('/api/submissions/start', { test_id: +testId });
        setSubmission(subRes.data);

        const savedRes = await api.get(`/api/submissions/${subRes.data.id}/answers`);
        const ansMap = {};
        savedRes.data.forEach(a => {
          ansMap[a.question_id] = {
            answer_text: a.answer_text,
            selected_options: a.selected_options,
          };
        });
        setAnswers(ansMap);
      } catch (err) {
        toast.error('Failed to load exam. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [testId]);

  useEffect(() => {
    let cancelled = false;

    navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: 'user',
      },
      audio: false,
    })
      .then(stream => {
        if (cancelled) {
          stream.getTracks().forEach(track => track.stop());
          return;
        }
        setCameraStream(stream);
        setAiStatus({ mode: 'info', label: 'Camera connected. AI analysis warming up…' });
      })
      .catch(() => {
        setAiStatus({ mode: 'error', label: 'Camera access failed. Proctoring cannot run.' });
        toast.error('Camera access is required for AI proctoring.', { id: 'camera-required' });
      });

    return () => {
      cancelled = true;
      setCameraStream(current => {
        current?.getTracks().forEach(track => track.stop());
        return null;
      });
    };
  }, []);

  // Auto-save every 30s
  useEffect(() => {
    autoSaveRef.current = setInterval(async () => {
      const sub = submissionRef.current;
      if (!sub || sub.is_submitted) return;
      for (const [qId, ans] of Object.entries(answers)) {
        if (!ans.answer_text && !ans.selected_options?.length) continue;
        try {
          await api.post(`/api/submissions/${sub.id}/save-answer`, {
            question_id: +qId, ...ans
          });
        } catch {}
      }
    }, 30000);
    return () => clearInterval(autoSaveRef.current);
  }, [answers]);

  const { integrityScore, violations, activeViolations, logViolation, applyRemoteViolations } = useProctoring({
    submissionId: submission?.id,
    initialIntegrityScore: submission?.integrity_score ?? 100,
    onViolation: handleViolationBanner,
    onBroadcast: sendRealtimeEvent,
  });

  useEffect(() => {
    if (!submission?.id || !cameraStream) return undefined;

    let cancelled = false;
    let timerId = null;
    let busy = false;
    const video = document.createElement('video');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d', { willReadFrequently: false });
    canvas.width = 640;
    canvas.height = 480;
    video.srcObject = cameraStream;
    video.muted = true;
    video.playsInline = true;

    const scheduleNext = (delay = 2200) => {
      if (!cancelled) {
        timerId = window.setTimeout(runFrameAnalysis, delay);
      }
    };

    const runFrameAnalysis = async () => {
      if (cancelled || busy) return;
      if (document.hidden || !navigator.onLine) {
        scheduleNext(2500);
        return;
      }
      if (video.readyState < 2 || !submissionRef.current || submissionRef.current.is_submitted) {
        scheduleNext(1200);
        return;
      }

      busy = true;
      try {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const frameB64 = canvas.toDataURL('image/jpeg', 0.72).split(',')[1];
        const response = await api.post('/api/proctoring/analyze-frame', {
          submission_id: submissionRef.current.id,
          frame_b64: frameB64,
        });

        if (cancelled) return;

        const payload = response.data || {};
        if (payload.ok === false) {
          const label = payload.note || payload.error || 'AI analysis unavailable right now.';
          setAiStatus({ mode: 'warning', label });
          scheduleNext(3500);
          return;
        }

        if (payload.note) {
          setAiStatus({ mode: 'warning', label: payload.note });
        } else {
          const checks = payload.checks_available || {};
          const activeChecks = [
            checks.face ? 'face' : null,
            checks.mesh ? 'eyes/head' : null,
            checks.yolo ? 'device' : null,
          ].filter(Boolean);
          setAiStatus({
            mode: 'info',
            label: activeChecks.length
              ? `AI live: ${activeChecks.join(', ')} monitoring active`
              : 'AI live monitoring active',
          });
        }

        applyRemoteViolations(payload.events || [], payload.integrity);
      } catch (error) {
        if (!cancelled) {
          const detail = error.response?.data?.detail || error.message || 'AI analysis request failed';
          setAiStatus({ mode: 'warning', label: detail });
        }
      } finally {
        busy = false;
        scheduleNext();
      }
    };

    const start = async () => {
      try {
        await video.play();
        setAiStatus(current => current.mode === 'error' ? current : { mode: 'info', label: 'Camera connected. AI analysis starting…' });
        scheduleNext(800);
      } catch {
        setAiStatus({ mode: 'error', label: 'Unable to start camera stream for AI analysis.' });
      }
    };

    start();

    return () => {
      cancelled = true;
      if (timerId) window.clearTimeout(timerId);
      video.pause();
      video.srcObject = null;
    };
  }, [applyRemoteViolations, cameraStream, submission?.id]);

  useEffect(() => {
    if (!submission?.id || !user?.id) return undefined;

    const socket = new WebSocket(getWsUrl(`/ws/proctor/${testId}/${user.id}`));
    socketRef.current = socket;

    socket.addEventListener('open', () => {
      const startingIntegrity = submission.integrity_score ?? 100;
      sendRealtimeEvent({
        type: 'joined',
        submission_id: submission.id,
        student_id: user.id,
        student_name: user.full_name,
        integrity_score: startingIntegrity,
        risk_level: getRiskLevel(startingIntegrity),
        started_at: submission.started_at,
        is_active: true,
        is_submitted: false,
      });
    });

    return () => {
      socketRef.current = null;
      socket.close();
    };
  }, [sendRealtimeEvent, submission?.id, submission?.started_at, testId, user?.full_name, user?.id]);

  const currentQ = questions[currentIdx];
  const currentAnswer = answers[currentQ?.id];

  const updateAnswer = (update) => {
    if (!currentQ) return;
    setAnswers(prev => ({ ...prev, [currentQ.id]: { ...(prev[currentQ.id] || {}), ...update } }));
  };

  const toggleFlag = () => {
    if (!currentQ) return;
    setFlagged(prev => { const n = new Set(prev); n.has(currentQ.id) ? n.delete(currentQ.id) : n.add(currentQ.id); return n; });
  };

  const handleSubmit = async (auto = false) => {
    if (submitLockRef.current) return;
    if (!auto && !confirm('Submit exam? You cannot change answers after submission.')) return;
    submitLockRef.current = true;
    clearInterval(autoSaveRef.current);
    setSubmitting(true);
    try {
      const answersArr = Object.entries(answers).map(([qId, ans]) => ({
        question_id: +qId,
        answer_text: ans.answer_text || null,
        selected_options: ans.selected_options || null,
      }));
      const startedAt = parseApiDate(submission?.started_at);
      const timeTaken = submission
        ? Math.max(0, Math.floor((Date.now() - (startedAt?.getTime() || Date.now())) / 1000))
        : 0;
      const submitRes = await api.post(`/api/submissions/${submission.id}/submit`, {
        answers: answersArr,
        time_taken_secs: timeTaken,
      });
      setSubmission(prev => prev ? { ...prev, ...submitRes.data, is_submitted: true } : prev);
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
      sendRealtimeEvent({
        type: 'submitted',
        submission_id: submission.id,
        student_id: user?.id,
        student_name: user?.full_name,
        integrity_score: submitRes.data.integrity_score ?? integrityScore,
        risk_level: submitRes.data.risk_level ?? getRiskLevel(integrityScore),
        percentage: submitRes.data.percentage,
        submitted_at: submitRes.data.submitted_at,
        is_active: false,
        is_submitted: true,
      });
      toast.success('Exam submitted successfully!');
      navigate(`/student/result/${submission.id}`);
    } catch {
      toast.error('Submission failed. Please try again.');
      setSubmitting(false);
      submitLockRef.current = false;
    }
  };

  const answeredCount = Object.entries(answers).filter(([, a]) =>
    a?.answer_text?.trim() || a?.selected_options?.length > 0
  ).length;

  const riskColor = integrityScore >= 80 ? 'text-emerald-400' : integrityScore >= 50 ? 'text-amber-400' : 'text-red-400';

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <Loader2 size={32} className="animate-spin text-brand-500 mx-auto mb-3" />
        <p className="text-gray-500 text-sm">Loading exam…</p>
      </div>
    </div>
  );

  if (!test || questions.length === 0) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center text-center p-4">
      <div>
        <p className="text-gray-400 text-lg font-medium">Exam not available</p>
        <p className="text-gray-600 text-sm mt-2">The test may have no questions or is inactive.</p>
        <button onClick={() => navigate('/student')} className="btn-secondary mt-4 mx-auto">Go Back</button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col select-none">
      {/* Violation banner */}
      {violationBanner && (
        <div className="fixed top-0 left-0 right-0 z-50 violation-banner">
          <div className="bg-red-600 text-white px-4 py-2.5 flex items-center gap-3 text-sm shadow-lg">
            <AlertTriangle size={16} className="flex-shrink-0" />
            <span className="font-medium">⚠ Violation detected: {violationBanner.desc}</span>
          </div>
        </div>
      )}

      {/* Top bar */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 py-2.5 flex items-center gap-3 sticky top-0 z-40">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center flex-shrink-0">
            <ShieldCheck size={14} className="text-white" />
          </div>
          <span className="text-sm font-semibold text-white truncate">{test?.title}</span>
        </div>

        {/* Progress */}
        <div className="hidden sm:flex items-center gap-2 flex-shrink-0">
          <span className="text-xs text-gray-500">{answeredCount}/{questions.length} answered</span>
          <div className="w-20 h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-brand-500 rounded-full transition-all"
              style={{ width: `${questions.length ? (answeredCount / questions.length) * 100 : 0}%` }} />
          </div>
        </div>

        {/* Integrity */}
        <div className={`flex items-center gap-1 text-xs font-semibold flex-shrink-0 ${riskColor}`} title="Integrity Score">
          <Eye size={12} />{Math.round(integrityScore)}
        </div>

        {/* Timer */}
        {test && submission && (
          <ExamTimer
            durationMins={test.duration_mins}
            startedAt={submission.started_at}
            onExpired={() => handleSubmit(true)}
          />
        )}

        <button onClick={() => handleSubmit(false)} disabled={submitting} className="btn-primary text-xs py-1.5 px-3 flex-shrink-0">
          {submitting ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
          {submitting ? 'Submitting…' : 'Submit'}
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar: webcam + violations */}
        <aside className="hidden lg:flex flex-col w-60 xl:w-64 flex-shrink-0 border-r border-gray-800 bg-gray-900/50 p-4 gap-4 overflow-y-auto">
          <WebcamPanel stream={cameraStream} activeViolations={activeViolations} aiStatus={aiStatus} />

          {/* Integrity score */}
          <div className="card p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-gray-400">Integrity Score</span>
              <span className={`text-sm font-bold ${riskColor}`}>{Math.round(integrityScore)}</span>
            </div>
            <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all duration-500 ${integrityScore >= 80 ? 'bg-emerald-500' : integrityScore >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                style={{ width: `${integrityScore}%` }} />
            </div>
            <p className={`text-xs mt-1.5 font-medium ${riskColor}`}>
              {integrityScore >= 80 ? '🟢 Low Risk' : integrityScore >= 50 ? '🟡 Medium Risk' : '🔴 High Risk'}
            </p>
          </div>

          {/* Recent violations */}
          {violations.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-2">Recent Alerts</p>
              <div className="space-y-1.5">
                {violations.slice(0, 4).map((v, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 rounded bg-red-500/10 border border-red-500/20">
                    <AlertTriangle size={11} className="text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-red-300 capitalize leading-tight">{v.violation_type?.replace(/_/g, ' ')}</p>
                      <p className="text-xs text-gray-600">{parseApiDate(v.timestamp)?.toLocaleTimeString() || ''}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Center: question */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-5 lg:p-8 max-w-3xl w-full mx-auto">
            <QuestionPanel
              question={currentQ}
              answer={currentAnswer}
              onAnswerChange={updateAnswer}
              index={currentIdx}
              total={questions.length}
            />
          </div>

          {/* Nav bar */}
          <div className="border-t border-gray-800 bg-gray-900/80 backdrop-blur px-5 py-3 flex items-center gap-3">
            <button onClick={() => setCurrentIdx(p => Math.max(0, p - 1))} disabled={currentIdx === 0} className="btn-secondary py-2">
              <ChevronLeft size={15} /> Prev
            </button>

            <button onClick={toggleFlag}
              className={`p-2 rounded-lg border text-xs transition-all ${flagged.has(currentQ?.id) ? 'border-amber-500 bg-amber-500/10 text-amber-400' : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'}`}
              title="Flag for review">
              <Flag size={14} />
            </button>

            <div className="flex-1" />

            <button onClick={() => setCurrentIdx(p => Math.min(questions.length - 1, p + 1))} disabled={currentIdx === questions.length - 1} className="btn-primary py-2">
              Next <ChevronRight size={15} />
            </button>
          </div>
        </main>

        {/* Right sidebar: question navigator */}
        <aside className="hidden md:flex flex-col w-48 xl:w-56 flex-shrink-0 border-l border-gray-800 bg-gray-900/50 p-4 overflow-y-auto">
          <p className="text-xs font-semibold text-gray-500 mb-3">Questions</p>
          <div className="grid grid-cols-5 gap-1.5">
            {questions.map((q, i) => {
              const a = answers[q.id];
              const answered = a?.answer_text?.trim() || a?.selected_options?.length > 0;
              const isCurrent = i === currentIdx;
              const isFlagged = flagged.has(q.id);
              return (
                <button key={q.id} onClick={() => setCurrentIdx(i)}
                  className={`q-pill ${isCurrent ? 'q-pill-current' : isFlagged ? 'q-pill-flagged' : answered ? 'q-pill-answered' : 'q-pill-unanswered'}`}>
                  {i + 1}
                </button>
              );
            })}
          </div>

          <div className="mt-4 space-y-1.5 text-xs text-gray-500">
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-brand-500 inline-block" /> Current</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-brand-600/40 border border-brand-600 inline-block" /> Answered</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-amber-500/30 border border-amber-500 inline-block" /> Flagged</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-gray-800 border border-gray-700 inline-block" /> Not answered</div>
          </div>

          <div className="mt-auto pt-4 space-y-2 text-xs text-gray-500 border-t border-gray-800">
            <div className="flex justify-between"><span>Answered</span><span className="text-white font-semibold">{answeredCount}/{questions.length}</span></div>
            <div className="flex justify-between"><span>Flagged</span><span className="text-amber-400 font-semibold">{flagged.size}</span></div>
            <div className="flex justify-between"><span>Remaining</span><span className="text-red-400 font-semibold">{questions.length - answeredCount}</span></div>
          </div>
        </aside>
      </div>
    </div>
  );
}
