import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, FileText, CheckCircle2, Clock, Calendar, Download, X, Search, MoreVertical, ChevronLeft, ChevronRight } from 'lucide-react';
import type { SubmittedPaper } from '../../lib/api';
import { getPaperViewUrl, getReceiptDownloadUrl } from '../../lib/api';

interface SubmissionsArchiveProps {
  submittedPapers: SubmittedPaper[];
  sessionId: string;
}

export function SubmissionsArchive({ submittedPapers, sessionId }: SubmissionsArchiveProps) {
  const [viewPaper, setViewPaper] = useState<string | null>(null);

  // Advanced Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [examTypeFilter, setExamTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('');
  
  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  // Status Styles mapping
  const getStatusStyle = (status: string) => {
    const s = (status || '').toUpperCase();
    if (s === 'COMPLETED' || s === 'SUBMITTED_TO_LMS' || s === 'SUCCESS') {
      return { bg: '#e6f4ea', color: '#137333', border: '#ceead6', label: 'Success' };
    }
    if (s === 'SUPERSEDED') {
      return { bg: '#f1f3f4', color: '#5f6368', border: '#dadce0', label: 'Superseded' };
    }
    return { bg: '#fef7e0', color: '#b06000', border: '#feebc8', label: 'Pending' };
  };

  // Unique lists for dropdowns
  const examTypes = ['all', ...Array.from(new Set(submittedPapers.map(p => p.exam_type).filter(Boolean)))];
  const statuses = ['all', 'Success', 'Pending', 'Superseded'];

  // Calculations for summary cards
  const totalSubmissions = submittedPapers.length;
  const successCount = submittedPapers.filter(p => {
    const s = (p.workflow_status || '').toUpperCase();
    return s === 'COMPLETED' || s === 'SUBMITTED_TO_LMS' || s === 'SUCCESS';
  }).length;
  const pendingCount = submittedPapers.filter(p => {
    const s = (p.workflow_status || '').toUpperCase();
    return s !== 'COMPLETED' && s !== 'SUBMITTED_TO_LMS' && s !== 'SUCCESS' && s !== 'SUPERSEDED';
  }).length;
  const supersededCount = submittedPapers.filter(p => (p.workflow_status || '').toUpperCase() === 'SUPERSEDED').length;

  // Filter papers logic
  const filteredSubmissions = submittedPapers.filter(paper => {
    const matchesSearch = 
      paper.parsed_subject_code?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      paper.subject_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      paper.original_filename?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesExamType = examTypeFilter === 'all' || paper.exam_type === examTypeFilter;

    let matchesStatus = true;
    if (statusFilter !== 'all') {
      const s = (paper.workflow_status || '').toUpperCase();
      if (statusFilter === 'Success') {
        matchesStatus = s === 'COMPLETED' || s === 'SUBMITTED_TO_LMS' || s === 'SUCCESS';
      } else if (statusFilter === 'Pending') {
        matchesStatus = s !== 'COMPLETED' && s !== 'SUBMITTED_TO_LMS' && s !== 'SUCCESS' && s !== 'SUPERSEDED';
      } else if (statusFilter === 'Superseded') {
        matchesStatus = s === 'SUPERSEDED';
      }
    }

    let matchesDate = true;
    if (dateFilter && paper.submit_timestamp) {
      const subDateStr = new Date(paper.submit_timestamp).toISOString().split('T')[0];
      matchesDate = subDateStr === dateFilter;
    }

    return matchesSearch && matchesExamType && matchesStatus && matchesDate;
  });

  // Paginated papers
  const totalPages = Math.ceil(filteredSubmissions.length / itemsPerPage) || 1;
  const paginatedSubmissions = filteredSubmissions.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const resetFilters = () => {
    setSearchQuery('');
    setExamTypeFilter('all');
    setStatusFilter('all');
    setDateFilter('');
    setCurrentPage(1);
  };

  const handleExport = () => {
    // Generate CSV and download
    const headers = ['Subject Code', 'Subject Name', 'Exam Type', 'Attempt', 'File Name', 'Submitted At', 'Status'];
    const csvRows = [headers.join(',')];
    
    filteredSubmissions.forEach(p => {
      const row = [
        p.parsed_subject_code,
        `"${p.subject_name || ''}"`,
        p.exam_type,
        p.attempt_number,
        `"${p.original_filename}"`,
        p.submit_timestamp ? new Date(p.submit_timestamp).toLocaleString() : 'N/A',
        p.workflow_status
      ];
      csvRows.push(row.join(','));
    });

    const csvContent = "data:text/csv;charset=utf-8," + csvRows.join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `submissions_archive_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header section with export & summary cards */}
      <div className="portal-card" style={{ padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div className="portal-brand-icon" style={{ width: 44, height: 44, borderRadius: 10, background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)' }}>
              <FileText size={20} color="white" />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 700, color: '#111827' }}>Submissions Archive</h2>
              <p style={{ margin: '0.15rem 0 0', color: '#6b7280', fontSize: '0.8rem' }}>Your complete submission history & transaction records</p>
            </div>
          </div>
          <button 
            onClick={handleExport}
            className="brutal-button-outline"
            style={{
              padding: '0.5rem 1rem',
              fontSize: '0.78rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem'
            }}
          >
            <Download size={14} /> Export
          </button>
        </div>

        {/* Summary Row */}
        <div className="portal-stats-row">
          {[
            { label: 'Total Submissions', value: totalSubmissions, color: '#4f46e5', bg: '#eef2ff', icon: FileText },
            { label: 'Success', value: successCount, color: '#10b981', bg: '#ecfdf5', icon: CheckCircle2 },
            { label: 'Pending', value: pendingCount, color: '#f59e0b', bg: '#fffbeb', icon: Clock },
            { label: 'Superseded', value: supersededCount, color: '#64748b', bg: '#f8fafc', icon: X }
          ].map((item, i) => {
            const Icon = item.icon;
            return (
              <div key={i} style={{
                background: 'var(--color-card)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: '0.875rem 1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                width: '100%'
              }}>
                <div style={{
                  background: `${item.color}15`,
                  color: item.color,
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  <Icon size={16} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: '1.2rem', fontWeight: 850, color: 'var(--color-foreground)', lineHeight: 1.1 }}>
                    {item.value}
                  </span>
                  <span style={{ fontSize: '0.68rem', color: 'var(--color-muted-foreground)', fontWeight: 600 }}>
                    {item.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main card with Filters & Submissions list */}
      <div className="portal-card" style={{ padding: '1.25rem 1.5rem' }}>
        {/* Advanced Filters Block */}
        <div className="portal-filters-bar" style={{
          background: 'var(--color-muted)',
          padding: '0.875rem 1rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          marginBottom: '1.25rem'
        }}>
          {/* Search bar */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-muted-foreground)' }}>Search</span>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder="Search by subject code, exam or file name..."
                value={searchQuery}
                onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
                style={{
                  width: '100%',
                  padding: '0.45rem 0.75rem 0.45rem 2rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1.5px solid var(--color-border)',
                  fontSize: 'var(--font-size-body)',
                  outline: 'none',
                  fontFamily: 'inherit',
                  background: 'var(--color-card)',
                  color: 'var(--color-foreground)'
                }}
              />
              <span style={{ position: 'absolute', left: '0.65rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-muted-foreground)' }}>
                <Search size={14} />
              </span>
            </div>
          </div>

          {/* Exam Type select */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-muted-foreground)' }}>Exam Type</span>
            <select
              value={examTypeFilter}
              onChange={(e) => { setExamTypeFilter(e.target.value); setCurrentPage(1); }}
              style={{
                width: '100%',
                padding: '0.45rem 0.75rem',
                borderRadius: 'var(--radius-sm)',
                border: '1.5px solid var(--color-border)',
                fontSize: 'var(--font-size-body)',
                outline: 'none',
                cursor: 'pointer',
                fontFamily: 'inherit',
                background: 'var(--color-card)',
                color: 'var(--color-foreground)'
              }}
            >
              {examTypes.map(type => (
                <option key={type} value={type}>
                  {type === 'all' ? 'All Types' : type}
                </option>
              ))}
            </select>
          </div>

          {/* Status select */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-muted-foreground)' }}>Status</span>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
              style={{
                width: '100%',
                padding: '0.45rem 0.75rem',
                borderRadius: 'var(--radius-sm)',
                border: '1.5px solid var(--color-border)',
                fontSize: 'var(--font-size-body)',
                outline: 'none',
                cursor: 'pointer',
                fontFamily: 'inherit',
                background: 'var(--color-card)',
                color: 'var(--color-foreground)'
              }}
            >
              {statuses.map(st => (
                <option key={st} value={st}>
                  {st === 'all' ? 'All Status' : st}
                </option>
              ))}
            </select>
          </div>

          {/* Date Picker */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-muted-foreground)' }}>Date Range</span>
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => { setDateFilter(e.target.value); setCurrentPage(1); }}
              style={{
                width: '100%',
                padding: '0.4rem 0.75rem',
                borderRadius: 'var(--radius-sm)',
                border: '1.5px solid var(--color-border)',
                fontSize: 'var(--font-size-body)',
                outline: 'none',
                fontFamily: 'inherit',
                background: 'var(--color-card)',
                color: 'var(--color-foreground)'
              }}
            />
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

        {filteredSubmissions.length === 0 ? (
          <div style={{ padding: '3.5rem 1.5rem', textAlign: 'center', background: '#f8fafc', borderRadius: '12px', color: '#64748b' }}>
            <Clock size={40} style={{ margin: '0 auto 0.75rem', opacity: 0.5 }} />
            <h3 style={{ margin: '0 0 0.25rem', fontWeight: 600, color: '#334155' }}>No submissions match your filters</h3>
            <p style={{ margin: 0, fontSize: '0.85rem' }}>Try clearing or adjusting your search query or filters.</p>
          </div>
        ) : (
          <div>
            <div style={{ overflowX: 'auto', marginBottom: '1rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '700px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
                    <th style={{ padding: '0.75rem', color: '#64748b', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Subject</th>
                    <th style={{ padding: '0.75rem', color: '#64748b', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Exam Details</th>
                    <th style={{ padding: '0.75rem', color: '#64748b', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>File Name</th>
                    <th style={{ padding: '0.75rem', color: '#1e293b', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                      Submitted At <span style={{ fontSize: '0.75rem' }}>&darr;</span>
                    </th>
                    <th style={{ padding: '0.75rem', color: '#64748b', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status</th>
                    <th style={{ padding: '0.75rem', color: '#64748b', fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedSubmissions.map((paper) => {
                    const statusStyle = getStatusStyle(paper.workflow_status);
                    const subDate = paper.submit_timestamp ? new Date(paper.submit_timestamp) : null;
                    
                    return (
                      <motion.tr 
                        key={paper.id} 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        whileHover={{ backgroundColor: 'var(--color-muted)' }}
                        style={{ borderBottom: '1px solid var(--color-border)', transition: 'background-color 0.2s ease' }}
                      >
                        {/* Subject */}
                        <td style={{ padding: '1rem 0.75rem' }}>
                          <div style={{ fontWeight: 600, color: 'var(--color-foreground)', fontSize: '0.875rem', letterSpacing: '-0.01em', fontFamily: 'var(--font-sans)' }}>
                            {paper.parsed_subject_code}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-muted-foreground)', marginTop: '0.25rem' }}>
                            {paper.subject_name || 'Subject'}
                          </div>
                        </td>

                        {/* Exam Details */}
                        <td style={{ padding: '1rem 0.75rem' }}>
                          <span style={{ 
                            background: 'var(--color-secondary)', color: 'var(--color-secondary-foreground)', fontSize: '0.7rem', 
                            padding: '0.25rem 0.5rem', borderRadius: 'var(--radius-sm)', fontWeight: 600
                          }}>
                            {paper.exam_type}
                          </span>
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-muted-foreground)', marginTop: '0.35rem', fontWeight: 500 }}>
                            Attempt {paper.attempt_number}
                          </div>
                        </td>

                        {/* File Name with PDF icon */}
                        <td style={{ padding: '1rem 0.75rem', maxWidth: '240px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <div style={{
                              background: 'var(--color-danger-bg)', color: 'var(--color-danger-fg)',
                              width: '32px', height: '32px', borderRadius: 'var(--radius-md)',
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              flexShrink: 0
                            }}>
                              <FileText size={16} />
                            </div>
                            <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--color-foreground)' }} title={paper.original_filename}>
                                {paper.original_filename}
                              </div>
                              <span style={{ fontSize: '0.75rem', color: 'var(--color-muted-foreground)' }}>PDF Document</span>
                            </div>
                          </div>
                        </td>

                        {/* Submitted At (Right Aligned) */}
                        <td style={{ padding: '1rem 0.75rem', textAlign: 'right' }}>
                          {subDate ? (
                            <div>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.35rem', color: 'var(--color-foreground)', fontSize: '0.85rem', fontWeight: 500 }}>
                                <Calendar size={13} color="var(--color-muted-foreground)" />
                                {subDate.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                              </div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--color-muted-foreground)', marginTop: '0.2rem' }}>
                                {subDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </div>
                            </div>
                          ) : (
                            <span style={{ color: 'var(--color-muted-foreground)', fontSize: '0.85rem' }}>N/A</span>
                          )}
                        </td>

                        {/* Status */}
                        <td style={{ padding: '1rem 0.75rem' }}>
                          <span style={{ 
                            background: statusStyle.bg, color: statusStyle.color, border: `1px solid ${statusStyle.border}`,
                            fontSize: '0.75rem', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontWeight: 600,
                            display: 'inline-flex', alignItems: 'center', gap: '0.35rem'
                          }}>
                            {statusStyle.label === 'Success' && <CheckCircle2 size={14} />}
                            {statusStyle.label}
                          </span>
                        </td>

                        {/* Actions (Right Aligned) */}
                        <td style={{ padding: '1rem 0.75rem', textAlign: 'right' }}>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end', width: '100%' }}>
                            {statusStyle.label === 'Success' && (
                              <motion.a
                                href={getReceiptDownloadUrl(sessionId, paper.artifact_uuid)}
                                target="_blank"
                                rel="noreferrer"
                                whileHover={{ y: -1, boxShadow: 'var(--shadow-sm)' }}
                                whileTap={{ scale: 0.98 }}
                                style={{
                                  background: 'var(--color-primary)', color: 'var(--color-primary-foreground)', border: 'none',
                                  padding: '0.375rem 0.75rem', borderRadius: 'var(--radius-md)', fontSize: '0.75rem', textDecoration: 'none',
                                  fontWeight: 500, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.35rem'
                                }}
                              >
                                <Download size={14} /> Receipt
                              </motion.a>
                            )}
                            <motion.button
                              className="portal-action-btn portal-view-btn"
                              whileHover={{ y: -1, boxShadow: 'var(--shadow-sm)', backgroundColor: 'var(--color-secondary)' }}
                              whileTap={{ scale: 0.98 }}
                              onClick={() => setViewPaper(paper.artifact_uuid)}
                              style={{
                                background: 'var(--color-card)', color: 'var(--color-foreground)', border: '1px solid var(--color-border)',
                                padding: '0.375rem 0.75rem', borderRadius: 'var(--radius-md)', fontSize: '0.75rem',
                                fontWeight: 500, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
                                transition: 'background-color 0.2s'
                              }}
                            >
                              <Eye size={14} /> View
                            </motion.button>
                            <button style={{
                              background: 'transparent', border: '1px solid transparent', color: 'var(--color-muted-foreground)', cursor: 'pointer',
                              padding: '0.375rem', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center',
                              transition: 'background-color 0.2s'
                            }}
                            onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--color-secondary)'}
                            onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                            >
                              <MoreVertical size={16} />
                            </button>
                          </div>
                        </td>
                      </motion.tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #f1f5f9', paddingTop: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
              <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>
                Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, filteredSubmissions.length)} of {filteredSubmissions.length} submissions
              </span>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <button
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  style={{
                    background: '#ffffff', border: '1.5px solid #cbd5e1',
                    borderRadius: '6px', width: '28px', height: '28px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                    opacity: currentPage === 1 ? 0.5 : 1
                  }}
                >
                  <ChevronLeft size={14} />
                </button>
                
                {Array.from({ length: totalPages }).map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentPage(idx + 1)}
                    style={{
                      background: currentPage === idx + 1 ? '#4f46e5' : '#ffffff',
                      border: currentPage === idx + 1 ? '1.5px solid #4f46e5' : '1.5px solid #cbd5e1',
                      color: currentPage === idx + 1 ? '#ffffff' : '#334155',
                      borderRadius: '6px', width: '28px', height: '28px',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      cursor: 'pointer', fontWeight: 600, fontSize: '0.78rem'
                    }}
                  >
                    {idx + 1}
                  </button>
                ))}

                <button
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  style={{
                    background: '#ffffff', border: '1.5px solid #cbd5e1',
                    borderRadius: '6px', width: '28px', height: '28px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                    opacity: currentPage === totalPages ? 0.5 : 1
                  }}
                >
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

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
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              className="portal-modal-card"
              style={{ width: '90%', maxWidth: '1000px', height: '85vh', display: 'flex', flexDirection: 'column' }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="portal-modal-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem', borderBottom: '1px solid #e2e8f0' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, color: '#1e293b' }}>
                  Submitted Examination Paper
                </h3>
                <button 
                  onClick={() => setViewPaper(null)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
                >
                  <X size={20} />
                </button>
              </div>
              <div style={{ flex: 1, background: '#f8fafc' }}>
                <iframe
                  src={getPaperViewUrl(sessionId, viewPaper)}
                  style={{ width: '100%', height: '100%', border: 'none' }}
                  title="Paper Viewer"
                />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
