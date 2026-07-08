import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Loader2, AlertCircle, User, Lock, Key, Eye, EyeOff,
  Shield, Zap, TrendingUp, Headphones, CheckCircle2
} from 'lucide-react';
import { loginStudent, fetchDashboard } from '../lib/api';

// Floating particle element
function Particle({ x, y, size, delay, color }: { x: string; y: string; size: number; delay: number; color: string }) {
  return (
    <motion.div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: size,
        height: size,
        borderRadius: '50%',
        background: color,
        opacity: 0.25,
        pointerEvents: 'none',
      }}
      animate={{ y: [0, -18, 0], opacity: [0.2, 0.45, 0.2] }}
      transition={{ duration: 3.5 + delay, repeat: Infinity, ease: 'easeInOut', delay }}
    />
  );
}

// Input field with floating icon + validation indicator
function InputField({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  icon: Icon,
  suffix,
  valid,
}: {
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  icon: React.ElementType;
  suffix?: React.ReactNode;
  valid?: boolean;
}) {
  const [focused, setFocused] = useState(false);
  const showValid = valid && value.length > 0;

  return (
    <div>
      <label style={{
        display: 'block',
        fontSize: '0.775rem',
        fontWeight: 700,
        color: '#374151',
        marginBottom: '0.4rem',
        letterSpacing: '0.01em',
      }}>
        {label}
      </label>
      <div style={{ position: 'relative' }}>
        <Icon
          size={16}
          style={{
            position: 'absolute',
            left: '0.875rem',
            top: '50%',
            transform: 'translateY(-50%)',
            color: focused ? '#6D04FF' : '#94a3b8',
            transition: 'color 0.2s',
            pointerEvents: 'none',
          }}
        />
        <input
          type={type}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={{
            width: '100%',
            padding: '0.65rem 2.5rem 0.65rem 2.6rem',
            borderRadius: '10px',
            border: `1.5px solid ${focused ? '#6D04FF' : showValid ? '#22C55E' : '#e2e8f0'}`,
            fontSize: '0.85rem',
            outline: 'none',
            fontFamily: 'inherit',
            background: focused ? '#fafafe' : '#f8faff',
            color: '#111827',
            boxSizing: 'border-box',
            transition: 'border-color 0.2s, background 0.2s',
            boxShadow: focused ? '0 0 0 3px rgba(109,4,255,0.08)' : 'none',
          }}
        />
        <div style={{ position: 'absolute', right: '0.875rem', top: '50%', transform: 'translateY(-50%)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          {showValid && <CheckCircle2 size={15} color="#22C55E" />}
          {suffix}
        </div>
      </div>
    </div>
  );
}

export default function StudentLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [registerNumber, setRegisterNumber] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const navigate = useNavigate();

  useEffect(() => { setMounted(true); }, []);

  const isUsernameValid = username.length >= 4;
  const isPasswordValid = password.length >= 6;
  const isRegNoValid = /^\d{10,12}$/.test(registerNumber);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password || !registerNumber) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const session = await loginStudent(username, password, registerNumber);
      localStorage.setItem('student_credentials', JSON.stringify({ username, password, registerNumber }));
      await fetchDashboard(session.session_id);
      navigate('/portal/student');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const benefits = [
    { title: 'Secure & Private', desc: 'Your data is protected with top security', icon: Shield },
    { title: 'Fast & Easy', desc: 'Quick access to your exam submissions', icon: Zap },
    { title: 'Track Progress', desc: 'Monitor your activity and performance', icon: TrendingUp },
    { title: 'Help & Support', desc: "We're here to help you anytime", icon: Headphones },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: 'linear-gradient(145deg, #f0f2fd 0%, #ece9ff 50%, #f4f6fb 100%)',
      fontFamily: "'Inter', 'system-ui', -apple-system, sans-serif",
      padding: '1.5rem',
      justifyContent: 'center',
      alignItems: 'center',
      boxSizing: 'border-box',
    }}>
      {/* Main card */}
      <motion.div
        initial={mounted ? { opacity: 0, y: 24 } : false}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        style={{
          width: '100%',
          maxWidth: '1040px',
          background: '#ffffff',
          borderRadius: '28px',
          boxShadow: '0 20px 60px rgba(109,4,255,0.07), 0 4px 16px rgba(0,0,0,0.05)',
          display: 'flex',
          overflow: 'hidden',
          minHeight: '600px',
          flexWrap: 'wrap',
          border: '1px solid rgba(109,4,255,0.07)',
        }}
      >
        {/* ─── LEFT PANEL: FORM ─── */}
        <div style={{
          flex: '1 1 440px',
          padding: '2.75rem 3rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          boxSizing: 'border-box',
        }}>
          {/* Brand row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '2rem' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '11px',
              background: 'linear-gradient(135deg, #6D04FF 0%, #9333ea 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 6px 16px rgba(109,4,255,0.28)',
              flexShrink: 0,
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0f172a', lineHeight: 1.1 }}>Student Portal</div>
              <div style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 500, marginTop: '1px' }}>Your gateway to academic success</div>
            </div>
          </div>

          {/* Heading */}
          <div style={{ marginBottom: '1.75rem' }}>
            <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.03em', lineHeight: 1.15 }}>
              Welcome <span style={{ color: '#6D04FF' }}>Back!</span> 👋
            </h1>
            <p style={{ margin: '0.4rem 0 0', fontSize: '0.83rem', color: '#64748b', fontWeight: 500 }}>
              Sign in to submit your exam papers
            </p>
          </div>

          {/* Error */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                animate={{ opacity: 1, height: 'auto', marginBottom: '1rem' }}
                exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                style={{
                  background: 'linear-gradient(135deg, #fff1f2, #ffe4e6)',
                  border: '1px solid #fecdd3',
                  color: '#be123c',
                  padding: '0.65rem 0.9rem',
                  borderRadius: '10px',
                  fontSize: '0.78rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontWeight: 600,
                }}
              >
                <AlertCircle size={15} />
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Form */}
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <InputField
              label="Academic Username (e.g. 22007928)"
              value={username}
              onChange={setUsername}
              placeholder="Enter username"
              icon={User}
              valid={isUsernameValid}
            />

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                <label style={{ fontSize: '0.775rem', fontWeight: 700, color: '#374151' }}>Academic Password</label>
              </div>
              <InputField
                label=""
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={setPassword}
                placeholder="Enter your password"
                icon={Lock}
                valid={isPasswordValid}
                suffix={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', display: 'flex', alignItems: 'center', padding: 0 }}
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                }
              />
            </div>

            <InputField
              label="Register Number"
              value={registerNumber}
              onChange={setRegisterNumber}
              placeholder="212222240047"
              icon={Key}
              valid={isRegNoValid}
            />

            {/* Remember me row */}
            <div style={{ display: 'flex', alignItems: 'center', marginTop: '0.15rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#64748b', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 500 }}>
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={e => setRememberMe(e.target.checked)}
                  style={{ width: '14px', height: '14px', accentColor: '#6D04FF', cursor: 'pointer', borderRadius: '4px' }}
                />
                Remember me
              </label>
            </div>

            {/* Sign In button */}
            <motion.button
              type="submit"
              disabled={loading}
              whileHover={!loading ? { scale: 1.015, boxShadow: '0 8px 20px rgba(109,4,255,0.35)' } : {}}
              whileTap={!loading ? { scale: 0.985 } : {}}
              style={{
                marginTop: '0.5rem',
                padding: '0.75rem',
                background: loading
                  ? '#a78bfa'
                  : 'linear-gradient(135deg, #6D04FF 0%, #8b3ff0 50%, #9333ea 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '11px',
                fontSize: '0.9rem',
                fontWeight: 700,
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                boxShadow: '0 6px 18px rgba(109,4,255,0.28)',
                letterSpacing: '0.01em',
                transition: 'background 0.2s',
              }}
            >
              {loading ? (
                <><Loader2 size={17} className="portal-spin" /> Signing in...</>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M13 12H3" />
                  </svg>
                  Sign In
                </>
              )}
            </motion.button>
          </form>

          {/* Secure badge */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'linear-gradient(135deg, #f8f5ff, #fafafe)',
            padding: '0.6rem 0.85rem',
            borderRadius: '10px',
            border: '1px solid #ede9fe',
            justifyContent: 'center',
            marginTop: '1.1rem',
          }}>
            <Shield size={14} color="#7c3aed" />
            <div>
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#1e1b4b' }}>Your data is secure with us</div>
              <div style={{ fontSize: '0.6rem', color: '#9ca3af', marginTop: '1px' }}>We never share your information with anyone.</div>
            </div>
          </div>
        </div>

        {/* ─── RIGHT PANEL: ILLUSTRATION ─── */}
        <div style={{
          flex: '1 1 420px',
          background: 'linear-gradient(145deg, #5b08cc 0%, #6D04FF 40%, #7c3aed 70%, #9333ea 100%)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2.5rem 2rem',
          position: 'relative',
          overflow: 'hidden',
          boxSizing: 'border-box',
        }}>
          {/* Background glow orbs */}
          <div style={{ position: 'absolute', top: '-60px', right: '-60px', width: '220px', height: '220px', borderRadius: '50%', background: 'rgba(255,255,255,0.06)', pointerEvents: 'none' }} />
          <div style={{ position: 'absolute', bottom: '-80px', left: '-40px', width: '260px', height: '260px', borderRadius: '50%', background: 'rgba(255,255,255,0.04)', pointerEvents: 'none' }} />

          {/* Floating particles */}
          {[
            { x: '8%', y: '10%', size: 10, delay: 0, color: '#c4b5fd' },
            { x: '85%', y: '18%', size: 7, delay: 0.8, color: '#fbbf24' },
            { x: '15%', y: '75%', size: 8, delay: 1.5, color: '#34d399' },
            { x: '80%', y: '70%', size: 12, delay: 0.4, color: '#c4b5fd' },
            { x: '50%', y: '6%', size: 6, delay: 1.2, color: '#f9a8d4' },
            { x: '90%', y: '45%', size: 9, delay: 0.6, color: '#a5f3fc' },
          ].map((p, i) => <Particle key={i} {...p} />)}

          {/* Floating icons around illustration */}
          {[
            { icon: '🎓', x: '10%', y: '20%', delay: 0 },
            { icon: '📋', x: '80%', y: '15%', delay: 0.5 },
            { icon: '✈️', x: '75%', y: '60%', delay: 1 },
            { icon: '📚', x: '8%', y: '65%', delay: 0.7 },
          ].map((item, i) => (
            <motion.div
              key={i}
              style={{
                position: 'absolute',
                left: item.x,
                top: item.y,
                fontSize: '1.5rem',
                filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.2))',
              }}
              animate={{ y: [0, -12, 0], rotate: [0, 8, -8, 0] }}
              transition={{ duration: 4 + i * 0.5, repeat: Infinity, ease: 'easeInOut', delay: item.delay }}
            >
              {item.icon}
            </motion.div>
          ))}

          {/* Main illustration */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}
          >
            <div style={{
              background: 'rgba(255,255,255,0.1)',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              borderRadius: '24px',
              padding: '1.5rem',
              border: '1px solid rgba(255,255,255,0.15)',
              marginBottom: '1.5rem',
              boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
            }}>
              <img
                src="/login_illustration.png"
                alt="Student studying illustration"
                style={{
                  width: '100%',
                  maxWidth: '300px',
                  height: 'auto',
                  borderRadius: '16px',
                  display: 'block',
                }}
                onError={e => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>

            {/* Carousel dots */}
            <div style={{ display: 'flex', gap: '6px', justifyContent: 'center', marginBottom: '1.25rem' }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{
                  width: i === 0 ? '20px' : '7px',
                  height: '7px',
                  borderRadius: '100px',
                  background: i === 0 ? '#ffffff' : 'rgba(255,255,255,0.35)',
                  transition: 'all 0.3s',
                }} />
              ))}
            </div>

            {/* Quote */}
            <div style={{ maxWidth: '300px', margin: '0 auto', textAlign: 'center' }}>
              <span style={{ fontSize: '2rem', lineHeight: 1, color: '#c4b5fd', fontFamily: 'serif' }}>&ldquo;</span>
              <p style={{ margin: '0.15rem 0', fontSize: '0.9rem', fontWeight: 600, color: '#ede9fe', lineHeight: 1.65 }}>
                Stay focused, keep learning,<br />
                <strong style={{ color: '#ffffff' }}>and achieve your goals.</strong>
              </p>
              <span style={{ fontSize: '2rem', lineHeight: 1, color: '#c4b5fd', fontFamily: 'serif' }}>&rdquo;</span>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* ─── BOTTOM BENEFITS BAR ─── */}
      <motion.div
        initial={mounted ? { opacity: 0, y: 16 } : false}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.25 }}
        style={{
          width: '100%',
          maxWidth: '1040px',
          background: '#ffffff',
          borderRadius: '18px',
          padding: '1rem 1.5rem',
          marginTop: '1rem',
          boxShadow: '0 4px 24px rgba(109,4,255,0.05)',
          border: '1px solid rgba(109,4,255,0.06)',
          display: 'flex',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          alignItems: 'center',
          boxSizing: 'border-box',
        }}
      >
        {benefits.map((b, idx) => {
          const BIcon = b.icon;
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flex: '1 1 180px' }}>
              <div style={{
                background: 'linear-gradient(135deg, #f5f3ff, #ede9fe)',
                color: '#7c3aed',
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                boxShadow: '0 2px 8px rgba(109,4,255,0.12)',
              }}>
                <BIcon size={16} />
              </div>
              <div>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#111827' }}>{b.title}</div>
                <div style={{ fontSize: '0.67rem', color: '#6b7280', marginTop: '1px', lineHeight: 1.4 }}>{b.desc}</div>
              </div>
            </div>
          );
        })}
      </motion.div>
    </div>
  );
}
