import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, CheckSquare, FileText, Upload, AlertTriangle, PlusCircle, Trash2, ChevronRight } from 'lucide-react';
import { fetchActivities } from '../../lib/api';
import type { PendingPaper, SubmittedPaper, Activity } from '../../lib/api';

interface TasksAndScheduleProps {
  pendingPapers: PendingPaper[];
  submittedPapers: SubmittedPaper[];
  sessionId: string;
  onViewAllActivity?: () => void;
}

function formatTime(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function getDateLabel(dateStr: string): string {
  const d = new Date(dateStr);
  const today = new Date();
  const diff = Math.floor((today.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Yesterday';
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

export function TasksAndSchedule({ pendingPapers, submittedPapers, sessionId, onViewAllActivity }: TasksAndScheduleProps) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loadingActivities, setLoadingActivities] = useState(true);

  useEffect(() => {
    async function loadActivities() {
      try {
        if (sessionId) {
          const acts = await fetchActivities(sessionId);
          setActivities(acts);
        }
      } catch (e) {
        console.error('Failed to load activity history', e);
      } finally {
        setLoadingActivities(false);
      }
    }
    loadActivities();
    
    const interval = setInterval(loadActivities, 30000);
    return () => clearInterval(interval);
  }, [pendingPapers, submittedPapers]);

  // Tasks from papers
  const tasks = [
    ...pendingPapers.map(p => ({
      id: p.artifact_uuid,
      label: 'Waiting for student to submit',
      sub: `${p.subject_name || p.subject_code} • ${p.exam_type} • Uploaded by staff`,
      icon: Clock,
      done: false,
      warn: !p.can_submit,
      status: 'Pending',
    })),
    ...submittedPapers.map(p => ({
      id: p.artifact_uuid,
      label: 'Submitted successfully',
      sub: `${p.subject_name || p.parsed_subject_code} • ${p.exam_type} • ${p.submit_timestamp ? 'Submitted at ' + formatTime(p.submit_timestamp) : 'Submitted'}`,
      icon: CheckSquare,
      done: true,
      warn: false,
      status: 'Success',
    })),
  ];

  return (
    <div className="portal-right-panel" style={{ width: '100%' }}>
      {/* Activity History Timeline */}
      <div className="portal-card portal-schedule-card">
        <div className="portal-card-header" style={{ marginBottom: '1.25rem' }}>
          <div>
            <h2 className="portal-card-title">Activity History</h2>
            <p className="portal-schedule-sub" style={{ margin: '0.15rem 0 0', fontSize: '0.75rem', color: '#64748b' }}>Recent timeline</p>
          </div>
        </div>

        <div className="portal-schedule-timeline" style={{ paddingRight: '0.25rem', position: 'relative' }}>
          {loadingActivities ? (
            <div style={{ padding: '1rem', color: '#9ca3af', fontSize: '0.8rem', textAlign: 'center' }}>Loading activities...</div>
          ) : activities.length === 0 ? (
            <div style={{ padding: '1.5rem 1rem', color: '#9ca3af', fontSize: '0.8rem', textAlign: 'center' }}>No recent activity.</div>
          ) : (
            <div style={{ position: 'relative' }}>
              {/* Vertical line running down middle-left */}
              <div style={{
                position: 'absolute',
                left: '69px',
                top: '10px',
                bottom: '10px',
                width: '2px',
                background: '#e2e8f0',
                zIndex: 1
              }} />

              {activities.slice(0, 4).map((act, i) => {
                let themeColor = '#6366f1';
                let bgTheme = '#ffffff';
                let title = 'Paper Added by Staff';
                let Icon = PlusCircle;
                
                if (act.type === 'submitted') {
                  themeColor = '#10b981';
                  title = 'Paper Submitted';
                  Icon = CheckSquare;
                } else if (act.type === 'removed') {
                  themeColor = '#ef4444';
                  title = 'Paper Removed';
                  Icon = Trash2;
                }

                return (
                  <div key={i} style={{ display: 'flex', marginBottom: '1rem', position: 'relative', zIndex: 2 }}>
                    {/* Time Column (Left) */}
                    <div style={{ width: '60px', textAlign: 'right', fontSize: '0.72rem', paddingRight: '0.5rem', paddingTop: '4px' }}>
                      <div style={{ fontWeight: 700, color: '#334155' }}>{getDateLabel(act.timestamp)}</div>
                      <div style={{ color: '#94a3b8', fontSize: '0.65rem' }}>{formatTime(act.timestamp)}</div>
                    </div>

                    {/* Timeline Line Dot (Middle) */}
                    <div style={{ width: '20px', display: 'flex', justifyContent: 'center', position: 'relative' }}>
                      <div style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        backgroundColor: themeColor,
                        border: '2px solid #ffffff',
                        boxShadow: '0 0 0 2px rgba(0,0,0,0.05)',
                        marginTop: '8px',
                        zIndex: 3
                      }} />
                    </div>

                    {/* Event Block (Right) */}
                    <div style={{ flex: 1, paddingLeft: '0.5rem' }}>
                      <motion.div
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        style={{
                          background: 'var(--color-card)',
                          border: '1px solid var(--color-border)',
                          borderLeft: `3px solid ${themeColor}`,
                          borderRadius: 'var(--radius-lg)',
                          padding: '1rem',
                          boxShadow: 'var(--shadow-sm)'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                          <Icon size={14} color={themeColor} />
                          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-foreground)', fontFamily: 'var(--font-sans)' }}>{title}</span>
                        </div>
                        <ul style={{ margin: 0, paddingLeft: '1.25rem', listStyleType: 'disc', fontSize: '0.75rem', color: 'var(--color-muted-foreground)', lineHeight: 1.5 }}>
                          {act.student_name && (
                            <li>Student: <span style={{ fontWeight: 600, color: 'var(--color-foreground)' }}>{act.student_name}</span></li>
                          )}
                          <li>Subject: {act.subject_name || act.subject_code}</li>
                          <li>Exam: {act.exam_type}</li>
                        </ul>
                      </motion.div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {onViewAllActivity && (
          <div style={{ display: 'flex', justifyContent: 'center', borderTop: '1px solid #f1f5f9', marginTop: '0.75rem', paddingTop: '0.75rem' }}>
            <button 
              onClick={onViewAllActivity}
              style={{
                background: 'none',
                border: 'none',
                color: '#6366f1',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.2rem',
                padding: '0.25rem 0.5rem',
                borderRadius: '6px',
                transition: 'background 0.15s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#f5f3ff'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
            >
              View all activity <ChevronRight size={13} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
