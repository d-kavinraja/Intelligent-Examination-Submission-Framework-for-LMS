import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Clock, Award, BookOpen, RefreshCw } from 'lucide-react';

interface DashboardHeaderProps {
  fullName: string;
  totalPending: number;
  totalSubmitted: number;
  lastUpdated: Date | null;
  onRefresh: () => void;
  refreshing?: boolean;
  sessionId?: string;
}

export function DashboardHeader({
  fullName,
  totalPending,
  totalSubmitted,
  lastUpdated,
  onRefresh,
  refreshing,
  sessionId,
}: DashboardHeaderProps) {
  const firstName = fullName?.split(' ')[0] || 'Student';
  const totalPapers = totalPending + totalSubmitted;
  const completionRate = totalPapers > 0 ? Math.round((totalSubmitted / totalPapers) * 100) : 0;

  const defaultAvatar = "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?q=80&w=256&auto=format&fit=crop";
  const [avatarSrc, setAvatarSrc] = useState(
    sessionId ? `http://localhost:8000/student/avatar?session=${sessionId}` : defaultAvatar
  );

  useEffect(() => {
    if (sessionId) {
      setAvatarSrc(`http://localhost:8000/student/avatar?session=${sessionId}`);
    }
  }, [sessionId]);

  const stats = [
    {
      value: totalPapers.toString(),
      label: 'Total Papers',
      icon: BookOpen,
      color: '#6366f1',
    },
    {
      value: `${completionRate}%`,
      label: 'Completion rate',
      icon: TrendingUp,
      color: '#10b981',
    },
    {
      value: totalSubmitted.toString(),
      label: 'Submitted',
      icon: Award,
      color: '#f59e0b',
    },
    {
      value: totalPending.toString(),
      label: 'Pending',
      icon: Clock,
      color: '#ef4444',
    },
  ];

  return (
    <div className="portal-header-section flex flex-col lg:flex-row justify-between items-stretch lg:items-center gap-6 mb-6 w-full">
      <div className="portal-welcome flex flex-col sm:flex-row items-center text-center sm:text-left gap-4">
        <img 
          src={avatarSrc}
          alt={firstName}
          onError={() => {
            if (avatarSrc !== defaultAvatar) {
              setAvatarSrc(defaultAvatar);
            }
          }}
          style={{
            width: '52px',
            height: '52px',
            borderRadius: '50%',
            objectFit: 'cover',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            flexShrink: 0
          }}
        />
        <div>
          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="portal-welcome-title"
            style={{ fontSize: 'var(--font-size-heading)', fontWeight: 700, color: 'var(--color-foreground)', margin: 0, letterSpacing: '-0.02em' }}
          >
            Hi {firstName}, welcome back! 👋
          </motion.h1>
          <p className="portal-welcome-subtitle" style={{ margin: '0.2rem 0 0', color: 'var(--color-muted-foreground)', fontSize: 'var(--font-size-body)', fontWeight: 500 }}>
            Check your progress and complete pending submissions to stay on track.
          </p>
          {lastUpdated && (
            <div className="portal-last-updated flex flex-col sm:flex-row items-center gap-2 mt-2">
              <span style={{ fontSize: 'var(--font-size-body)', color: 'var(--color-muted-foreground)' }}>Last updated: {lastUpdated.toLocaleTimeString()}</span>
              <motion.button
                onClick={onRefresh}
                className="portal-refresh-btn"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95, rotate: 180 }}
              >
                <RefreshCw size={12} className={refreshing ? 'portal-spin' : ''} />
                Refresh
              </motion.button>
            </div>
          )}
        </div>
      </div>

      <div className="portal-stats-row grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 w-full gap-4">
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ y: -2, boxShadow: 'var(--shadow-hover)' }}
              transition={{ delay: i * 0.08, duration: 0.2 }}
              className="portal-stat-item"
              style={{
                background: 'var(--color-card)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-md)',
                borderRadius: 'var(--radius-lg)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                textAlign: 'left',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
                <div style={{
                  background: `${stat.color}15`,
                  color: stat.color,
                  width: '42px',
                  height: '42px',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  <Icon size={20} strokeWidth={2.5} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                  <span style={{
                    fontSize: '1.75rem',
                    fontWeight: 700,
                    color: 'var(--color-foreground)',
                    lineHeight: 1,
                    fontFamily: 'var(--font-sans)',
                    letterSpacing: '-0.02em'
                  }}>
                    {stat.value}
                  </span>
                  <span style={{
                    fontSize: '0.65rem',
                    color: 'var(--color-muted-foreground)',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    {stat.label}
                  </span>
                </div>
              </div>
              
              <div style={{ 
                borderTop: '1px solid var(--color-border)', 
                paddingTop: '0.75rem', 
                fontSize: '0.65rem', 
                color: 'var(--color-muted-foreground)', 
                fontWeight: 500,
                textAlign: 'center',
                background: 'var(--color-muted)',
                margin: '0.5rem -1.25rem -1.25rem -1.25rem',
                paddingBottom: '0.75rem'
              }}>
                Last 30 days
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
