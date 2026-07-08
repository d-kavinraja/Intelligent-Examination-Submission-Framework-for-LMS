import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, FileText, Clock, CheckCircle2, AlertCircle, Upload, Eye, X, BarChart3, Search } from 'lucide-react';
import type { PendingPaper, SubmittedPaper } from '../../lib/api';
import { submitPaper, getPaperViewUrl, reportPaperIssue } from '../../lib/api';

interface CourseListProps {
  pendingPapers: PendingPaper[];
  submittedPapers: SubmittedPaper[];
  sessionId: string;
  onSubmitSuccess: () => void;
}

const subjectColors = [
  { bg: 'rgba(139, 92, 246, 0.12)', border: '#8b5cf6', accent: '#8b5cf6', tag: '#ede9fe' },
  { bg: 'rgba(59, 130, 246, 0.12)', border: '#3b82f6', accent: '#3b82f6', tag: '#dbeafe' },
  { bg: 'rgba(245, 158, 11, 0.12)', border: '#f59e0b', accent: '#f59e0b', tag: '#fef3c7' },
  { bg: 'rgba(16, 185, 129, 0.12)', border: '#10b981', accent: '#10b981', tag: '#d1fae5' },
  { bg: 'rgba(239, 68, 68, 0.12)', border: '#ef4444', accent: '#ef4444', tag: '#fee2e2' },
];

function getSubjectColor(code: string) {
  const idx = code.charCodeAt(0) % subjectColors.length;
  return subjectColors[idx];
}

export function CourseList({ pendingPapers, submittedPapers, sessionId, onSubmitSuccess }: CourseListProps) {
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [submitResult, setSubmitResult] = useState<{ id: string; success: boolean; msg: string } | null>(null);
  const [viewPaper, setViewPaper] = useState<string | null>(null);
  const [reportPaper, setReportPaper] = useState<string | null>(null);
  const [reportMessage, setReportMessage] = useState('');
  const [isReporting, setIsReporting] = useState(false);

  // Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedExamType, setSelectedExamType] = useState('all');
  const [selectedAttempt, setSelectedAttempt] = useState('all');
  const [seeAll, setSeeAll] = useState(false);

  const allPapers = [
    ...pendingPapers.map(p => ({ ...p, isSubmitted: false })),
    ...submittedPapers.map(p => ({
      artifact_uuid: p.artifact_uuid,
      subject_code: p.parsed_subject_code || 'N/A',
      subject_name: p.subject_name,
      filename: p.original_filename,
      exam_type: p.exam_type,
      attempt_number: p.attempt_number,
      can_submit: false,
      isSubmitted: true,
      uploaded_at: p.uploaded_at,
      submit_timestamp: p.submit_timestamp,
    })),
  ];

  const examTypes = ['all', ...Array.from(new Set(allPapers.map(p => p.exam_type).filter(Boolean)))];
  const attempts = ['all', ...Array.from(new Set(allPapers.map(p => p.attempt_number).filter(n => n !== undefined))).sort((a, b) => Number(a) - Number(b))];

  const filteredPapers = allPapers.filter(paper => {
    const matchesSearch = 
      paper.subject_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (paper.subject_name && paper.subject_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (paper.filename && paper.filename.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesExamType = selectedExamType === 'all' || paper.exam_type === selectedExamType;
    const matchesAttempt = selectedAttempt === 'all' || String(paper.attempt_number) === selectedAttempt;

    return matchesSearch && matchesExamType && matchesAttempt;
  });

  const displayedPapers = seeAll ? filteredPapers : filteredPapers.slice(0, 4);

  const handleSubmit = async (uuid: string) => {
    setSubmitting(uuid);
    setSubmitResult(null);
    try {
      const res = await submitPaper(sessionId, uuid);
      setSubmitResult({ id: uuid, success: true, msg: res.message || 'Submitted successfully!' });
      setTimeout(() => {
        onSubmitSuccess();
        setSubmitResult(null);
      }, 2000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Submission failed';
      setSubmitResult({ id: uuid, success: false, msg });
    } finally {
      setSubmitting(null);
    }
  };

  if (allPapers.length === 0) {
    return (
      <div className="portal-card portal-courses-card">
        <div className="portal-card-header">
          <h2 className="portal-card-title">My Exam Papers</h2>
        </div>
        <div className="portal-empty-state">
          <FileText size={40} className="portal-empty-icon" />
          <p>No exam papers assigned yet.</p>
          <span>Papers will appear here once staff uploads them.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="portal-card portal-courses-card">
      <div className="portal-card-header" style={{ borderBottom: 'none', paddingBottom: '0.5rem' }}>
        <h2 className="portal-card-title">My Exam Papers</h2>
        {filteredPapers.length > 4 && (
          <button 
            className="portal-see-all"
            onClick={() => setSeeAll(!seeAll)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer' }}
          >
            {seeAll ? 'Show less' : 'See all'} 
            <ChevronRight size={14} style={{ transform: seeAll ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }} />
          </button>
        )}
      </div>

      {/* Filters Bar */}
      <div className="portal-filters-bar">
        {/* Search Bar */}
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            placeholder="Search by subject code, name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              padding: '0.5rem 1rem 0.5rem 2.25rem',
              borderRadius: 'var(--radius-sm)',
              border: '1.5px solid var(--color-border)',
              fontSize: 'var(--font-size-body)',
              outline: 'none',
              fontFamily: 'inherit',
              background: 'var(--color-card)',
              color: 'var(--color-foreground)'
            }}
          />
          <span style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-muted-foreground)' }}>
            <Search size={14} />
          </span>
        </div>

        {/* Exam Type Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-muted-foreground)', whiteSpace: 'nowrap' }}>Exam Type:</span>
          <select
            value={selectedExamType}
            onChange={(e) => setSelectedExamType(e.target.value)}
            style={{
              padding: '0.45rem 1.5rem 0.45rem 0.75rem',
              borderRadius: 'var(--radius-sm)',
              border: '1.5px solid var(--color-border)',
              fontSize: 'var(--font-size-body)',
              background: 'var(--color-card)',
              color: 'var(--color-foreground)',
              outline: 'none',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            {examTypes.map(type => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Types' : type}
              </option>
            ))}
          </select>
        </div>

        {/* Attempt Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-muted-foreground)', whiteSpace: 'nowrap' }}>Attempt:</span>
          <select
            value={selectedAttempt}
            onChange={(e) => setSelectedAttempt(e.target.value)}
            style={{
              padding: '0.45rem 1.5rem 0.45rem 0.75rem',
              borderRadius: 'var(--radius-sm)',
              border: '1.5px solid var(--color-border)',
              fontSize: 'var(--font-size-body)',
              background: 'var(--color-card)',
              color: 'var(--color-foreground)',
              outline: 'none',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            {attempts.map(attempt => (
              <option key={attempt} value={attempt}>
                {attempt === 'all' ? 'All Attempts' : `Attempt ${attempt}`}
              </option>
            ))}
          </select>
        </div>
      </div>

      {displayedPapers.length === 0 ? (
        <div className="portal-empty-state" style={{ padding: '3rem 1.5rem' }}>
          <FileText size={40} className="portal-empty-icon" />
          <p>No matching exam papers found.</p>
          <span>Try adjusting your search query or filters.</span>
        </div>
      ) : (
        <div className="portal-courses-grid">
          {displayedPapers.map((paper, idx) => {
            const color = getSubjectColor(paper.subject_code);
            const isBusy = submitting === paper.artifact_uuid;
            const result = submitResult?.id === paper.artifact_uuid ? submitResult : null;

            return (
              <motion.div
                key={paper.artifact_uuid}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                whileHover={{ y: -4, boxShadow: `0 12px 24px ${color.accent}18`, borderColor: color.accent }}
                transition={{ delay: idx * 0.05 }}
                className="portal-course-card"
                style={{ 
                  background: 'var(--color-card)', 
                  borderColor: 'var(--color-border)', 
                  borderWidth: '1px',
                  borderRadius: 'var(--radius-lg)',
                  boxShadow: 'var(--shadow-sm)',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.85rem',
                  position: 'relative',
                  minHeight: '270px',
                  transition: 'border-color 0.2s, box-shadow 0.2s'
                }}
              >
                {/* Card Header Tag & Icon */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="portal-course-tag" style={{ background: color.tag, color: color.accent, fontWeight: 700, borderRadius: 'var(--radius-sm)', fontSize: '0.68rem', padding: '0.2rem 0.5rem' }}>
                    {paper.exam_type}
                  </div>
                  <div style={{ 
                    background: `${color.accent}15`, 
                    color: color.accent,
                    width: '32px', 
                    height: '32px', 
                    borderRadius: 'var(--radius-md)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    {paper.isSubmitted
                      ? <CheckCircle2 size={16} />
                      : <FileText size={16} />}
                  </div>
                </div>

                {/* Subject info */}
                <div className="portal-course-info" style={{ flex: '1 0 auto' }}>
                  <h3 className="portal-course-code" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-foreground)', margin: '0 0 0.25rem', fontFamily: 'var(--font-sans)', letterSpacing: '-0.02em' }}>
                    {paper.subject_code}
                  </h3>
                  {paper.subject_name && (
                    <p className="portal-course-name" style={{ 
                      fontSize: '0.75rem', 
                      color: 'var(--color-muted-foreground)', 
                      margin: 0, 
                      lineHeight: 1.4, 
                      fontWeight: 500,
                      whiteSpace: 'nowrap',
                      textOverflow: 'ellipsis',
                      overflow: 'hidden',
                      display: 'block',
                      width: '100%'
                    }}>
                      {paper.subject_name}
                    </p>
                  )}
                </div>

                {/* Status bar */}
                <div className="portal-course-meta" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', borderTop: '1px solid var(--color-border)', paddingTop: '0.75rem', marginBottom: '0.25rem' }}>
                  <span className={`portal-status-badge ${paper.isSubmitted ? 'submitted' : 'pending'}`} style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    fontSize: '0.68rem',
                    fontWeight: 600,
                    padding: '0.25rem 0.5rem',
                    borderRadius: '6px',
                    background: paper.isSubmitted ? 'var(--color-success-bg)' : 'var(--color-warning-bg)',
                    color: paper.isSubmitted ? 'var(--color-success-fg)' : 'var(--color-warning-fg)'
                  }}>
                    {paper.isSubmitted
                      ? <><CheckCircle2 size={11} /> Submitted</>
                      : <><Clock size={11} /> Pending</>}
                  </span>
                  <span className="portal-attempt-badge" style={{ fontSize: '0.68rem', fontWeight: 600, color: 'var(--color-muted-foreground)', background: 'var(--color-secondary)', padding: '0.25rem 0.5rem', borderRadius: '6px' }}>
                    Attempt {paper.attempt_number}
                  </span>
                </div>

                {/* Actions */}
                <div className="portal-course-actions" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', width: '100%' }}>
                  <div style={{ display: 'flex', gap: '0.5rem', width: '100%' }}>
                    <motion.button
                      className="portal-action-btn portal-view-btn"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setViewPaper(getPaperViewUrl(sessionId, paper.artifact_uuid))}
                      style={{ 
                        flex: 1, 
                        padding: '0.45rem', 
                        borderRadius: '8px', 
                        fontSize: '0.72rem', 
                        fontWeight: 600, 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center', 
                        gap: '0.25rem', 
                        border: '1px solid #e2e8f0', 
                        background: '#f8fafc', 
                        color: '#334155', 
                        cursor: 'pointer' 
                      }}
                    >
                      <Eye size={13} /> View
                    </motion.button>

                    <motion.button
                      className="portal-action-btn portal-report-btn"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setReportPaper(paper.artifact_uuid)}
                      style={{ 
                        flex: 1, 
                        padding: '0.45rem', 
                        borderRadius: '8px', 
                        fontSize: '0.72rem', 
                        fontWeight: 600, 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center', 
                        gap: '0.25rem', 
                        border: '1px solid #ffe4e6', 
                        background: '#fff1f2', 
                        color: '#e11d48', 
                        cursor: 'pointer' 
                      }}
                    >
                      <BarChart3 size={13} /> Report
                    </motion.button>
                  </div>

                  {!paper.isSubmitted && (paper as PendingPaper).can_submit && (
                    <motion.button
                      className={`portal-action-btn portal-submit-btn ${isBusy ? 'loading' : ''}`}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleSubmit(paper.artifact_uuid)}
                      disabled={isBusy}
                      style={{
                        width: '100%',
                        padding: '0.55rem',
                        borderRadius: '8px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.35rem',
                        border: 'none',
                        background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
                        color: '#fff',
                        boxShadow: '0 4px 10px rgba(79, 70, 229, 0.2)',
                        cursor: 'pointer'
                      }}
                    >
                      <Upload size={13} />
                      {isBusy ? 'Submitting...' : 'Submit Now'}
                    </motion.button>
                  )}
                </div>

                {/* Result toast */}
                <AnimatePresence>
                  {result && (
                    <motion.div
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className={`portal-course-result ${result.success ? 'success' : 'error'}`}
                    >
                      {result.success ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                      {result.msg}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Paper viewer modal */}
      <AnimatePresence>
        {viewPaper && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="portal-modal-overlay"
            onClick={() => setViewPaper(null)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="portal-modal"
              onClick={e => e.stopPropagation()}
            >
              <div className="portal-modal-header">
                <span>Exam Paper Preview</span>
                <button onClick={() => setViewPaper(null)} className="portal-modal-close">
                  <X size={18} />
                </button>
              </div>
              <iframe
                src={viewPaper}
                className="portal-modal-iframe"
                title="Exam Paper"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Report modal */}
      <AnimatePresence>
        {reportPaper && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="portal-modal-overlay"
            onClick={() => setReportPaper(null)}
            style={{ zIndex: 1000 }}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="portal-modal"
              style={{ maxWidth: '500px', height: 'auto', padding: '2rem', textAlign: 'center' }}
              onClick={e => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
                <button onClick={() => setReportPaper(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                  <X size={20} />
                </button>
              </div>
              <div style={{ 
                background: '#fffbeb', 
                padding: '1rem', 
                borderRadius: '50%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                marginBottom: '1.25rem',
                alignSelf: 'center',
                width: '72px',
                height: '72px'
              }}>
                <AlertCircle size={40} color="#f59e0b" />
              </div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#111827', margin: '0 0 0.5rem' }}>Report an Issue</h3>
              
              {reportPaper && (() => {
                const selectedPaper = allPapers.find(p => p.artifact_uuid === reportPaper);
                if (!selectedPaper) return null;
                return (
                  <div style={{ 
                    background: '#f8fafc', 
                    border: '1px solid #e2e8f0', 
                    borderRadius: '8px', 
                    padding: '0.75rem 1rem', 
                    marginBottom: '1rem',
                    textAlign: 'left',
                    fontSize: '0.85rem'
                  }}>
                    <div style={{ fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                      Paper: {selectedPaper.subject_code} - {selectedPaper.subject_name || 'Unnamed Subject'}
                    </div>
                    <div style={{ color: '#64748b', fontSize: '0.75rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      File: {selectedPaper.filename}
                    </div>
                  </div>
                );
              })()}

              <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '1.5rem', lineHeight: 1.5 }}>
                Found an issue with this paper (e.g. wrong subject)? Send a message to staff to have it corrected.
              </p>
              
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
                    setReportPaper(null);
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
                  onClick={async () => {
                    if (!reportMessage.trim()) {
                      alert('Please enter a message to report.');
                      return;
                    }
                    setIsReporting(true);
                    try {
                      await reportPaperIssue(sessionId, reportPaper, reportMessage);
                      setSubmitResult({ id: reportPaper, success: true, msg: 'Report sent successfully' });
                      setReportPaper(null);
                      setReportMessage('');
                      setTimeout(() => setSubmitResult(null), 3000);
                    } catch (err: any) {
                      setSubmitResult({ id: reportPaper, success: false, msg: err.message || 'Failed to send report' });
                      setTimeout(() => setSubmitResult(null), 3000);
                    } finally {
                      setIsReporting(false);
                    }
                  }}
                  disabled={isReporting}
                  style={{ 
                    background: '#f59e0b', color: '#fff', border: 'none', 
                    padding: '0.6rem 1.5rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer',
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
    </div>
  );
}
