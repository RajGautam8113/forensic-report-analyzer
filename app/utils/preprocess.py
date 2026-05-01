# utils/preprocess.py
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# utils/preprocess.py
KEYWORDS = ['postmortem', 'autopsy', 'forensic', 'cause of death', 'medical officer']

def is_postmortem_report(text):
    return any(kw in text.lower() for kw in KEYWORDS)
# utils/preprocess.py (or utils/extractors.py)
import re

def extract_fields(text):
    fields = {}
    fields['name']    = re.search(r'Name\s*:\s*(.*)', text)
    fields['age']     = re.search(r'Age\s*:\s*(.*)', text)
    fields['gender']  = re.search(r'Gender\s*:\s*(.*)', text)
    # Aur bhi fields add karo
    return {k: (m.group(1).strip() if m else None) for k, m in fields.items()}
