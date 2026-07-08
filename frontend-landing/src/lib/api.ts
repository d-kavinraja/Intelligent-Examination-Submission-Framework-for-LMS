/**
 * API utilities for the Student Portal
 * Connects to the exam_middleware backend at localhost:8000
 */

const API_BASE = 'http://localhost:8000';

export interface LoginResponse {
  session_id: string;
  moodle_username: string;
  full_name: string;
  register_number?: string;
}

export interface PendingPaper {
  artifact_uuid: string;
  subject_code: string;
  subject_name?: string;
  assignment_name?: string;
  filename: string;
  uploaded_at: string;
  workflow_status?: string;
  exam_type: string;
  attempt_number: number;
  attempt_2_locked: boolean;
  can_submit: boolean;
  message?: string;
  target_site_url?: string;
}

export interface SubmittedPaper {
  id: number;
  artifact_uuid: string;
  raw_filename: string;
  original_filename: string;
  subject_name?: string;
  parsed_reg_no?: string;
  parsed_subject_code?: string;
  exam_type: string;
  attempt_number: number;
  workflow_status: string;
  uploaded_at: string;
  submit_timestamp?: string;
}

export interface DashboardData {
  moodle_user_id: number;
  moodle_username: string;
  full_name: string;
  pending_papers: PendingPaper[];
  submitted_papers: SubmittedPaper[];
  total_pending: number;
  total_submitted: number;
}

export async function loginStudent(
  username: string,
  password: string,
  registerNumber: string
): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/auth/student/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username,
      password,
      register_number: registerNumber,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }

  return res.json();
}

export async function fetchDashboard(sessionId: string): Promise<DashboardData> {
  const res = await fetch(`${API_BASE}/student/dashboard`, {
    headers: {
      'X-Session-ID': sessionId,
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch dashboard');
  }

  return res.json();
}

export async function submitPaper(sessionId: string, artifactUuid: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/student/submit/${artifactUuid}`, {
    method: 'POST',
    headers: {
      'X-Session-ID': sessionId,
      'Content-Type': 'application/json',
    },
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || 'Submission failed');
  }

  return data;
}

export function getPaperViewUrl(sessionId: string, artifactUuid: string): string {
  return `${API_BASE}/student/paper/${artifactUuid}/view?session=${sessionId}`;
}

export async function reportPaperIssue(
  sessionId: string,
  artifactUuid: string,
  message: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/student/paper/${artifactUuid}/report`, {
    method: 'POST',
    headers: {
      'X-Session-ID': sessionId,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || 'Failed to submit report');
  }

  return data;
}

export function getReceiptDownloadUrl(sessionId: string, artifactUuid: string): string {
  return `${API_BASE}/student/paper/${artifactUuid}/receipt?session=${sessionId}`;
}

export async function deleteReport(sessionId: string, reportId: number): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/student/reports/${reportId}`, {
    method: 'DELETE',
    headers: {
      'X-Session-ID': sessionId,
      'Content-Type': 'application/json',
    },
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || 'Failed to delete report');
  }

  return data;
}

export interface Activity {
  type: 'added' | 'submitted' | 'removed';
  subject_code: string;
  subject_name: string;
  exam_type: string;
  timestamp: string;
  student_name?: string;
  filename?: string;
}

export async function fetchActivities(sessionId: string): Promise<Activity[]> {
  const res = await fetch(`${API_BASE}/student/activities`, {
    headers: {
      'X-Session-ID': sessionId,
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch activities');
  }

  const data = await res.json();
  return data.activities || [];
}

export interface Report {
  id: number;
  artifact_uuid: string | null;
  original_filename: string | null;
  parsed_reg_no: string | null;
  parsed_subject_code: string | null;
  description: string;
  created_at: string;
  resolved: boolean;
  resolved_by: string | null;
  resolved_at: string | null;
  resolved_note: string | null;
}

export async function fetchMyReports(sessionId: string): Promise<Report[]> {
  const res = await fetch(`${API_BASE}/student/reports`, {
    headers: {
      'X-Session-ID': sessionId,
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch reports');
  }

  return res.json();
}
