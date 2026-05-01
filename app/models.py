import sqlite3
import os
import json
from datetime import datetime

DB_PATH = None  # set dynamically by main.py

def init_db():
    if DB_PATH is None:
        raise RuntimeError("Database path not set")

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Original reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                extracted_text TEXT,
                name TEXT,
                age TEXT,
                gender TEXT,
                address TEXT,
                date_of_death TEXT,
                cause_of_death TEXT,
                examiner TEXT
            )
        ''')

        # Add new columns to reports (ignore if already exist)
        new_columns = [
            ('ai_cause_of_death', 'TEXT'),
            ('tampering_risk', 'TEXT'),
            ('consistency_score', 'REAL'),
            ('event_type', 'TEXT'),
            ('time_of_death', 'TEXT'),
            ('fir_info', 'TEXT'),
            ('doctor_comments', 'TEXT'),
            ('medical_history', 'TEXT'),
            ('lab_results', 'TEXT'),
            ('created_at', 'TEXT'),
        ]
        for col_name, col_type in new_columns:
            try:
                cursor.execute(f'ALTER TABLE reports ADD COLUMN {col_name} {col_type}')
            except sqlite3.OperationalError:
                pass  # Column already exists

        # Body conditions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS body_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER REFERENCES reports(id),
                injury_type TEXT,
                body_part TEXT,
                severity TEXT,
                description TEXT,
                bleeding_level TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Verification results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER REFERENCES reports(id),
                consistency_score REAL,
                tampering_risk TEXT,
                ai_cause_of_death TEXT,
                ai_confidence INTEGER,
                cod_match INTEGER,
                matches_json TEXT,
                mismatches_json TEXT,
                red_flags_json TEXT,
                ai_reasoning_json TEXT,
                verification_summary TEXT,
                scene_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Evidence media table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evidence_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER REFERENCES reports(id),
                filename TEXT,
                file_type TEXT,
                file_path TEXT,
                ocr_text TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()


def insert_report(data):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reports (
                filename, extracted_text, name, age, gender, address,
                date_of_death, cause_of_death, examiner,
                ai_cause_of_death, tampering_risk, consistency_score,
                event_type, time_of_death, fir_info, doctor_comments,
                medical_history, lab_results, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('filename'),
            data.get('extracted_text'),
            data.get('name'),
            data.get('age'),
            data.get('gender'),
            data.get('address'),
            data.get('date_of_death'),
            data.get('cause_of_death'),
            data.get('examiner'),
            data.get('ai_cause_of_death'),
            data.get('tampering_risk'),
            data.get('consistency_score'),
            data.get('event_type'),
            data.get('time_of_death'),
            data.get('fir_info'),
            data.get('doctor_comments'),
            data.get('medical_history'),
            data.get('lab_results'),
            datetime.now().isoformat(),
        ))
        conn.commit()
        return cursor.lastrowid


def insert_body_conditions(report_id, conditions):
    """Insert multiple body condition entries for a report."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for cond in conditions:
            cursor.execute('''
                INSERT INTO body_conditions (
                    report_id, injury_type, body_part, severity,
                    description, bleeding_level
                )
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                report_id,
                cond.get('injury_type'),
                cond.get('body_part'),
                cond.get('severity'),
                cond.get('description'),
                cond.get('bleeding_level'),
            ))
        conn.commit()


def insert_verification(report_id, verification):
    """Insert verification result for a report."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO verifications (
                report_id, consistency_score, tampering_risk,
                ai_cause_of_death, ai_confidence, cod_match,
                matches_json, mismatches_json, red_flags_json,
                ai_reasoning_json, verification_summary, scene_notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id,
            verification.get('consistency_score'),
            verification.get('tampering_risk'),
            verification.get('ai_cause_of_death'),
            verification.get('ai_confidence'),
            1 if verification.get('cod_match') else 0,
            json.dumps(verification.get('matches', [])),
            json.dumps(verification.get('missing_from_report', []) + verification.get('suspicious', [])),
            json.dumps(verification.get('red_flags', [])),
            json.dumps(verification.get('ai_reasoning', [])),
            verification.get('summary', ''),
            verification.get('scene_notes', ''),
        ))
        conn.commit()


def get_all_reports():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, filename, name, age, gender, date_of_death,
                   tampering_risk, consistency_score, ai_cause_of_death
            FROM reports ORDER BY id DESC
        ''')
        return cursor.fetchall()


def get_report_by_id(report_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_body_conditions(report_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM body_conditions WHERE report_id = ?', (report_id,))
        return [dict(r) for r in cursor.fetchall()]


def get_verification(report_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM verifications WHERE report_id = ? ORDER BY id DESC LIMIT 1', (report_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Parse JSON fields
            for field in ['matches_json', 'mismatches_json', 'red_flags_json', 'ai_reasoning_json']:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except json.JSONDecodeError:
                        result[field] = []
            return result
        return None


def insert_evidence_media(report_id, media_list):
    """Insert evidence media entries for a report.
    media_list: list of dicts with keys: filename, file_type, file_path, ocr_text
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for media in media_list:
            cursor.execute('''
                INSERT INTO evidence_media (
                    report_id, filename, file_type, file_path, ocr_text
                )
                VALUES (?, ?, ?, ?, ?)
            ''', (
                report_id,
                media.get('filename'),
                media.get('file_type'),
                media.get('file_path'),
                media.get('ocr_text', ''),
            ))
        conn.commit()


def get_evidence_media(report_id):
    """Get all evidence media for a report."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM evidence_media WHERE report_id = ? ORDER BY id', (report_id,))
        return [dict(r) for r in cursor.fetchall()]


def extract_pdf_text(pdf_path):
    import pdfplumber
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text
