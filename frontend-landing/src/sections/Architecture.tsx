import { motion } from "framer-motion"
import { SectionHeader } from "../components/ui/SectionHeader"
import { Database, FileText, Server, Layers, Folder, File } from "lucide-react"

const projectStructure = [
  {
    name: "IESF-LMS",
    type: "folder",
    children: [
      {
        name: "exam_middleware",
        type: "folder",
        desc: "Primary Backend Framework",
        children: [
          {
            name: "app",
            type: "folder",
            children: [
              { name: "api/routes", type: "folder", desc: "Endpoints (auth, upload, student, admin)" },
              { name: "core", type: "folder", desc: "Configuration & Cryptography (security, config)" },
              { name: "db", type: "folder", desc: "DB Engine & SQLAlchemy Models (database, models)" },
              { name: "services", type: "folder", desc: "Business Logic (moodle_client, submission_service)" },
            ]
          },
          { name: "init_db.py", type: "file", desc: "Schema Creator & Sample Seeder" },
          { name: "scanner_agent.py", type: "file", desc: "Scanned Folder Watcher Script" },
          { name: "setup_subject_mapping.py", type: "file", desc: "Subject-to-LMS catalog configuration utility" },
          { name: "setup_username_reg.py", type: "file", desc: "Username-to-Register map editor utility" },
        ]
      },
      {
        name: "hf_space",
        type: "folder",
        desc: "HuggingFace Space ML Inference Server",
        children: [
          { name: "app.py", type: "file", desc: "YOLOv8 + CRNN OCR API Server" },
          { name: "requirements.txt", type: "file", desc: "PyTorch & YOLO Dependencies" },
        ]
      },
      {
        name: "frontend-landing",
        type: "folder",
        desc: "React Landing Page (This application)"
      },
      { name: "docker-compose.yml", type: "file", desc: "Local Docker Orchestration" },
      { name: "index.html", type: "file", desc: "Root Entrypoint serving built React assets" },
    ]
  }
];

const renderTree = (nodes: any[], level = 0) => {
  return nodes.map((node, idx) => (
    <motion.div 
      key={`${node.name}-${idx}`}
      initial={{ opacity: 0, x: -20 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ delay: level * 0.1 + idx * 0.05 }}
      className={`flex items-start gap-2 my-2 ${level > 0 ? "ml-6 border-l-2 border-dashed border-[#a1a1aa] pl-4" : ""}`}
    >
      <div className="mt-0.5 shrink-0">
        {node.type === 'folder' ? <Folder className="h-5 w-5 text-[#2563eb]" fill="#2563eb" fillOpacity={0.2} /> : <File className="h-5 w-5 text-green-600" />}
      </div>
      <div className="flex-grow">
        <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-3">
          <span className={`font-mono text-sm ${node.type === 'folder' ? 'font-bold text-[#111111]' : 'text-[#555555]'}`}>
            {node.name}
          </span>
          {node.desc && (
            <span className="font-sans text-xs text-[#777777] italic">- {node.desc}</span>
          )}
        </div>
        {node.children && <div className="mt-2">{renderTree(node.children, level + 1)}</div>}
      </div>
    </motion.div>
  ))
}

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
          className="max-w-5xl mx-auto mb-20"
        >
          <div className="brutal-card bg-white p-6 md:p-8">
            <div className="flex items-center gap-3 mb-6 border-b-2 border-[#111111] pb-4">
              <Folder className="h-6 w-6 text-[#111111]" fill="#111111" />
              <h3 className="font-sans font-bold text-[#111111] text-2xl tracking-tight">Project Structure</h3>
            </div>
            <div className="overflow-x-auto custom-scrollbar pb-4">
              <div className="min-w-[600px] md:min-w-0">
                {renderTree(projectStructure)}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Database Schema Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-5xl mx-auto"
        >
          <div className="flex items-center gap-3 mb-8">
            <Database className="h-8 w-8 text-[#2563eb]" />
            <h3 className="font-sans font-bold text-[#111111] text-2xl tracking-tight">Database Schema</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {schema.map((item, i) => (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className="brutal-card bg-white p-5 flex flex-col h-full hover:-translate-y-2 hover:shadow-[8px_8px_0px_#111111] transition-all duration-300"
              >
                <div className="flex items-center justify-between mb-4 border-b-2 border-[#111111] pb-3">
                  <h4 className="font-sans font-bold text-[#2563eb] text-lg leading-tight">{item.model}</h4>
                  <Database className="h-5 w-5 text-[#a1a1aa] shrink-0 ml-2" />
                </div>
                <p className="font-sans text-sm text-[#555555] mb-5 flex-grow font-medium leading-relaxed">{item.desc}</p>
                <div className="bg-[#f4f2ea] p-4 rounded border-2 border-[#111111] max-h-40 overflow-y-auto custom-scrollbar shadow-inner relative">
                  <p className="font-mono text-[11px] text-[#111111] leading-relaxed break-words whitespace-normal relative z-10">
                    {item.details}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
