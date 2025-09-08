import re
import spacy

# NLP model load
nlp = spacy.load("en_core_web_sm")

def extract_forensic_info(text):
    info = {}

    match = re.search(r'Name\s*:\s*([A-Za-z ,.\'-]+)', text)
    info['Name'] = match.group(1).strip() if match else ""

    match = re.search(r'Age\s*:\s*(\d{1,3})\s*years?', text)
    if not match:
        match = re.search(r'(\d{1,3})[- ]?years?[- ]?old', text)
    info['Age'] = f"{match.group(1)} years" if match else ""

    match = re.search(r'Gender\s*:\s*(Male|Female|Other)', text, re.I)
    if not match:
        match = re.search(r'\b(male|female|man|woman|boy|girl)\b', text, re.I)
    info['Gender'] = match.group(1).capitalize() if match else ""

    match = re.search(r'Address\s*:\s*(.+)', text)
    info['Address'] = match.group(1).strip() if match else ""

    match = re.search(r'Date of Death\s*:\s*([^\n]+)', text)
    if not match:
        match = re.search(r'on (\d{1,2}/\d{1,2}/\d{2,4})', text)
    info['Date of Death'] = match.group(1).strip() if match else ""

    match = re.search(r'Cause of Death\s*:\s*([^\n]+)', text)
    info['Cause of Death'] = match.group(1).strip() if match else ""

    match = re.search(r'Examiner\s*:\s*([A-Za-z ,.\'-]+)', text)
    info['Examiner'] = match.group(1).strip() if match else ""

    return info

def classify_entity(ent_text, ent_label):
    mapping = {
        'PERSON': 'Name',
        'DATE': 'Date',
        'GPE': 'Location',
        'ORG': 'Organization',
        'LOC': 'Location',
        'NORP': 'Group',
        'MONEY': 'Amount',
        'TIME': 'Time',
        'CARDINAL': 'Number'
    }
    return mapping.get(ent_label, 'Other')

def extract_entities(text, forensic_info=None):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        cls = classify_entity(ent.text, ent.label_)
        entities.append({
            'text': ent.text,
            'label': cls,
            'original_label': ent.label_
        })
    return entities
