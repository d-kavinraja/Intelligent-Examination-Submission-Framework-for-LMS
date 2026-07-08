import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { fetchMyReports, deleteReport, type Report } from '../../lib/api';
import { AlertCircle, CheckCircle2, Clock, Trash2, Loader2, LifeBuoy } from 'lucide-react';

interface ReportsPanelProps {
  sessionId: string;
}

export function ReportsPanel({ sessionId }: ReportsPanelProps) {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);

  useEffect(() => {
    loadReports();
  }, [sessionId]);

  const loadReports = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchMyReports(sessionId);
      setReports(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (reportId: number) => {
    if (!confirm('Are you sure you want to withdraw this report?')) return;
    try {
      setDeleting(reportId);
      await deleteReport(sessionId, reportId);
      setReports(reports.filter(r => r.id !== reportId));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to withdraw report');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="portal-grid" style={{ gridTemplateColumns: '1fr' }}>
      <div className="portal-left-col">
        <div className="portal-card" style={{ 
          padding: '1.25rem 2rem', 
          marginBottom: '1.25rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'var(--color-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div className="portal-brand-icon" style={{ width: 48, height: 48, borderRadius: 12, background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}>
              <LifeBuoy size={22} color="white" />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 700, color: 'var(--color-foreground)' }}>Support Desk</h2>
              <p style={{ margin: '0.15rem 0 0', color: 'var(--color-muted-foreground)', fontSize: '0.8rem' }}>Track your reported issues and discrepancy tickets</p>
            </div>
          </div>
        </div>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem 0' }}>
            <Loader2 className="portal-loader-icon" size={32} />
          </div>
        ) : error ? (
          <div className="portal-empty-state" style={{ padding: '3rem 1.5rem', color: 'var(--color-danger-fg)' }}>
            <AlertCircle size={40} />
            <p>{error}</p>
            <button 
              onClick={loadReports}
              style={{
                marginTop: '1rem',
                padding: '0.5rem 1rem',
                background: 'var(--color-danger-fg)',
                color: 'white',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                fontWeight: 600
              }}
            >
              Retry
            </button>
          </div>
        ) : reports.length === 0 ? (
          <div className="portal-empty-state" style={{ padding: '3rem 1.5rem' }}>
            <CheckCircle2 size={40} className="portal-empty-icon" style={{ color: 'var(--color-success-fg)' }} />
            <p>No issues reported.</p>
            <span>You can report discrepancies from your pending papers view.</span>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {reports.map((report) => (
              <motion.div
                key={report.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  background: 'var(--color-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  boxShadow: 'var(--shadow-sm)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: 'var(--color-foreground)' }}>
                      {report.parsed_subject_code || 'Unknown Subject'}
                    </h3>
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.8rem', color: 'var(--color-muted-foreground)' }}>
                      Paper: {report.original_filename || 'Unknown File'}
                    </p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {report.resolved ? (
                      <span style={{ 
                        background: 'var(--color-success-bg)', 
                        color: 'var(--color-success-fg)', 
                        padding: '0.25rem 0.75rem', 
                        borderRadius: '99px', 
                        fontSize: '0.75rem', 
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem'
                      }}>
                        <CheckCircle2 size={12} /> Resolved
                      </span>
                    ) : (
                      <span style={{ 
                        background: 'var(--color-warning-bg)', 
                        color: 'var(--color-warning-fg)', 
                        padding: '0.25rem 0.75rem', 
                        borderRadius: '99px', 
                        fontSize: '0.75rem', 
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem'
                      }}>
                        <Clock size={12} /> Pending
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ background: 'var(--color-muted)', padding: '1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', color: 'var(--color-secondary-foreground)' }}>
                  <strong>Your Report:</strong> {report.description}
                </div>

                {report.resolved && report.resolved_note && (
                  <div style={{ background: 'var(--color-success-bg)', padding: '1rem', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', color: 'var(--color-success-fg)', borderLeft: '4px solid var(--color-success-fg)' }}>
                    <strong>Staff Response:</strong> {report.resolved_note}
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem', paddingTop: '0.75rem', borderTop: '1px solid var(--color-border)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-muted-foreground)' }}>
                    Reported on {new Date(report.created_at).toLocaleDateString()}
                  </span>
                  
                  {!report.resolved && (
                    <button
                      onClick={() => handleDelete(report.id)}
                      disabled={deleting === report.id}
                      style={{
                        background: 'transparent',
                        color: 'var(--color-danger-fg)',
                        border: '1px solid var(--color-danger-fg)',
                        padding: '0.35rem 0.75rem',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: deleting === report.id ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        opacity: deleting === report.id ? 0.6 : 1
                      }}
                    >
                      {deleting === report.id ? <Loader2 size={12} className="portal-loader-icon" /> : <Trash2 size={12} />}
                      Withdraw Report
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
