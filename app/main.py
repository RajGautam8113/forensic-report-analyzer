from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
import pdfplumber
import os
import re

import models  # Database models
from utils.nlp_utils import extract_forensic_info, extract_entities  # NLP utils

app = Flask(__name__)
app.secret_key = 'replace_with_secure_key'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize DB on app start
models.init_db()

def extract_forensic_info(text):
    info = {}

    # Name
    match = re.search(r'Name\s*:\s*([A-Za-z ,.\'-]+)', text)
    info['Name'] = match.group(1).strip() if match else ""

    # Age (Improve detection!)
    match = re.search(r'Age\s*:\s*(\d{1,3})\s*years?', text)
    if not match:
        match = re.search(r'(\d{1,3})[- ]?years?[- ]?old', text)
    if not match:
        match = re.search(r'(\d{1,3})\s*years', text)
    info['Age'] = f"{match.group(1)} years" if match else ""

    # Gender (avoid capturing Age as Gender!)
    match = re.search(r'Gender\s*:\s*(Male|Female|Other)', text, re.I)
    if not match:
        match = re.search(r'\b(male|female)\b', text, re.I)
    info['Gender'] = match.group(1).capitalize() if match else ""

    # Rest fields same as before...
    match = re.search(r'Address\s*:\s*(.+)', text)
    info['Address'] = match.group(1).strip() if match else ""

    match = re.search(r'Date of Death\s*:\s*([^\n]+)', text)
    info['Date of Death'] = match.group(1).strip() if match else ""

    match = re.search(r'Cause of Death\s*:\s*([^\n]+)', text)
    info['Cause of Death'] = match.group(1).strip() if match else ""

    match = re.search(r'Examiner\s*:\s*([A-Za-z ,.\'-]+)', text)
    info['Examiner'] = match.group(1).strip() if match else ""

    return info


def extract_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pt = page.extract_text()
            if pt:
                text += pt + "\n"
    return text


def extract_txt_text(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_report_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return extract_pdf_text(filepath)
    elif ext == ".txt":
        return extract_txt_text(filepath)
    else:
        return "Unsupported file format."


def clean_text(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f or f.filename == '':
            flash("Please select a file to upload.")
            return redirect(url_for('upload_file'))

        filename = secure_filename(f.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        f.save(save_path)

        raw_text = extract_report_text(save_path)
        clean_report = clean_text(raw_text)
        forensic_info = extract_forensic_info(clean_report)
        entities = extract_entities(clean_report, forensic_info)

        data_to_save = forensic_info.copy()
        data_to_save.update({
            'filename': filename,
            'extracted_text': clean_report
        })
        models.insert_report(data_to_save)

        return render_template('result.html',
                               filename=filename,
                               report_text=clean_report,
                               forensic_info=forensic_info,
                               entities=entities)
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

    keys = ['id', 'filename', 'extracted_text', 'Name', 'Age', 'Gender', 'Address', 'Date of Death', 'Cause of Death', 'Examiner']
    report_data = dict(zip(keys, report))

    return render_template('report_detail.html', report=report_data)


if __name__ == '__main__':
    app.run(debug=True)
