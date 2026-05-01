import os
import json
import yaml
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

import models
from utils.nlp_utils import extract_forensic_info, extract_entities, extract_injuries_from_text
from utils.cross_verifier import cross_verify, extract_injuries_from_report_text
from utils.media_processor import process_evidence_file, get_media_type
from docx import Document
import easyocr

load_dotenv()

# config.yaml path (project root pe)
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

app = Flask(__name__)
app.secret_key = config['app']['secret_key']

UPLOAD_FOLDER = config['upload']['folder']
ALLOWED_EXTENSIONS = set(config['upload']['allowed_extensions'])
DB_PATH = config['database']['path']

# Evidence media config
EVIDENCE_CONFIG = config.get('evidence', {})
EVIDENCE_IMAGE_EXTS = set(EVIDENCE_CONFIG.get('allowed_image_extensions', ['jpg', 'jpeg', 'png', 'bmp', 'tiff']))
EVIDENCE_VIDEO_EXTS = set(EVIDENCE_CONFIG.get('allowed_video_extensions', ['mp4', 'avi', 'mov', 'mkv']))
EVIDENCE_ALL_EXTS = EVIDENCE_IMAGE_EXTS | EVIDENCE_VIDEO_EXTS
EVIDENCE_MAX_FILES = EVIDENCE_CONFIG.get('max_files', 10)
EVIDENCE_FRAME_INTERVAL = EVIDENCE_CONFIG.get('frame_interval_seconds', 2)
EVIDENCE_MAX_FRAMES = EVIDENCE_CONFIG.get('max_frames', 10)

models.DB_PATH = DB_PATH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
models.init_db()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_evidence_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EVIDENCE_ALL_EXTS


def extract_report_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return models.extract_pdf_text(filepath)
    elif ext == ".txt":
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext == ".docx":
        try:
            doc = Document(filepath)
            return '\n'.join([para.text for para in doc.paragraphs])
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            return ""
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        try:
            reader = easyocr.Reader(['en'])
            result = reader.readtext(filepath, detail=0)
            return '\n'.join(result)
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    else:
        print(f"Unsupported file extension: {ext}")
        return ""


# =============================================================
# MULTI-LAYER MEDICAL REPORT VALIDATOR (5-Layer Scoring System)
# =============================================================

# Layer 2: Mandatory forensic keywords (must have ≥2)
MANDATORY_KEYWORDS = [
    'postmortem', 'post mortem', 'autopsy', 'forensic',
    'cause of death', 'medico legal', 'dead body', 'pm report',
    'post-mortem', 'medicolegal', 'inquest', 'death certificate',
    'autopsy report', 'examination of dead body',
]

# Layer 3: Medical/forensic terminology (each hit adds score)
MEDICAL_TERMS = [
    # Forensic-specific
    'hemorrhage', 'laceration', 'contusion', 'abrasion', 'fracture',
    'rigor mortis', 'livor mortis', 'algor mortis', 'lividity',
    'putrefaction', 'decomposition', 'toxicology', 'viscera',
    'histopathology', 'cadaveric', 'exhumation', 'strangulation',
    'asphyxia', 'drowning', 'ligature', 'petechiae', 'ecchymosis',
    'hematoma', 'edema', 'cyanosis', 'pallor',
    # Injury/wound terms
    'incised wound', 'stab wound', 'gunshot wound', 'blunt force',
    'sharp force', 'penetrating wound', 'exit wound', 'entry wound',
    'defense wound', 'defensive wound', 'crush injury',
    # Anatomy
    'cranium', 'cerebral', 'thorax', 'abdomen', 'pelvis', 'cervical',
    'vertebrae', 'femur', 'tibia', 'sternum', 'scapula', 'clavicle',
    'hyoid', 'trachea', 'larynx', 'spleen', 'liver', 'kidney',
    'lung', 'heart', 'aorta', 'meninges', 'dura mater',
    # Medical procedures/findings
    'dissection', 'incision', 'suture', 'specimen', 'blood sample',
    'organ weight', 'stomach contents', 'brain weight',
    'internal examination', 'external examination',
    'perimortem', 'antemortem', 'postmortem interval',
    # Death/legal
    'deceased', 'manner of death', 'mode of death', 'natural death',
    'homicide', 'suicide', 'accidental death', 'undetermined',
    'foul play', 'criminal', 'poisoning',
]

# Layer 4: Anti-patterns — if these appear, it's NOT a medical report
ANTI_PATTERNS = [
    # Resume/CV
    'curriculum vitae', 'resume', 'work experience', 'job experience',
    'career objective', 'career summary', 'professional summary',
    'skills and abilities', 'educational qualification', 'hobbies',
    'references available', 'linkedin.com', 'portfolio',
    'cover letter', 'job application', 'years of experience',
    'proficient in', 'team player', 'problem solving skills',
    # Business/Financial
    'invoice', 'receipt', 'bank statement', 'balance sheet',
    'profit and loss', 'tax return', 'financial statement',
    'purchase order', 'quotation', 'billing address',
    # Academic
    'assignment', 'semester', 'gpa', 'cgpa', 'transcript',
    'thesis', 'dissertation', 'course outline', 'syllabus',
    'lecture notes', 'bibliography',
    # E-commerce/Tech
    'shopping cart', 'add to cart', 'checkout', 'product review',
    'terms of service', 'privacy policy', 'cookie policy',
    'subscribe', 'newsletter', 'unsubscribe',
    # Other
    'recipe', 'ingredients', 'cooking instructions',
    'travel itinerary', 'flight booking', 'hotel reservation',
]

# Layer 5: Structural patterns typical to forensic/medical reports
STRUCTURAL_PATTERNS = [
    'name of deceased', 'name of the deceased', 'name of dead body',
    'date of death', 'time of death', 'place of death',
    'date of autopsy', 'date of postmortem', 'date of examination',
    'brought by', 'identified by', 'police station',
    'fir no', 'fir number', 'case number', 'ud case',
    'medical examiner', 'examining doctor', 'autopsy performed by',
    'external examination', 'internal examination',
    'opinion as to cause of death', 'cause of death',
    'injuries on the body', 'injury list',
    'preservation of viscera', 'viscera preserved',
    'body received', 'dead body received',
    'clothes on the body', 'articles found',
    'rigor mortis present', 'post mortem lividity',
]


def is_postmortem_report(text):
    """
    Multi-layer scoring system to validate if uploaded file is a
    genuine forensic/postmortem/medical report.

    Scoring:
        Layer 1: Min length check (pass/fail)
        Layer 2: Mandatory keywords (0-25 points)
        Layer 3: Medical terminology density (0-40 points)
        Layer 4: Anti-pattern detection (pass/fail with penalty)
        Layer 5: Structural patterns (0-35 points)

    Returns:
        tuple(bool, str) — (is_valid, reason_message)
    """
    if not text:
        return False, "File is empty or no text could be extracted."

    text_lower = text.lower()
    word_count = len(text_lower.split())

    # ─── Layer 1: Minimum length ───
    if len(text) < 200 or word_count < 40:
        return False, "File is too short to be a forensic report. A valid report typically contains detailed examination findings."

    # ─── Layer 4: Anti-patterns (check early to fast-reject) ───
    anti_hits = []
    for pattern in ANTI_PATTERNS:
        if pattern in text_lower:
            anti_hits.append(pattern)

    if len(anti_hits) >= 2:
        return False, f"This file appears to be a non-medical document (detected: {', '.join(anti_hits[:3])}). Please upload a valid forensic/postmortem report."

    # ─── Layer 2: Mandatory keywords (0-25 points) ───
    mandatory_hits = sum(1 for kw in MANDATORY_KEYWORDS if kw in text_lower)

    if mandatory_hits == 0:
        return False, "No forensic/postmortem keywords found. Please upload a valid forensic report containing terms like 'postmortem', 'autopsy', 'cause of death', etc."

    mandatory_score = min(25, mandatory_hits * 6)  # Each hit = 6 pts, max 25

    # ─── Layer 3: Medical terminology density (0-40 points) ───
    medical_hits = sum(1 for term in MEDICAL_TERMS if term in text_lower)
    # Normalize by document length (per 500 words)
    density = (medical_hits / max(word_count, 1)) * 500
    medical_score = min(40, medical_hits * 2.5)  # Each hit = 2.5 pts, max 40

    # ─── Layer 5: Structural patterns (0-35 points) ───
    structural_hits = sum(1 for pat in STRUCTURAL_PATTERNS if pat in text_lower)
    structural_score = min(35, structural_hits * 5)  # Each hit = 5 pts, max 35

    # ─── Calculate total score ───
    total_score = mandatory_score + medical_score + structural_score

    # Anti-pattern penalty (if 1 hit, reduce score by 15)
    if len(anti_hits) == 1:
        total_score -= 15

    # ─── Decision ───
    if total_score >= 40:
        return True, f"Valid forensic report (confidence score: {min(100, int(total_score))}%)"
    elif total_score >= 25:
        return False, (
            f"File has some medical content but doesn't appear to be a complete forensic/postmortem report "
            f"(score: {int(total_score)}/100). Missing key elements like examination details, "
            f"cause of death, or autopsy findings. Please upload an official forensic report."
        )
    else:
        return False, (
            f"This file does not appear to be a medical or forensic report "
            f"(score: {int(total_score)}/100). Please upload a valid postmortem/autopsy/forensic report."
        )


def parse_body_conditions(form):
    """Parse body condition entries from the form data."""
    conditions = []
    # Form sends arrays: injury_type[], body_part[], severity[], description[], bleeding_level[]
    injury_types = form.getlist('injury_type[]')
    body_parts = form.getlist('body_part[]')
    severities = form.getlist('severity[]')
    descriptions = form.getlist('description[]')
    bleeding_levels = form.getlist('bleeding_level[]')

    for i in range(len(injury_types)):
        # Skip empty entries
        if not injury_types[i] and not (body_parts[i] if i < len(body_parts) else ''):
            continue

        conditions.append({
            'injury_type': injury_types[i] if i < len(injury_types) else '',
            'body_part': body_parts[i] if i < len(body_parts) else '',
            'severity': severities[i] if i < len(severities) else 'moderate',
            'description': descriptions[i] if i < len(descriptions) else '',
            'bleeding_level': bleeding_levels[i] if i < len(bleeding_levels) else 'none',
        })

    return conditions


def process_evidence_media_files(files, report_id):
    """
    Process uploaded evidence media files.
    Saves them, runs OCR, and returns metadata list.

    Args:
        files: list of FileStorage objects
        report_id: the report ID to associate with

    Returns:
        list of dicts with keys: filename, file_type, file_path, ocr_text
    """
    evidence_dir = os.path.join(UPLOAD_FOLDER, 'evidence', str(report_id))
    os.makedirs(evidence_dir, exist_ok=True)

    media_records = []
    processed = 0

    for file in files:
        if not file or file.filename == '':
            continue
        if not allowed_evidence_file(file.filename):
            continue
        if processed >= EVIDENCE_MAX_FILES:
            break

        filename = secure_filename(file.filename)
        # Avoid name collisions
        base, ext = os.path.splitext(filename)
        save_name = f"{base}_{processed}{ext}"
        save_path = os.path.join(evidence_dir, save_name)
        file.save(save_path)

        # Process for OCR
        result = process_evidence_file(
            save_path,
            frame_interval=EVIDENCE_FRAME_INTERVAL,
            max_frames=EVIDENCE_MAX_FRAMES,
        )

        media_records.append({
            'filename': save_name,
            'file_type': result['media_type'],
            'file_path': save_path,
            'ocr_text': result['ocr_text'],
        })
        processed += 1

    return media_records


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash("Please select a file to upload.")
            return redirect(url_for('upload_file'))

        if not allowed_file(file.filename):
            flash(f"Only files with extensions {ALLOWED_EXTENSIONS} are allowed.")
            return redirect(url_for('upload_file'))

        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        text = extract_report_text(save_path)
        if not text:
            flash("Unable to extract text from the file.")
            os.remove(save_path)
            return redirect(url_for('upload_file'))

        # Multi-layer validation
        is_valid, validation_msg = is_postmortem_report(text)
        if not is_valid:
            flash(f"❌ Rejected: {validation_msg}")
            os.remove(save_path)
            return redirect(url_for('upload_file'))

        # -------- NLP extraction --------
        forensic_info = extract_forensic_info(text)
        entities = extract_entities(text, forensic_info)

        # -------- Parse body conditions from form --------
        body_conditions = parse_body_conditions(request.form)
        scene_notes = request.form.get('scene_notes', '')

        # -------- Extract injuries mentioned in report --------
        report_injuries = extract_injuries_from_text(text)

        # -------- Cross-Verification (only if body conditions provided) --------
        verification = None
        evidence_texts = []

        # We need a report_id first for evidence folder — insert report now
        data_to_save = {
            'filename': filename,
            'extracted_text': text,
            'name': forensic_info.get('name'),
            'age': forensic_info.get('age'),
            'gender': forensic_info.get('gender'),
            'address': forensic_info.get('address'),
            'date_of_death': forensic_info.get('date_of_death'),
            'cause_of_death': forensic_info.get('cause_of_death'),
            'examiner': forensic_info.get('examiner'),
            'event_type': forensic_info.get('event_type'),
            'time_of_death': forensic_info.get('time_of_death'),
            'fir_info': forensic_info.get('fir_info'),
            'doctor_comments': forensic_info.get('doctor_comments'),
            'medical_history': forensic_info.get('medical_history'),
            'lab_results': forensic_info.get('lab_results'),
        }

        report_id = models.insert_report(data_to_save)

        # -------- Process evidence media --------
        evidence_files = request.files.getlist('evidence_media')
        evidence_media = []
        if evidence_files:
            evidence_media = process_evidence_media_files(evidence_files, report_id)
            if evidence_media:
                models.insert_evidence_media(report_id, evidence_media)
                evidence_texts = [m['ocr_text'] for m in evidence_media if m.get('ocr_text')]

        # -------- Cross-Verification --------
        if body_conditions:
            verification = cross_verify(
                forensic_info=forensic_info,
                report_injuries_text=report_injuries,
                body_conditions=body_conditions,
                report_text=text,
                evidence_texts=evidence_texts,
            )
            verification['scene_notes'] = scene_notes

        # Update report with verification data
        if verification:
            # Update the report row with AI results
            import sqlite3
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE reports SET
                        ai_cause_of_death = ?,
                        tampering_risk = ?,
                        consistency_score = ?
                    WHERE id = ?
                ''', (
                    verification.get('ai_cause_of_death'),
                    verification.get('tampering_risk'),
                    verification.get('consistency_score'),
                    report_id,
                ))
                conn.commit()

        # Save body conditions
        if body_conditions:
            models.insert_body_conditions(report_id, body_conditions)

        # Save verification results
        if verification:
            models.insert_verification(report_id, verification)

        # -------- Render result UI --------
        return render_template(
            'result.html',
            filename=filename,
            report_text=text,
            forensic_info=forensic_info,
            entities=entities,
            body_conditions=body_conditions,
            verification=verification,
            report_injuries=report_injuries,
            scene_notes=scene_notes,
            report_id=report_id,
            evidence_media=evidence_media,
        )

    return render_template('index.html')


@app.route('/reports')
def list_reports():
    reports = models.get_all_reports()
    return render_template('reports_list.html', reports=reports)


@app.route('/reports/<int:report_id>')
def report_detail(report_id):
    report = models.get_report_by_id(report_id)
    if not report:
        flash("Report not found")
        return redirect(url_for('list_reports'))

    body_conditions = models.get_body_conditions(report_id)
    verification = models.get_verification(report_id)
    evidence_media = models.get_evidence_media(report_id)

    return render_template(
        'report_detail.html',
        report=report,
        body_conditions=body_conditions,
        verification=verification,
        evidence_media=evidence_media,
    )


@app.route('/evidence/<int:report_id>/<filename>')
def serve_evidence(report_id, filename):
    """Serve evidence media files."""
    evidence_dir = os.path.join(UPLOAD_FOLDER, 'evidence', str(report_id))
    return send_from_directory(evidence_dir, filename)


if __name__ == '__main__':
    app.run(
        host=config['server']['host'],
        port=int(config['server']['port']),
        debug=config['server']['debug']
    )
