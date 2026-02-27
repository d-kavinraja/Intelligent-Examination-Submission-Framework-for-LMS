"""
Scanner Agent — Local Python script that runs on the PC connected to
the Ricoh scanner. It watches a folder for new scanned files and
automatically sends them to the server for AI extraction + upload.

=== SETUP ===
1. pip install requests watchdog
2. Configure SETTINGS below (server URL, credentials, scan folder)
3. Run:  python scanner_agent.py

=== HOW IT WORKS ===
Scanner saves to WATCH_FOLDER → Agent detects new file → waits for
file to finish writing → POSTs to /extract/scan-upload → server runs
AI extraction → renames to {reg_no}_{subject_code}_{exam_type}.pdf →
creates artifact → Agent moves original file to "processed/" folder.
"""

import os
import sys
import time
import json
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime

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

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

# ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ScannerAgent")


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

        # Track files we've already seen (to avoid re-processing)
        self._seen_files: set[str] = set()

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

    def process_file(self, file_path: Path) -> bool:
        """
        Send a single scanned file to the server for extraction + upload.
        Returns True if successful.
        """
        log.info(f"── Processing: {file_path.name}")

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
                    timeout=120,  # extraction can take time
                )

            if resp.status_code == 401:
                log.warning("   Token expired — re-authenticating...")
                if self.login():
                    return self.process_file(file_path)  # retry once
                return False

            data = resp.json()

            if data.get("success"):
                log.info(f"   ✓ Extracted: Reg={data['register_number']} "
                         f"({data['register_confidence']}%) | "
                         f"Subject={data['subject_code']} "
                         f"({data['subject_confidence']}%)")
                log.info(f"   ✓ Uploaded as: {data['renamed_filename']}")
                log.info(f"   ✓ Artifact UUID: {data['artifact_uuid']}")

                # Move to processed folder
                dest = self.processed_folder / f"{data['renamed_filename']}__{file_path.name}"
                shutil.move(str(file_path), str(dest))
                log.info(f"   ✓ Moved to: processed/{dest.name}")
                return True
            else:
                error = data.get("error", "Unknown error")
                stage = data.get("stage", "unknown")
                log.error(f"   ✗ Failed at stage '{stage}': {error}")

                # If extraction failed (can't read reg/subject), move to failed
                dest = self.failed_folder / file_path.name
                shutil.move(str(file_path), str(dest))
                log.warning(f"   Moved to: failed/{file_path.name}")
                return False

        except requests.exceptions.Timeout:
            log.error(f"   ✗ Request timed out (server may be starting up)")
            return False
        except Exception as e:
            log.error(f"   ✗ Error: {e}")
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

    def scan_folder(self):
        """Scan the watch folder for new files and process them."""
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
            self.process_file(entry)

    def run(self):
        """Main loop — continuously watch folder and process new files."""
        log.info("=" * 60)
        log.info("  Scanner Agent — Smart Scan Pipeline")
        log.info("=" * 60)
        log.info(f"  Server:       {self.server_url}")
        log.info(f"  Watch folder: {self.watch_folder}")
        log.info(f"  Exam type:    {self.exam_type}")
        log.info(f"  Poll every:   {POLL_INTERVAL}s")
        log.info("=" * 60)

        # Pre-flight checks
        if not self.login():
            log.error("Cannot start — login failed. Check credentials.")
            sys.exit(1)

        if not self.check_extraction_ready():
            log.warning("⚠ Extraction models may not be ready yet. "
                        "Will retry when first file is processed.")

        log.info(f"\nWatching '{self.watch_folder}' for new scanned files...")
        log.info("Press Ctrl+C to stop.\n")

        try:
            while True:
                self.scan_folder()
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            log.info("\nStopped by user.")


def main():
    parser = argparse.ArgumentParser(description="Scanner Agent — auto-upload scanned answer sheets")
    parser.add_argument("--server", default=SERVER_URL, help=f"Server URL (default: {SERVER_URL})")
    parser.add_argument("--username", default=STAFF_USERNAME, help=f"Staff username (default: {STAFF_USERNAME})")
    parser.add_argument("--password", default=STAFF_PASSWORD, help=f"Staff password (default: {STAFF_PASSWORD})")
    parser.add_argument("--folder", default=WATCH_FOLDER, help=f"Scanner output folder (default: {WATCH_FOLDER})")
    parser.add_argument("--exam-type", default=DEFAULT_EXAM_TYPE, choices=["CIA1", "CIA2"],
                        help=f"Exam type (default: {DEFAULT_EXAM_TYPE})")
    args = parser.parse_args()

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
