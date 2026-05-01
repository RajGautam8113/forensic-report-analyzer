from flask import Flask, request, render_template
app = Flask(__name__)
from werkzeug.utils import secure_filename
from utils.preprocess import allowed_file
from utils.ocr_utils import extract_text_from_pdf
from utils.preprocess import is_postmortem_report
from utils.preprocess import extract_fields
from flask import request, render_template
from utils.preprocess import allowed_file, is_postmortem_report, extract_fields
from utils.ocr_utils import extract_text_from_pdf

@app.route('/upload', methods=['POST'])
def upload_report():
    file = request.files['file']
    if not allowed_file(file.filename):
        return "Only PDF files are accepted!"
    
    file_path = 'uploads/' + secure_filename(file.filename)   # uploads folder me save karo
    file.save(file_path)

    text = extract_text_from_pdf(file_path)
    if not is_postmortem_report(text):
        return "Incorrect file type. Please upload an actual postmortem report."

    report_data = extract_fields(text)
    return render_template('result.html', data=report_data)

# Removed the unreachable code and misplaced print statement.
# The function should return after rendering the template.

# Remove:
# return "Report not found", 404
# print(report_data)