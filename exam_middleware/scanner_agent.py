"""
Scanner Agent — Local Python script that runs on the PC connected to
the Ricoh scanner. It watches a folder for new scanned files and
automatically sends them to the server for AI extraction + upload.

=== SETUP ===
1. pip install requests
2. Configure SETTINGS below (server URL, credentials, scan folder)
3. Run:  python scanner_agent.py

=== HOW IT WORKS ===
Scanner saves to WATCH_FOLDER → Agent detects new file → waits for
file to finish writing → adds to QUEUE → processes ONE file at a time →
POSTs to /extract/scan-upload → waits for server response → verifies
artifact UUID is unique → moves original file → processes NEXT file.

Each file is fully uploaded and confirmed before the next one starts.
"""

import os
import sys
import time
import json
import shutil
import hashlib
import logging
import argparse
from pathlib import Path
from datetime import datetime
from collections import deque

import requests

# ─────────────────────────────────────────────────────────────────
# SETTINGS — Edit these to match your environment
# ─────────────────────────────────────────────────────────────────

# Server URL (your Render deployment)
SERVER_URL = "https://exam-middleware.onrender.com"

# Staff credentials (the agent logs in as staff to upload)
STAFF_USERNAME = "admin"
STAFF_PASSWORD = "admin123"

# Folder where the Ricoh scanner saves files
WATCH_FOLDER = r"C:\ScanInbox"

# Exam type to tag files with (CIA1 or CIA2)
DEFAULT_EXAM_TYPE = "CIA1"

# How often to check for new files (seconds)
POLL_INTERVAL = 3

# Wait this long after detecting a file before processing
# (ensures scanner has finished writing)
FILE_STABLE_WAIT = 2

# Delay between processing each file in the queue (seconds)
# Prevents server overload and ensures DB commits complete
QUEUE_DELAY = 3

# Maximum retries for a single file
MAX_RETRIES = 2

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

# ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ScannerAgent")


def file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


class ScannerAgent:
    def __init__(self, server_url: str, username: str, password: str,
                 watch_folder: str, exam_type: str):
        self.server_url = server_url.rstrip("/")
        self.username = username
        self.password = password
        self.watch_folder = Path(watch_folder)
        self.exam_type = exam_type
        self.auth_token = None

        # Create subfolders
        self.processed_folder = self.watch_folder / "processed"
        self.failed_folder = self.watch_folder / "failed"
        self.processed_folder.mkdir(parents=True, exist_ok=True)
        self.failed_folder.mkdir(parents=True, exist_ok=True)

        # Sequential queue — files wait here until processed one-by-one
        self._queue: deque[Path] = deque()
        # Track files already queued/processed (by path) to avoid duplicates
        self._seen_files: set[str] = set()
        # Track artifact UUIDs returned by server to detect overwrites
        self._uploaded_uuids: set[str] = set()
        # Stats
        self._stats = {"processed": 0, "failed": 0, "skipped": 0}

    def login(self) -> bool:
        """Authenticate with the server and get a JWT token."""
        log.info(f"Logging in to {self.server_url} as '{self.username}'...")
        try:
            resp = requests.post(
                f"{self.server_url}/auth/staff/login",
                data={"username": self.username, "password": self.password},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.auth_token = data.get("access_token") or data.get("token")
                if self.auth_token:
                    log.info("✓ Logged in successfully")
                    return True
                log.error(f"Login response missing token: {data}")
            else:
                log.error(f"Login failed (HTTP {resp.status_code}): {resp.text[:200]}")
        except Exception as e:
            log.error(f"Login error: {e}")
        return False

    def check_extraction_ready(self) -> bool:
        """Check if AI models are loaded on the server."""
        try:
            resp = requests.get(f"{self.server_url}/extract/status", timeout=15)
            data = resp.json()
            if data.get("extraction_available"):
                log.info("✓ AI extraction models are ready on server")
                return True
            else:
                log.warning("✗ Extraction models not available on server")
                return False
        except Exception as e:
            log.error(f"Could not check extraction status: {e}")
            return False

    def process_file(self, file_path: Path, retry_count: int = 0) -> bool:
        """
        Send a single scanned file to the server for extraction + upload.
        Blocks until the server responds. Returns True if successful.
        """
        file_hash = file_sha256(file_path)
        log.info(f"── Processing [{self._stats['processed']+self._stats['failed']+1}]: "
                 f"{file_path.name}  (hash: {file_hash})")

        if not self.auth_token:
            if not self.login():
                log.error("   Cannot process — not authenticated")
                return False

        try:
            with open(file_path, "rb") as f:
                resp = requests.post(
                    f"{self.server_url}/extract/scan-upload",
                    files={"file": (file_path.name, f, "application/octet-stream")},
                    data={"exam_type": self.exam_type},
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=180,  # generous timeout for HF Space wake-up
                )

            if resp.status_code == 401:
                log.warning("   Token expired — re-authenticating...")
                if self.login() and retry_count < MAX_RETRIES:
                    return self.process_file(file_path, retry_count + 1)
                return False

            data = resp.json()

            if data.get("success"):
                reg = data.get('register_number', '?')
                sub = data.get('subject_code', '?')
                reg_conf = data.get('register_confidence', 0)
                sub_conf = data.get('subject_confidence', 0)
                renamed = data.get('renamed_filename', '?')
                uuid = data.get('artifact_uuid', '')

                log.info(f"   ✓ Extracted: Reg={reg} ({reg_conf}%) | Subject={sub} ({sub_conf}%)")
                log.info(f"   ✓ Uploaded as: {renamed}")
                log.info(f"   ✓ Artifact UUID: {uuid}")

                # Warn if server returned a UUID we've already seen (overwrite)
                if uuid in self._uploaded_uuids:
                    log.warning(f"   ⚠ DUPLICATE UUID detected! Server overwrote a previous upload.")
                    log.warning(f"   ⚠ This file may have the same extracted reg+subject as another file.")
                self._uploaded_uuids.add(uuid)

                # Move to processed folder (include hash to distinguish files)
                dest = self.processed_folder / f"{renamed}__{file_hash}__{file_path.name}"
                shutil.move(str(file_path), str(dest))
                log.info(f"   ✓ Moved to: processed/{dest.name}")
                self._stats["processed"] += 1
                return True
            else:
                error = data.get("error") or data.get("detail") or str(data)
                stage = data.get("stage", "server")
                log.error(f"   ✗ Failed at stage '{stage}': {error}")

                # Move to failed folder
                dest = self.failed_folder / file_path.name
                if dest.exists():
                    dest = self.failed_folder / f"{file_hash}__{file_path.name}"
                shutil.move(str(file_path), str(dest))
                log.warning(f"   Moved to: failed/{dest.name}")
                self._stats["failed"] += 1
                return False

        except requests.exceptions.Timeout:
            log.error(f"   ✗ Request timed out (server may be starting up)")
            if retry_count < MAX_RETRIES:
                log.info(f"   Retrying ({retry_count + 1}/{MAX_RETRIES})...")
                time.sleep(5)
                return self.process_file(file_path, retry_count + 1)
            self._stats["failed"] += 1
            return False
        except Exception as e:
            log.error(f"   ✗ Error: {e}")
            self._stats["failed"] += 1
            return False

    def _is_file_stable(self, file_path: Path) -> bool:
        """Check if a file has stopped being written to."""
        try:
            size1 = file_path.stat().st_size
            time.sleep(FILE_STABLE_WAIT)
            size2 = file_path.stat().st_size
            return size1 == size2 and size2 > 0
        except OSError:
            return False

    def _discover_new_files(self):
        """Scan the watch folder and add new files to the queue."""
        if not self.watch_folder.exists():
            log.error(f"Watch folder does not exist: {self.watch_folder}")
            return

        for entry in sorted(self.watch_folder.iterdir()):
            if not entry.is_file():
                continue
            if entry.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue
            if str(entry) in self._seen_files:
                continue

            # Wait for file to finish writing
            if not self._is_file_stable(entry):
                log.debug(f"File still writing: {entry.name}")
                continue

            self._seen_files.add(str(entry))
            self._queue.append(entry)
            log.info(f"   ⊕ Queued: {entry.name}  (queue size: {len(self._queue)})")

    def _process_queue(self):
        """Process files from the queue ONE AT A TIME, sequentially."""
        while self._queue:
            file_path = self._queue.popleft()

            # Skip if file was already moved/deleted
            if not file_path.exists():
                log.warning(f"   Skipping (file gone): {file_path.name}")
                self._stats["skipped"] += 1
                continue

            # Process this file — block until complete
            success = self.process_file(file_path)

            # Wait before processing next file to let server DB commit
            if self._queue:
                remaining = len(self._queue)
                log.info(f"   ⏳ Waiting {QUEUE_DELAY}s before next file... "
                         f"({remaining} remaining in queue)")
                time.sleep(QUEUE_DELAY)

    def run(self):
        """Main loop — discover files and process them sequentially."""
        log.info("=" * 60)
        log.info("  Scanner Agent — Sequential Queue Pipeline")
        log.info("=" * 60)
        log.info(f"  Server:       {self.server_url}")
        log.info(f"  Watch folder: {self.watch_folder}")
        log.info(f"  Exam type:    {self.exam_type}")
        log.info(f"  Poll every:   {POLL_INTERVAL}s")
        log.info(f"  Queue delay:  {QUEUE_DELAY}s between files")
        log.info("=" * 60)

        # Pre-flight checks
        if not self.login():
            log.error("Cannot start — login failed. Check credentials.")
            sys.exit(1)

        if not self.check_extraction_ready():
            log.warning("⚠ Extraction models may not be ready yet. "
                        "Will retry when first file is processed.")

        log.info(f"\nWatching '{self.watch_folder}' for new scanned files...")
        log.info("Files will be uploaded ONE AT A TIME in sequence.")
        log.info("Press Ctrl+C to stop.\n")

        try:
            while True:
                # Step 1: Discover new files and add to queue
                self._discover_new_files()

                # Step 2: Process queue sequentially (blocks until empty)
                if self._queue:
                    log.info(f"── Queue has {len(self._queue)} file(s) — processing sequentially...")
                    self._process_queue()
                    log.info(f"── Queue empty. Stats: "
                             f"✓ {self._stats['processed']} processed | "
                             f"✗ {self._stats['failed']} failed | "
                             f"⊘ {self._stats['skipped']} skipped")

                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            log.info(f"\nStopped by user. Final stats: "
                     f"✓ {self._stats['processed']} processed | "
                     f"✗ {self._stats['failed']} failed | "
                     f"⊘ {self._stats['skipped']} skipped")


def main():
    parser = argparse.ArgumentParser(description="Scanner Agent — auto-upload scanned answer sheets")
    parser.add_argument("--server", default=SERVER_URL, help=f"Server URL (default: {SERVER_URL})")
    parser.add_argument("--username", default=STAFF_USERNAME, help=f"Staff username (default: {STAFF_USERNAME})")
    parser.add_argument("--password", default=STAFF_PASSWORD, help=f"Staff password (default: {STAFF_PASSWORD})")
    parser.add_argument("--folder", default=WATCH_FOLDER, help=f"Scanner output folder (default: {WATCH_FOLDER})")
    parser.add_argument("--exam-type", default=DEFAULT_EXAM_TYPE, choices=["CIA1", "CIA2"],
                        help=f"Exam type (default: {DEFAULT_EXAM_TYPE})")
    parser.add_argument("--delay", type=int, default=QUEUE_DELAY,
                        help=f"Seconds between processing each file (default: {QUEUE_DELAY})")
    args = parser.parse_args()

    global QUEUE_DELAY
    QUEUE_DELAY = args.delay

    agent = ScannerAgent(
        server_url=args.server,
        username=args.username,
        password=args.password,
        watch_folder=args.folder,
        exam_type=args.exam_type,
    )
    agent.run()


if __name__ == "__main__":
    main()
