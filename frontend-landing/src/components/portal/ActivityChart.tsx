import React, { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  UploadCloud, 
  CheckCircle2, 
  Trash2, 
  FileText, 
  AlertCircle, 
  Calendar, 
  TrendingUp, 
  Clock, 
  Filter, 
  ChevronDown, 
  CheckSquare, 
  Info, 
  X, 
  ChevronRight,
  TrendingDown,
  Sparkles,
  Zap,
  Shield,
  Activity
} from 'lucide-react';
import { fetchActivities, fetchMyReports, reportPaperIssue } from '../../lib/api';
import type { Activity as LogActivity, Report, PendingPaper, SubmittedPaper } from '../../lib/api';

interface ActivityData {
  day: string;
  submissions: number;
  added: number;
}

interface ActivityChartProps {
  sessionId: string;
  pendingPapers?: PendingPaper[];
  submittedPapers?: SubmittedPaper[];
  onTabChange?: (tab: any) => void;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '10px',
        padding: '0.75rem',
        boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        fontSize: '0.78rem'
      }}>
        <p style={{ fontWeight: 700, margin: '0 0 0.35rem', color: '#1f2937' }}>{label}</p>
        {payload.map((entry: any) => (
          <div key={entry.name} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', margin: '0.15rem 0' }}>
            <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: entry.color }} />
            <span style={{ color: '#4b5563' }}>{entry.name}:</span>
            <strong style={{ color: '#1f2937' }}>{entry.value}</strong>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function ActivityChart({ sessionId, pendingPapers = [], submittedPapers = [], onTabChange }: ActivityChartProps) {
  const [data, setData] = useState<ActivityData[]>([]);
  const [range, setRange] = useState<'7d' | '30d'>('7d');
  const [totalSubmissions, setTotalSubmissions] = useState(0);
  const [rawActivities, setRawActivities] = useState<LogActivity[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  
  // Local reporting modal state
  const [reportingOpen, setReportingOpen] = useState(false);
  const [selectedPaperForReport, setSelectedPaperForReport] = useState('general');
  const [reportMessage, setReportMessage] = useState('');
  const [isReporting, setIsReporting] = useState(false);
  const [toast, setToast] = useState<{ success: boolean; msg: string } | null>(null);

  // Filters State
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedCia, setSelectedCia] = useState('all');
  const [dateRange, setDateRange] = useState('');

  // Calculations for summary cards
  const totalPapers = pendingPapers.length + submittedPapers.length;
  const submittedCount = submittedPapers.length;
  const pendingCount = pendingPapers.length;
  const completionRate = totalPapers > 0 ? Math.round((submittedCount / totalPapers) * 100) : 0;

  const loadActivities = async () => {
    try {
      if (!sessionId) return;
      
      const activities = await fetchActivities(sessionId);
      setRawActivities(activities);
      
      // Filter out submissions
      const submissions = activities.filter(a => a.type === 'submitted');
      setTotalSubmissions(submissions.length);
      
      const daysCount = range === '7d' ? 7 : 30;
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      const chartData: ActivityData[] = [];
      
      for (let i = daysCount - 1; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        const dayStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        
        // Count submissions on this day
        const submissionsCount = submissions.filter(s => {
          const sDate = new Date(s.timestamp);
          return sDate.getDate() === d.getDate() && sDate.getMonth() === d.getMonth() && sDate.getFullYear() === d.getFullYear();
        }).length;

        // Count added papers on this day
        const addedCount = activities.filter(a => {
          if (a.type !== 'added') return false;
          const aDate = new Date(a.timestamp);
          return aDate.getDate() === d.getDate() && aDate.getMonth() === d.getMonth() && aDate.getFullYear() === d.getFullYear();
        }).length;
        
        chartData.push({ 
          day: dayStr, 
          submissions: submissionsCount,
          added: addedCount
        });
      }
      
      setData(chartData);
    } catch (e) {
      console.error('Failed to load activities', e);
    }
  };

  const loadReports = async () => {
    try {
      if (!sessionId) return;
      const data = await fetchMyReports(sessionId);
      setReports(data);
    } catch (e) {
      console.error('Failed to load reports', e);
    }
  };

  useEffect(() => {
    loadActivities();
    loadReports();
    
    const interval = setInterval(() => {
      loadActivities();
      loadReports();
    }, 30000);
    return () => clearInterval(interval);
  }, [range, pendingPapers, submittedPapers]);

  // Unique filters data
  const uniqueSubjects = ['all', ...Array.from(new Set([
    ...pendingPapers.map(p => p.subject_code),
    ...submittedPapers.map(p => p.parsed_subject_code).filter(Boolean)
  ]))];

  const uniqueCias = ['all', ...Array.from(new Set([
    ...pendingPapers.map(p => p.exam_type),
    ...submittedPapers.map(p => p.exam_type).filter(Boolean)
  ]))];

  // Filtering activities timeline
  const filteredActivities = rawActivities.filter(act => {
    const matchesSubject = selectedSubject === 'all' || 
      act.subject_code === selectedSubject || 
      act.subject_name?.includes(selectedSubject);
      
    const matchesCia = selectedCia === 'all' || act.exam_type === selectedCia;
    
    let matchesDate = true;
    if (dateRange && act.timestamp) {
      const actDateStr = new Date(act.timestamp).toISOString().split('T')[0];
      matchesDate = actDateStr === dateRange;
    }

    return matchesSubject && matchesCia && matchesDate;
  });

  const resetFilters = () => {
    setSelectedSubject('all');
    setSelectedCia('all');
    setDateRange('');
  };

  const handleReportSubmit = async () => {
    if (!reportMessage.trim()) {
      alert('Please type a message first.');
      return;
    }
    setIsReporting(true);
    try {
      await reportPaperIssue(sessionId, selectedPaperForReport, reportMessage);
      setToast({ success: true, msg: 'Issue reported successfully! Staff will be notified.' });
      setReportMessage('');
      setReportingOpen(false);
      loadReports();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      setToast({ success: false, msg: err.message || 'Failed to submit report' });
      setTimeout(() => setToast(null), 4000);
    } finally {
      setIsReporting(false);
    }
  };

  // Recharts Chart Stats calculations
  const totalSubCount = filteredActivities.filter(a => a.type === 'submitted').length;
  const totalAddedCount = filteredActivities.filter(a => a.type === 'added').length;
  const avgSubPerDay = (totalSubCount / (range === '7d' ? 7 : 30)).toFixed(2);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', width: '100%' }}>
      {/* 1. Summary Cards row */}
      <div style={{ display: 'flex', gap: '0.875rem', flexWrap: 'wrap' }}>
        {[
          { label: 'Total Submissions', value: totalPapers, color: '#4f46e5', desc: 'All time', icon: FileText },
          { label: 'Submitted', value: submittedCount, color: '#10b981', desc: 'This period', icon: CheckCircle2 },
          { label: 'Pending', value: pendingCount, color: '#f59e0b', desc: 'This period', icon: Clock },
          { label: 'Completion Rate', value: `${completionRate}%`, color: '#06b6d4', desc: 'This period', icon: TrendingUp }
        ].map((item, i) => {
          const Icon = item.icon;
          return (
            <motion.div key={i} 
              whileHover={{ y: -2, boxShadow: 'var(--shadow-hover)' }}
              transition={{ duration: 0.2 }}
              style={{
                flex: '1 1 180px',
                background: 'var(--color-card)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                boxShadow: 'var(--shadow-md)',
                minWidth: '150px'
              }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
                <div style={{
                  background: `${item.color}15`,
                  color: item.color,
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
                  <span style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-foreground)', lineHeight: 1, fontFamily: 'var(--font-sans)', letterSpacing: '-0.02em' }}>
                    {item.value}
                  </span>
                  <span style={{ fontSize: '0.65rem', color: 'var(--color-muted-foreground)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {item.label}
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
                {item.desc}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* 2. Filters & Controls */}
      <div className="portal-filters-bar" style={{
        background: 'var(--color-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        padding: '0.875rem 1rem'
      }}>
        {/* Date Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%' }}>
          <Calendar size={15} color="var(--color-muted-foreground)" />
          <input 
            type="date" 
            value={dateRange}
            onChange={e => setDateRange(e.target.value)}
            style={{
              padding: '0.45rem',
              borderRadius: 'var(--radius-sm)',
              border: '1.5px solid var(--color-border)',
              fontSize: 'var(--font-size-body)',
              outline: 'none',
              width: '100%',
              fontFamily: 'inherit',
              background: 'var(--color-card)',
              color: 'var(--color-foreground)'
            }}
          />
        </div>

        {/* Subject Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-muted-foreground)', whiteSpace: 'nowrap' }}>Subject:</span>
          <select
            value={selectedSubject}
            onChange={e => setSelectedSubject(e.target.value)}
            style={{
              padding: '0.45rem',
              borderRadius: 'var(--radius-sm)',
              border: '1.5px solid var(--color-border)',
              fontSize: 'var(--font-size-body)',
              outline: 'none',
              width: '100%',
              cursor: 'pointer',
              fontFamily: 'inherit',
              background: 'var(--color-card)',
              color: 'var(--color-foreground)'
            }}
          >
            {uniqueSubjects.map(sub => (
              <option key={sub} value={sub}>{sub === 'all' ? 'All Subjects' : sub}</option>
            ))}
          </select>
        </div>

        {/* CIA Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-muted-foreground)', whiteSpace: 'nowrap' }}>CIA Type:</span>
          <select
            value={selectedCia}
            onChange={e => setSelectedCia(e.target.value)}
            style={{
              padding: '0.45rem',
              borderRadius: 'var(--radius-sm)',
              border: '1.5px solid var(--color-border)',
              fontSize: 'var(--font-size-body)',
              outline: 'none',
              width: '100%',
              cursor: 'pointer',
              fontFamily: 'inherit',
              background: 'var(--color-card)',
              color: 'var(--color-foreground)'
            }}
          >
            {uniqueCias.map(cia => (
              <option key={cia} value={cia}>{cia === 'all' ? 'All CIA Types' : cia}</option>
            ))}
          </select>
        </div>

        {/* Reset button */}
        <button
          onClick={resetFilters}
          className="brutal-button-outline"
          style={{
            padding: '0.45rem 1rem',
            fontSize: 'var(--font-size-btn)',
            cursor: 'pointer',
            height: '38px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
          }}
        >
          Reset
        </button>
      </div>

      {/* 3. Improved Area Chart Card */}
      <div className="portal-card" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700, color: '#111827' }}>Activities Overview</h3>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '0.35rem', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.7rem', color: '#64748b' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#4f46e5' }} />
                Submissions
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.7rem', color: '#64748b' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }} />
                Papers Added by Staff
              </div>
            </div>
          </div>

          {/* Time range toggler */}
          <div style={{ display: 'flex', background: '#f1f5f9', borderRadius: '8px', padding: '2px' }}>
            {[
              { label: 'Last 7 Days', value: '7d' },
              { label: 'Last 30 Days', value: '30d' }
            ].map(item => (
              <button
                key={item.value}
                onClick={() => setRange(item.value as any)}
                style={{
                  background: range === item.value ? '#ffffff' : 'none',
                  border: 'none',
                  color: range === item.value ? '#4f46e5' : '#64748b',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '0.35rem 0.75rem',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  boxShadow: range === item.value ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                  transition: 'all 0.15s'
                }}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Recharts Area Chart */}
        <div style={{ width: '100%', height: '200px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorSubmissions" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorAdded" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="submissions" name="Submissions" stroke="#4f46e5" strokeWidth={2} fillOpacity={1} fill="url(#colorSubmissions)" dot={{ r: 3, fill: '#4f46e5' }} />
              <Area type="monotone" dataKey="added" name="Papers Added" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorAdded)" dot={{ r: 3, fill: '#10b981' }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Stats below chart */}
        <div style={{ display: 'flex', gap: '1rem', borderTop: '1px solid #f1f5f9', marginTop: '1rem', paddingTop: '1rem', flexWrap: 'wrap' }}>
          {[
            { label: 'Total Submissions', value: totalSubCount, color: '#4f46e5' },
            { label: 'Papers Added by Staff', value: totalAddedCount, color: '#10b981' },
            { label: 'Average per Day', value: avgSubPerDay, color: '#6366f1' }
          ].map((stat, i) => (
            <div key={i} style={{ flex: '1 1 120px', minWidth: '100px' }}>
              <span style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 600 }}>{stat.label}</span>
              <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#1f2937', marginTop: '0.15rem' }}>{stat.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Enhanced Activity Timeline */}
      <div className="portal-card" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700, color: '#111827' }}>Activity History</h3>
          <button style={{
            background: 'none', border: '1px solid #e2e8f0', padding: '0.35rem 0.75rem', borderRadius: '6px',
            fontSize: '0.75rem', fontWeight: 700, color: '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem'
          }}>
            <Filter size={13} /> Filter
          </button>
        </div>

        {filteredActivities.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', background: '#f8fafc', borderRadius: '12px', color: '#64748b', fontSize: '0.8rem' }}>
            No matching activity found in this period.
          </div>
        ) : (
          <div style={{ position: 'relative' }}>
            {/* Timeline Line */}
            <div style={{ position: 'absolute', left: '79px', top: '10px', bottom: '10px', width: '2px', background: '#e2e8f0', zIndex: 1 }} />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'relative', zIndex: 2 }}>
              {filteredActivities.slice(0, 5).map((act, idx) => {
                const d = new Date(act.timestamp);
                let themeColor = '#4f46e5'; // Blue
                let title = 'Paper Added by Staff';
                let Icon = UploadCloud;
                let badgeLabel = 'ADDED';
                
                if (act.type === 'submitted') {
                  themeColor = '#10b981'; // Green
                  title = 'Paper Submitted by Student';
                  Icon = CheckSquare;
                  badgeLabel = 'SUBMISSION';
                } else if (act.type === 'removed') {
                  themeColor = '#ef4444'; // Red
                  title = 'Paper Removed by Staff';
                  Icon = Trash2;
                  badgeLabel = 'REMOVED';
                }

                return (
                  <div key={idx} style={{ display: 'flex', alignItems: 'flex-start' }}>
                    {/* Time (Left) */}
                    <div style={{ width: '70px', textAlign: 'right', paddingRight: '0.75rem', paddingTop: '6px', fontSize: '0.7rem' }}>
                      <div style={{ fontWeight: 700, color: '#334155' }}>
                        {d.getMonth() + 1}/{d.getDate()}/{d.getFullYear()}
                      </div>
                      <div style={{ color: '#94a3b8', fontSize: '0.65rem', marginTop: '1px' }}>
                        {d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>

                    {/* Dot Indicator (Middle) */}
                    <div style={{ width: '20px', display: 'flex', justifyContent: 'center', position: 'relative' }}>
                      <div style={{
                        width: '10px', height: '10px', borderRadius: '50%', backgroundColor: themeColor,
                        border: '2px solid #ffffff', boxShadow: '0 0 0 2px rgba(0,0,0,0.05)', marginTop: '8px', zIndex: 3
                      }} />
                    </div>

                    {/* Card content (Right) */}
                    <div style={{ flex: 1, paddingLeft: '0.5rem' }}>
                      <div style={{
                        background: '#ffffff', border: '1.5px solid #e2e8f0', borderLeft: `3px solid ${themeColor}`,
                        borderRadius: '10px', padding: '0.75rem 1rem', boxShadow: '0 1px 2px rgba(0,0,0,0.01)'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
                          <Icon size={14} color={themeColor} />
                          <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#1e293b' }}>{title}</span>
                          <span style={{
                            fontSize: '0.6rem', fontWeight: 800, padding: '0.15rem 0.4rem', borderRadius: '4px',
                            background: `${themeColor}12`, color: themeColor
                          }}>
                            {badgeLabel}
                          </span>
                        </div>
                        <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem', color: '#4b5563', lineHeight: 1.4 }}>
                          {act.student_name ? `${act.student_name} submitted ` : ''}
                          <strong>{act.subject_code} ({act.exam_type})</strong>
                        </p>
                        <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                          Subject: {act.subject_name || 'Subject'}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ display: 'flex', justifyContent: 'center', borderTop: '1px solid #f1f5f9', marginTop: '0.875rem', paddingTop: '0.875rem' }}>
              <button 
                onClick={() => onTabChange && onTabChange('Submissions')}
                style={{
                  background: 'none', border: 'none', color: '#4f46e5', fontSize: '0.78rem', fontWeight: 700,
                  cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.2rem'
                }}
              >
                View All Activity <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 5. My Reports (Empty State & list) */}
      <div className="portal-card" style={{ padding: '1.25rem 1.5rem' }}>
        <h3 style={{ margin: '0 0 1.25rem', fontSize: '0.9375rem', fontWeight: 700, color: '#111827' }}>My Reports</h3>
        
        {reports.length === 0 ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '1.5rem 2rem',
            gap: '2rem',
            flexWrap: 'wrap'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
              <div style={{ flexShrink: 0 }}>
                {/* Clipboard illustration SVG */}
                <svg width="70" height="70" viewBox="0 0 100 100" fill="none">
                  <rect x="25" y="15" width="50" height="70" rx="10" fill="#e0e7ff" />
                  <rect x="35" y="8" width="30" height="12" rx="4" fill="#4f46e5" />
                  <circle cx="50" cy="14" r="3" fill="#ffffff" />
                  <rect x="35" y="35" width="30" height="4" rx="2" fill="#a5b4fc" />
                  <rect x="35" y="47" width="20" height="4" rx="2" fill="#a5b4fc" />
                  <rect x="35" y="59" width="25" height="4" rx="2" fill="#a5b4fc" />
                  <circle cx="68" cy="68" r="14" fill="#ffffff" stroke="#4f46e5" strokeWidth="3" />
                  <line x1="77.5" y1="77.5" x2="88" y2="88" stroke="#4f46e5" strokeWidth="4" strokeLinecap="round" />
                </svg>
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#1f2937' }}>No issues reported yet</h4>
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.82rem', color: '#6b7280' }}>
                  Help us improve by reporting any problems you face.
                </p>
              </div>
            </div>
            <button 
              onClick={() => setReportingOpen(true)}
              style={{
                background: '#4f46e5',
                color: '#ffffff',
                border: 'none',
                padding: '0.55rem 1.25rem',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '0.8rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                boxShadow: '0 4px 10px rgba(79, 70, 229, 0.2)',
                transition: 'background 0.15s'
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#4338ca'}
              onMouseLeave={e => e.currentTarget.style.background = '#4f46e5'}
            >
              Report an Issue
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
            {reports.map((rep) => {
              const d = new Date(rep.created_at);
              const isResolved = rep.resolved;
              
              return (
                <div key={rep.id} style={{ 
                  display: 'flex', alignItems: 'flex-start', gap: '1rem', 
                  padding: '1rem', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px',
                  borderLeft: `4px solid ${isResolved ? '#10b981' : '#f59e0b'}`
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <div>
                        <h4 style={{ margin: 0, fontWeight: 700, color: '#1e293b', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          Report #{rep.id}
                          <span style={{ 
                            fontSize: '0.7rem', padding: '0.15rem 0.5rem', borderRadius: '6px', fontWeight: 700,
                            background: isResolved ? '#e6f4ea' : '#fff7e0',
                            color: isResolved ? '#137333' : '#b06000'
                          }}>
                            {isResolved ? 'Resolved' : 'Pending'}
                          </span>
                        </h4>
                        <p style={{ margin: '0.25rem 0 0', color: '#64748b', fontSize: '0.78rem' }}>
                          Subject: {rep.parsed_subject_code || 'N/A'} | Paper: {rep.original_filename || 'Unknown'}
                        </p>
                      </div>
                      <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                        {d.toLocaleDateString()} {d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    
                    <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '8px', fontSize: '0.8rem', color: '#334155', border: '1px solid #e2e8f0' }}>
                      <strong>Your Message:</strong> {rep.description}
                    </div>
                    
                    {isResolved && (
                      <div style={{ marginTop: '0.5rem', background: '#e6f4ea', padding: '0.75rem', borderRadius: '8px', fontSize: '0.8rem', color: '#137333', border: '1px solid #ceead6' }}>
                        <strong>Staff Reply:</strong> {rep.resolved_note || 'Resolved.'}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            <button 
              onClick={() => setReportingOpen(true)}
              style={{
                alignSelf: 'flex-start', background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1',
                padding: '0.45rem 1rem', borderRadius: '8px', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer', marginTop: '0.5rem'
              }}
            >
              Report another issue
            </button>
          </div>
        )}
      </div>

      {/* 7. Bottom benefits row */}
      <div style={{
        display: 'flex',
        gap: '0.875rem',
        background: '#ffffff',
        border: '1px solid rgba(0,0,0,0.06)',
        borderRadius: '16px',
        padding: '1rem',
        boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
        flexWrap: 'wrap',
        alignItems: 'center'
      }}>
        <div style={{
          background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
          color: '#ffffff',
          padding: '0.6rem 1.25rem',
          borderRadius: '12px',
          fontWeight: 800,
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.35rem',
          minHeight: '44px'
        }}>
          <Sparkles size={16} /> Benefits
        </div>
        
        <div style={{ display: 'flex', flex: 1, justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          {[
            { title: 'Better insights', desc: 'Understand your activity at a glance', icon: Zap },
            { title: 'Faster actions', desc: 'Quick filters and clear information', icon: Shield },
            { title: 'Improved experience', desc: 'Clean UI for better usability', icon: CheckSquare },
            { title: 'Data clarity', desc: 'Visuals that help you track progress', icon: Activity }
          ].map((benefit, idx) => {
            const BIcon = benefit.icon;
            return (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flex: '1 1 180px' }}>
                <div style={{ background: '#f5f3ff', color: '#6366f1', width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <BIcon size={14} />
                </div>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#1f2937' }}>{benefit.title}</div>
                  <div style={{ fontSize: '0.68rem', color: '#6b7280', marginTop: '1px' }}>{benefit.desc}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Local Issue Reporting Modal */}
      <AnimatePresence>
        {reportingOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="portal-modal-overlay"
            onClick={() => setReportingOpen(false)}
            style={{ zIndex: 1000 }}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              className="portal-modal"
              style={{ maxWidth: '500px', height: 'auto', padding: '2rem', textAlign: 'center' }}
              onClick={e => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
                <button onClick={() => setReportingOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                  <X size={20} />
                </button>
              </div>
              <div style={{ background: '#fffbeb', padding: '1rem', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem', alignSelf: 'center', width: '72px', height: '72px' }}>
                <AlertCircle size={40} color="#f59e0b" />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#111827', margin: '0 0 0.5rem' }}>Report an Issue</h3>
              <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '1.5rem', lineHeight: 1.5 }}>
                Found an issue with a paper or the portal? Describe the problem below.
              </p>

              {/* Subject Paper Selector */}
              <div style={{ textAlign: 'left', marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#4b5563', display: 'block', marginBottom: '0.35rem' }}>Select Relevant Paper:</span>
                <select
                  value={selectedPaperForReport}
                  onChange={e => setSelectedPaperForReport(e.target.value)}
                  style={{
                    width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1.5px solid #cbd5e1', fontSize: '0.8rem', fontFamily: 'inherit', background: '#fff'
                  }}
                >
                  <option value="general">General Portal Issue</option>
                  {[...pendingPapers, ...submittedPapers].map(p => {
                    const code = p.subject_code || (p as any).parsed_subject_code;
                    const uuid = p.artifact_uuid;
                    return (
                      <option key={uuid} value={uuid}>
                        {code} - {p.exam_type} (Attempt {p.attempt_number})
                      </option>
                    );
                  })}
                </select>
              </div>

              <textarea 
                placeholder="Type your message here..."
                value={reportMessage}
                onChange={(e) => setReportMessage(e.target.value)}
                style={{
                  width: '100%', minHeight: '100px', padding: '0.75rem', borderRadius: '8px', 
                  border: '1.5px solid #e2e8f0', fontSize: '0.875rem', marginBottom: '1.5rem',
                  resize: 'vertical', fontFamily: 'inherit'
                }}
              />
              
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                <button 
                  onClick={() => {
                    setReportingOpen(false);
                    setReportMessage('');
                  }}
                  disabled={isReporting}
                  style={{ 
                    background: '#f8fafc', color: '#64748b', border: '1px solid #e2e8f0', 
                    padding: '0.6rem 1.5rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer',
                    opacity: isReporting ? 0.7 : 1
                  }}
                >
                  Cancel
                </button>
                <button 
                  onClick={handleReportSubmit}
                  disabled={isReporting}
                  style={{ 
                    background: '#4f46e5', color: '#fff', border: 'none', 
                    padding: '0.6rem 1.5rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer',
                    boxShadow: '0 4px 10px rgba(79, 70, 229, 0.2)',
                    opacity: isReporting ? 0.7 : 1
                  }}
                >
                  {isReporting ? 'Sending...' : 'Send Report'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Global Toast for alerts */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            style={{
              position: 'fixed', bottom: '2rem', right: '2rem',
              background: toast.success ? '#10b981' : '#ef4444',
              color: '#ffffff', padding: '0.75rem 1.5rem', borderRadius: '8px',
              fontSize: '0.85rem', fontWeight: 700, boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              zIndex: 9999, display: 'flex', alignItems: 'center', gap: '0.5rem'
            }}
          >
            {toast.success ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
