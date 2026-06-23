import { motion } from "framer-motion"
import { SectionHeader } from "../components/ui/SectionHeader"
import { Database, FileText, Server, Layers } from "lucide-react"

const schema = [
  { 
    model: "ExaminationArtifact", 
    desc: "Primary table tracking scanned exam papers.",
    details: "id (PK), artifact_uuid (UUID, Unique), raw_filename (varchar), original_filename (varchar), parsed_reg_no (varchar), parsed_subject_code (varchar), register_confidence (int), subject_confidence (int), exam_type (varchar, default 'CIA1'), attempt_number (int, default 1), attempt_2_locked (bool), file_blob_path (varchar), file_hash (varchar), file_size_bytes (bigint), mime_type (varchar), file_content (LargeBinary/BYTEA), moodle_user_id (bigint), moodle_username (varchar), moodle_course_id (int), moodle_assignment_id (int), workflow_status (Enum), auto_processed (bool), moodle_draft_item_id (bigint), moodle_submission_id (varchar), lms_transaction_id (varchar), transaction_id (varchar, Unique), uploaded_at (timestamp), validated_at (timestamp), submit_timestamp (timestamp), completed_at (timestamp), uploaded_by_staff_id (FK -> staff_users), submitted_by_user_id (bigint), transaction_log (JSONB), error_message (text), retry_count (int)."
  },
  { 
    model: "SubjectMapping", 
    desc: "Maps university subject codes to specific Moodle assignments.",
    details: "id (PK), subject_code (varchar), subject_name (varchar), exam_type (varchar, default 'CIA1'), moodle_course_id (int), moodle_course_idnumber (varchar), moodle_assignment_id (int), moodle_assignment_name (varchar), cmid (int), target_site_url (varchar), assignment_password_encrypted (text), resolved_at (timestamp), exam_session (varchar), is_active (bool), created_at (timestamp), updated_at (timestamp), last_verified_at (timestamp). Unique constraint: (subject_code, exam_type)."
  },
  { 
    model: "ExamSubmission", 
    desc: "State synchronization ledger preventing double submissions and tracking locked items.",
    details: "id (PK), student_id (varchar, university register number), moodle_user_id (bigint), moodle_username (varchar), subject_code (varchar), assignment_id (int), exam_type (varchar, default 'CIA1'), attempt_number (int, default 1), artifact_id (FK -> examination_artifacts, SET NULL), status (varchar, default 'PENDING'), submitted_at (timestamp), locked_at (timestamp), target_site_url (varchar), transaction_id (varchar), created_at (timestamp). Unique constraint: (student_id, subject_code, exam_type, attempt_number)."
  },
  { 
    model: "StudentSession", 
    desc: "Temporary student SSO sessions containing encrypted Moodle tokens.",
    details: "id (PK), session_id (varchar, Unique), moodle_user_id (bigint), moodle_user_ids (JSON dict for multi-tenant), moodle_username (varchar), moodle_fullname (varchar), register_number (varchar), encrypted_token (text), encrypted_tokens (JSON dict for multi-tenant), token_expires_at (timestamp), ip_address (varchar), user_agent (varchar), created_at (timestamp), last_activity_at (timestamp), expires_at (timestamp)."
  },
  { 
    model: "StudentUsernameRegister", 
    desc: "Authorization map matching Moodle usernames to university register numbers.",
    details: "id (PK), moodle_username (varchar, Unique), register_number (varchar), created_at (timestamp), updated_at (timestamp). Unique constraint: (moodle_username, register_number)."
  },
  { 
    model: "StaffUser", 
    desc: "Administrative and exam-cell personnel with access to upload and parse.",
    details: "id (PK), username (varchar, Unique), email (varchar, Unique), hashed_password (varchar), full_name (varchar), role (varchar, default 'staff'), is_active (bool), created_at (timestamp), last_login_at (timestamp)."
  },
  { 
    model: "AuditLog", 
    desc: "Immutable system activity ledger for compliance and security forensics.",
    details: "id (PK), action (varchar), action_category (varchar), description (text), actor_type (varchar), actor_id (varchar), actor_username (varchar), actor_ip (varchar), artifact_id (FK -> examination_artifacts, CASCADE), target_type (varchar), target_id (varchar), request_data (JSONB), response_data (JSONB), error_details (JSONB), moodle_api_function (varchar), moodle_response_code (int), created_at (timestamp)."
  },
  { 
    model: "SubmissionQueue", 
    desc: "Buffering queue to handle retries for failed Moodle API requests.",
    details: "id (PK), artifact_id (FK -> examination_artifacts, CASCADE), status (varchar, default 'QUEUED'), priority (int), retry_count (int), max_retries (int), next_retry_at (timestamp), queued_at (timestamp), processed_at (timestamp), last_error (text)."
  },
  { 
    model: "SystemConfig", 
    desc: "Dynamic key-value config registry for platform parameters.",
    details: "id (PK), key (varchar, Unique), value (text), value_type (varchar), description (text), updated_at (timestamp)."
  }
]

export function Architecture() {
  return (
    <section className="py-24 bg-[#f4f2ea] border-t-2 border-[#111111]" id="architecture">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeader 
          badge="System Design" 
          title="Robust Architecture." 
          description="Designed for data integrity, security, and complete auditability across every step."
        />

        {/* 4-node flow using brutalist cards */}
        <div className="mt-16 mb-24 max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
            
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="z-10">
              <div className="brutal-card p-6 text-center h-full flex flex-col justify-center bg-white hover:bg-[#e5e3d9] transition-colors cursor-default">
                <div className="h-12 w-12 mx-auto border-2 border-[#111111] bg-[#f4f2ea] flex items-center justify-center mb-4 text-[#111111] shadow-[2px_2px_0px_#111111]">
                  <FileText className="h-6 w-6" />
                </div>
                <h4 className="font-sans font-bold text-[#111111] mb-1 text-sm">Physical Layer</h4>
                <p className="font-mono text-[10px] text-[#555555] mb-3">Scanned Answer Sheets</p>
                <span className="font-mono text-[10px] font-bold bg-[#111111] text-white px-2 py-1 rounded">PDF/JPG</span>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }} className="z-10">
              <div className="brutal-card p-6 text-center h-full flex flex-col justify-center bg-white hover:bg-[#e5e3d9] transition-colors cursor-default">
                <div className="h-12 w-12 mx-auto border-2 border-[#111111] bg-[#2563eb] flex items-center justify-center mb-4 text-white shadow-[2px_2px_0px_#111111]">
                  <Server className="h-6 w-6" />
                </div>
                <h4 className="font-sans font-bold text-[#111111] mb-1 text-sm">FastAPI Core</h4>
                <p className="font-mono text-[10px] text-[#555555] mb-3">PostgreSQL + JWT</p>
                <span className="font-mono text-[10px] font-bold bg-[#2563eb] text-white px-2 py-1 rounded">AUTH / API</span>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }} className="z-10">
              <div className="brutal-card p-6 text-center h-full flex flex-col justify-center bg-white hover:bg-[#e5e3d9] transition-colors cursor-default">
                <div className="h-12 w-12 mx-auto border-2 border-[#111111] bg-green-500 flex items-center justify-center mb-4 text-[#111111] shadow-[2px_2px_0px_#111111]">
                  <Layers className="h-6 w-6" />
                </div>
                <h4 className="font-sans font-bold text-[#111111] mb-1 text-sm">HF Spaces</h4>
                <p className="font-mono text-[10px] text-[#555555] mb-3">YOLO + CRNN Models</p>
                <span className="font-mono text-[10px] font-bold bg-green-500 text-[#111111] px-2 py-1 rounded">INFERENCE</span>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.3 }} className="z-10">
              <div className="brutal-card p-6 text-center h-full flex flex-col justify-center bg-white hover:bg-[#e5e3d9] transition-colors cursor-default">
                <div className="h-12 w-12 mx-auto border-2 border-[#111111] bg-yellow-400 flex items-center justify-center mb-4 text-[#111111] shadow-[2px_2px_0px_#111111]">
                  <Database className="h-6 w-6" />
                </div>
                <h4 className="font-sans font-bold text-[#111111] mb-1 text-sm">Moodle LMS</h4>
                <p className="font-mono text-[10px] text-[#555555] mb-3">Assignment Submissions</p>
                <span className="font-mono text-[10px] font-bold bg-yellow-400 text-[#111111] px-2 py-1 rounded">SSO / SYNC</span>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Project Structure Tree */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-5xl mx-auto mb-16"
        >
          <div className="brutal-card bg-white p-6">
            <h3 className="font-sans font-bold text-[#111111] uppercase tracking-wide text-sm mb-4 border-b-2 border-[#111111] pb-2">Project Structure</h3>
            <pre className="font-mono text-xs md:text-sm text-[#555555] overflow-x-auto leading-relaxed">
<span className="text-[#111111] font-bold">IESF-LMS/</span>
├── <span className="text-[#2563eb] font-bold">exam_middleware/</span>                  <span className="text-[#a1a1aa] italic"># Primary Backend Framework</span>
│   ├── <span className="text-[#2563eb] font-bold">app/</span>
│   │   ├── <span className="text-[#2563eb] font-bold">api/routes/</span>                <span className="text-[#a1a1aa] italic"># Endpoints (auth, upload, student, admin)</span>
│   │   ├── <span className="text-[#2563eb] font-bold">core/</span>                      <span className="text-[#a1a1aa] italic"># Configuration & Cryptography (security, config)</span>
│   │   ├── <span className="text-[#2563eb] font-bold">db/</span>                        <span className="text-[#a1a1aa] italic"># DB Engine & SQLAlchemy Models (database, models)</span>
│   │   └── <span className="text-[#2563eb] font-bold">services/</span>                  <span className="text-[#a1a1aa] italic"># Business Logic (moodle_client, submission_service)</span>
│   ├── <span className="text-green-600 font-bold">init_db.py</span>                     <span className="text-[#a1a1aa] italic"># Schema Creator & Sample Seeder</span>
│   ├── <span className="text-green-600 font-bold">scanner_agent.py</span>               <span className="text-[#a1a1aa] italic"># Scanned Folder Watcher Script</span>
│   ├── <span className="text-green-600 font-bold">setup_subject_mapping.py</span>       <span className="text-[#a1a1aa] italic"># Subject-to-LMS catalog configuration utility</span>
│   └── <span className="text-green-600 font-bold">setup_username_reg.py</span>          <span className="text-[#a1a1aa] italic"># Username-to-Register map editor utility</span>
├── <span className="text-[#2563eb] font-bold">hf_space/</span>                         <span className="text-[#a1a1aa] italic"># HuggingFace Space ML Inference Server</span>
│   ├── <span className="text-green-600 font-bold">app.py</span>                         <span className="text-[#a1a1aa] italic"># YOLOv8 + CRNN OCR API Server</span>
│   └── <span className="text-[#555555]">requirements.txt</span>               <span className="text-[#a1a1aa] italic"># PyTorch & YOLO Dependencies</span>
├── <span className="text-[#2563eb] font-bold">frontend-landing/</span>                 <span className="text-[#a1a1aa] italic"># React Landing Page (This application)</span>
├── <span className="text-green-600 font-bold">docker-compose.yml</span>                <span className="text-[#a1a1aa] italic"># Local Docker Orchestration</span>
└── <span className="text-green-600 font-bold">index.html</span>                        <span className="text-[#a1a1aa] italic"># Root Entrypoint serving built React assets</span>
            </pre>
          </div>
        </motion.div>

        {/* Database Schema Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-5xl mx-auto"
        >
          <div className="brutal-card bg-white overflow-hidden">
            <div className="flex items-center gap-3 p-5 border-b-2 border-[#111111] bg-[#f4f2ea]">
              <Database className="h-5 w-5 text-[#2563eb]" />
              <h3 className="font-sans font-bold text-[#111111] uppercase tracking-wide text-sm">Database Schema</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b-2 border-[#111111] bg-white">
                    <th className="px-6 py-4 font-bold text-[#555555] uppercase w-1/3">Model</th>
                    <th className="px-6 py-4 font-bold text-[#555555] uppercase">Schema Attributes (Fields & Relationships)</th>
                  </tr>
                </thead>
                <tbody>
                  {schema.map((item, i) => (
                    <tr key={i} className="hover:bg-[#f4f2ea] transition-colors border-b border-dashed border-[#a1a1aa] last:border-0 group">
                      <td className="px-6 py-4 vertical-align-top">
                        <span className="text-[#2563eb] font-bold block mb-1">
                          {item.model}
                        </span>
                        <span className="text-[10px] text-[#777777] font-sans block">{item.desc}</span>
                      </td>
                      <td className="px-6 py-4 text-[#555555] leading-relaxed group-hover:text-[#111111] font-mono text-[10px] break-words whitespace-normal">
                        {item.details}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
