import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Loader2, WifiOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useStudentPortal } from '../lib/portalHooks';
import { PortalNavbar, type PortalTab } from '../components/portal/PortalNavbar';
import { PortalFooter } from '../components/portal/PortalFooter';
import { DashboardHeader } from '../components/portal/DashboardHeader';
import { CourseList } from '../components/portal/CourseList';
import { ActivityChart } from '../components/portal/ActivityChart';
import { TasksAndSchedule } from '../components/portal/TasksAndSchedule';
import { ReportsPanel } from '../components/portal/ReportsPanel';
import { Settings, User, FileText, BarChart3, Calendar } from 'lucide-react';

import { SubmissionsArchive } from '../components/portal/SubmissionsArchive';

export default function StudentPortal() {
  const { loading, error, session, dashboard, lastUpdated, refresh, initialized } = useStudentPortal();
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<PortalTab>('Dashboard');
  const navigate = useNavigate();

  useEffect(() => {
    if (initialized && !loading && !session) {
      navigate('/portal/student/login');
    }
  }, [initialized, loading, session, navigate]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refresh();
    setRefreshing(false);
  };

  // Loading state
  if (loading || !initialized) {
    return (
      <div className="portal-loading-screen">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="portal-loading-card"
        >
          <div className="portal-loading-brand">
            <div className="portal-brand-icon" style={{ width: 56, height: 56, borderRadius: 16 }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h2>Student Portal</h2>
          </div>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
          >
            <Loader2 size={32} className="portal-loader-icon" />
          </motion.div>
          <p className="portal-loading-text">Connecting to your dashboard...</p>
          <span className="portal-loading-sub">Authenticating with Moodle LMS</span>
        </motion.div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="portal-loading-screen">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="portal-loading-card portal-error-card"
        >
          <WifiOff size={48} className="portal-error-icon" />
          <h2 className="portal-error-title">Connection Failed</h2>
          <p className="portal-error-msg">{error}</p>
          <div className="portal-error-hints">
            <p>Make sure the backend is running:</p>
            <code>cd exam_middleware &amp;&amp; python run.py</code>
          </div>
          <motion.button
            className="portal-retry-btn"
            onClick={handleRefresh}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
          >
            Retry Connection
          </motion.button>
        </motion.div>
      </div>
    );
  }

  // Also guard if session is null for some reason
  if (!session) return null;

  const fullName = dashboard?.full_name || session?.full_name || 'Student';
  const username = dashboard?.moodle_username || session?.moodle_username || '';
  const pendingPapers = dashboard?.pending_papers || [];
  const submittedPapers = dashboard?.submitted_papers || [];

  return (
    <div className="portal-root">
      <PortalNavbar
        fullName={fullName}
        username={username}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        moodleUserId={dashboard?.moodle_user_id}
        sessionId={session?.session_id || ''}
      />

      <main className="portal-main">
        {activeTab === 'Dashboard' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <DashboardHeader
              fullName={fullName}
              totalPending={dashboard?.total_pending || 0}
              totalSubmitted={dashboard?.total_submitted || 0}
              lastUpdated={lastUpdated}
              onRefresh={handleRefresh}
              refreshing={refreshing}
              sessionId={session?.session_id || ''}
            />

            <div className="portal-grid">
              <div className="portal-left-col">
                <CourseList
                  pendingPapers={pendingPapers}
                  submittedPapers={submittedPapers}
                  sessionId={session?.session_id || ''}
                  onSubmitSuccess={handleRefresh}
                />
              </div>

              <TasksAndSchedule
                pendingPapers={pendingPapers}
                submittedPapers={submittedPapers}
                sessionId={session?.session_id || ''}
                onViewAllActivity={() => setActiveTab('Submissions')}
              />
            </div>

            {/* Tips & Actions Section */}
            <div style={{
              display: 'flex',
              gap: 'var(--portal-spacing)',
              marginTop: 'var(--portal-spacing)',
              flexWrap: 'wrap'
            }}>
              {/* Left Card: Tips & Actions list */}
              <div className="portal-card" style={{
                flex: '1 1 300px',
                padding: 'var(--portal-spacing)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.85rem'
              }}>
                <h3 style={{ 
                  margin: 0, 
                  fontSize: 'var(--font-size-section)', 
                  fontWeight: 600, 
                  color: 'var(--color-foreground)', 
                  borderBottom: '1px solid var(--color-border)', 
                  paddingBottom: '0.5rem' 
                }}>
                  Tips & Actions
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
                    <div style={{ color: 'var(--color-muted-foreground)', marginTop: '2px' }}>
                      <FileText size={15} />
                    </div>
                    <span style={{ fontSize: 'var(--font-size-body)', color: 'var(--color-muted-foreground)', fontWeight: 500 }}>
                      <strong style={{ color: 'var(--color-accent)' }}>Tip:</strong> Exam schedule check
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
                    <div style={{ color: 'var(--color-muted-foreground)', marginTop: '2px' }}>
                      <Calendar size={15} />
                    </div>
                    <span style={{ fontSize: 'var(--font-size-body)', color: 'var(--color-muted-foreground)', fontWeight: 500 }}>
                      <strong style={{ color: 'var(--color-accent)' }}>Action:</strong> Set reminders, quick-link to Calendar
                    </span>
                  </div>
                </div>
              </div>

              {/* Right Card: Quick Call-to-action banner */}
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                style={{
                  flex: '2 1 500px',
                  background: 'var(--color-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-lg)',
                  padding: 'var(--portal-spacing)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 'var(--portal-spacing)',
                  flexWrap: 'wrap',
                  boxShadow: 'var(--shadow-sm)'
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
                    <div style={{
                      background: 'var(--color-secondary)',
                      color: 'var(--color-primary)',
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A5 5 0 0 0 8 8c0 1 .3 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5" />
                        <path d="M9 18h6" />
                        <path d="M10 22h4" />
                      </svg>
                    </div>
                    <div style={{ fontSize: 'var(--font-size-body)', color: 'var(--color-muted-foreground)', fontWeight: 500 }}>
                      <strong style={{ color: 'var(--color-foreground)' }}>Tip:</strong> Set reminders, quick-link to Calendar
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
                    <div style={{
                      background: 'var(--color-warning-bg)',
                      color: 'var(--color-warning-fg)',
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                      </svg>
                    </div>
                    <div style={{ fontSize: 'var(--font-size-body)', color: 'var(--color-muted-foreground)', fontWeight: 500 }}>
                      <strong style={{ color: 'var(--color-foreground)' }}>Action:</strong> Set reminders for quick link us
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => setActiveTab('Submissions')}
                  className="brutal-button-outline"
                  style={{
                    padding: '0.5rem 1rem',
                    fontSize: 'var(--font-size-btn)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem'
                  }}
                >
                  Go to Submissions <span>&rarr;</span>
                </button>
              </motion.div>
            </div>
          </motion.div>
        )}

        {activeTab === 'Analytics' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="portal-grid" style={{ gridTemplateColumns: '1fr' }}>
            <div className="portal-left-col">
              <div className="portal-card" style={{ 
                padding: '1.25rem 2rem', 
                marginBottom: '1.25rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: '#ffffff',
                border: '1px solid rgba(0,0,0,0.06)',
                borderRadius: '16px',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div className="portal-brand-icon" style={{ width: 48, height: 48, borderRadius: 12, background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)' }}>
                    <BarChart3 size={22} color="white" />
                  </div>
                  <div>
                    <h2 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 700, color: '#111827' }}>Analytics & Insights</h2>
                    <p style={{ margin: '0.15rem 0 0', color: '#6b7280', fontSize: '0.8rem' }}>Track your submission activity over time</p>
                  </div>
                </div>
                {/* Laptop illustration on the right */}
                <div style={{ height: '70px', display: 'flex', alignItems: 'center', opacity: 0.95 }} className="portal-header-illustration">
                  <svg width="100" height="70" viewBox="0 0 120 80" fill="none">
                    <rect x="20" y="10" width="80" height="50" rx="4" fill="#1e293b" />
                    <rect x="24" y="14" width="72" height="42" fill="#ffffff" />
                    <path d="M28 48 l12 -12 l10 8 l14 -18 l14 10" fill="none" stroke="#6366f1" strokeWidth="2.5" strokeLinecap="round" />
                    <circle cx="40" cy="36" r="2" fill="#6366f1" />
                    <circle cx="50" cy="44" r="2" fill="#6366f1" />
                    <circle cx="64" cy="26" r="2" fill="#6366f1" />
                    <circle cx="78" cy="36" r="2" fill="#6366f1" />
                    <circle cx="82" cy="22" r="6" fill="none" stroke="#10b981" strokeWidth="2" />
                    <circle cx="82" cy="22" r="3" fill="#10b981" />
                    <path d="M10 60 h100 l-6 8 h-88 z" fill="#64748b" />
                    <rect x="52" y="60" width="16" height="4" fill="#475569" />
                  </svg>
                </div>
              </div>
              <ActivityChart 
                sessionId={session?.session_id || ''} 
                pendingPapers={pendingPapers}
                submittedPapers={submittedPapers}
                onTabChange={setActiveTab}
              />
            </div>
          </motion.div>
        )}

        {activeTab === 'Submissions' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <SubmissionsArchive
              submittedPapers={submittedPapers}
              sessionId={session?.session_id || ''}
            />
          </motion.div>
        )}

        {activeTab === 'Support Desk' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <ReportsPanel sessionId={session?.session_id || ''} />
          </motion.div>
        )}

        {activeTab === 'Profile' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <div className="portal-card" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '400px', textAlign: 'center' }}>
              <div style={{ background: '#f3f4f6', padding: '1.5rem', borderRadius: '50%', marginBottom: '1.5rem' }}>
                <User size={48} color="#9ca3af" />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#374151', margin: '0 0 0.5rem' }}>Student Profile</h3>
              <p style={{ color: '#6b7280', maxWidth: '400px' }}>Profile customization options are coming soon. Your identity is managed via Academia.</p>
            </div>
          </motion.div>
        )}

        {activeTab === 'Settings' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <div className="portal-card" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '400px', textAlign: 'center' }}>
              <div style={{ background: '#f3f4f6', padding: '1.5rem', borderRadius: '50%', marginBottom: '1.5rem' }}>
                <Settings size={48} color="#9ca3af" />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#374151', margin: '0 0 0.5rem' }}>Portal Settings</h3>
              <p style={{ color: '#6b7280', maxWidth: '400px' }}>Configure notifications and display preferences here in a future update.</p>
            </div>
          </motion.div>
        )}
      </main>
      <PortalFooter />
    </div>
  );
}
