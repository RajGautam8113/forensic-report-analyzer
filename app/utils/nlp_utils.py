import re
import spacy
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "en_core_web_sm")

nlp = spacy.load(MODEL_PATH)

def extract_forensic_info(text: str) -> dict:
    """
    Key fields for 'Key Report Details' section.
    Enhanced: now also extracts injuries, timeline, labs from report text.
    """
    info = {}
    if not text:
        return info

    # Name of Deceased (multiple patterns)
    for pattern in [
        r"Name of (?:Deceased|the Deceased|Dead Body|Patient|Victim)[\s:]+(.+)",
        r"Deceased[\s:]+(.+)",
        r"Name[\s:]+([A-Z][a-z]+ [A-Z][a-z]+)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["name"] = m.group(1).strip().split('\n')[0].strip()
            break

    # Age (e.g. "Age: 42 years" or "Age: 42")
    for pattern in [
        r"Age[\s:]+(\d{1,3})\s*(?:years?|yrs?)?",
        r"(\d{1,3})\s*(?:year|yr)[\s\-]*old",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["age"] = m.group(1).strip()
            break

    # Gender
    m = re.search(r"Gender[\s:]+\s*(Male|Female|Other|Transgender)", text, re.I)
    if m:
        info["gender"] = m.group(1).strip().title()
    else:
        # Try to detect from text
        text_lower = text.lower()
        if ' male ' in text_lower or 'male body' in text_lower:
            info["gender"] = "Male"
        elif ' female ' in text_lower or 'female body' in text_lower:
            info["gender"] = "Female"

    # Address
    for pattern in [
        r"(?:Residential )?Address[\s:]+(.+)",
        r"Resident of[\s:]+(.+)",
        r"R/o[\s:]+(.+)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["address"] = m.group(1).strip().split('\n')[0].strip()
            break

    # Date of Death
    for pattern in [
        r"Date of Death[\s\(]*(?:Approximate)?[\s\):]*([^\n]+)",
        r"Date of (?:Incident|Accident)[\s:]+([^\n]+)",
        r"Died on[\s:]+([^\n]+)",
        r"Death (?:on|date)[\s:]+([^\n]+)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["date_of_death"] = m.group(1).strip()
            break

    # Primary Cause of Death (enhanced patterns)
    for pattern in [
        r"(?:Primary |Official |Immediate )?Cause of Death[\s:]+([^\n]+)",
        r"COD[\s:]+([^\n]+)",
        r"Death (?:was |is )?(?:due to|caused by)[\s:]+([^\n]+)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["cause_of_death"] = m.group(1).strip()
            break

    # Examiner
    for pattern in [
        r"(?:Chief )?Medical (?:Examiner|Officer)[\s:]+([^\n]+)",
        r"Examining Doctor[\s:]+([^\n]+)",
        r"Autopsy (?:performed|conducted) by[\s:]+([^\n]+)",
        r"Dr\.?\s+([A-Z][a-z]+ [A-Z][a-z]+)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["examiner"] = m.group(1).strip()
            break

    # ========== ENHANCED: Additional fields ==========

    # Time of Death
    for pattern in [
        r"Time of Death[\s:]+([^\n]+)",
        r"Time of (?:Incident|Accident)[\s:]+([^\n]+)",
        r"Estimated Time of Death[\s:]+([^\n]+)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["time_of_death"] = m.group(1).strip()
            break

    # Type of Event
    for pattern in [
        r"Type of (?:Event|Incident|Death)[\s:]+([^\n]+)",
        r"Manner of Death[\s:]+([^\n]+)",
        r"Nature of (?:Event|Incident)[\s:]+([^\n]+)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["event_type"] = m.group(1).strip()
            break

    # FIR / Police info
    for pattern in [
        r"(?:FIR|Police)[\s/]*(?:Summary|Report|No\.?)[\s:]+([^\n]+)",
        r"Filed (?:complaint|FIR) under[\s:]+([^\n]+)",
        r"(?:Police|FIR) (?:Case|Number)[\s:]+([^\n]+)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["fir_info"] = m.group(1).strip()
            break

    # Doctor Comments
    for pattern in [
        r"Doctor(?:'s)? Comments?[\s:]+([^\n]+(?:\n(?![A-Z])[^\n]+)*)",
        r"(?:Specialist|Expert) Notes?[\s:]+([^\n]+(?:\n(?![A-Z])[^\n]+)*)",
        r"Clinical (?:Notes?|Opinion)[\s:]+([^\n]+(?:\n(?![A-Z])[^\n]+)*)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["doctor_comments"] = m.group(1).strip()
            break

    # Pre-existing Medical History
    for pattern in [
        r"(?:Pre-existing |Past |Previous )?Medical History[\s:]+([^\n]+)",
        r"Known (?:medical )?conditions?[\s:]+([^\n]+)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            info["medical_history"] = m.group(1).strip()
            break

    # Lab Results / Toxicology
    tox_patterns = [
        r"(?:Toxicology|Toxins?|Drugs?)[\s:]+([^\n]+)",
        r"Alcohol[\s:]+([^\n]+)",
        r"Blood (?:Alcohol|Test)[\s:]+([^\n]+)",
    ]
    lab_results = []
    for pattern in tox_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            lab_results.append(m.group(0).strip())
    if lab_results:
        info["lab_results"] = '; '.join(lab_results)

    return info


def extract_entities(text: str, forensic_info: dict) -> list:
    """
    spaCy NER se entities list bana kar dega
    jo 'Named Entities Found' table me dikhani hai.
    """
    entities = []
    if not text:
        return entities

    doc = nlp(text)

    # Useful labels only
    allowed_labels = {"PERSON", "ORG", "GPE", "LOC", "DATE", "TIME", "CARDINAL", "NORP"}
    seen = set()

    for ent in doc.ents:
        value = ent.text.strip()
        label = ent.label_

        if not value or len(value) <= 2:
            continue
        if label not in allowed_labels:
            continue

        key = (label, value)
        if key in seen:
            continue
        seen.add(key)

        entities.append({
            "type": label,
            "value": value
        })

    return entities


def extract_injuries_from_text(text: str) -> list:
    """
    Extract injury descriptions mentioned in the report text.
    Returns list of injury strings found in the report.
    """
    if not text:
        return []

    injuries = []
    text_lower = text.lower()

    # Look for injury-related sections
    injury_section_patterns = [
        r'(?:Injury\s*List|External\s*Examination|Injuries?\s*(?:Found|Observed|Noted)|'
        r'Physical\s*Examination|Autopsy\s*Findings?)[\s:]*\n((?:[\s\S]*?\n){1,15})',
    ]

    for pattern in injury_section_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            section = m.group(1)
            lines = section.strip().split('\n')
            for line in lines:
                line = line.strip(' -•*\t')
                if len(line) > 5 and any(kw in line.lower() for kw in
                    ['fracture', 'wound', 'cut', 'bleeding', 'bruise', 'injury',
                     'laceration', 'burn', 'hemorrhage', 'abrasion', 'swelling',
                     'contusion', 'trauma', 'damage', 'rupture']):
                    injuries.append(line)

    # Individual injury patterns
    injury_kw_patterns = [
        r'(?:fracture|fractured)\s+(?:of\s+)?[^\n.]{3,50}',
        r'(?:laceration|lacerations?)\s+(?:on|of|over)\s+[^\n.]{3,50}',
        r'(?:wound|wounds)\s+(?:on|of|over)\s+[^\n.]{3,50}',
        r'(?:bleeding|hemorrhage)\s+(?:from|in|of)\s+[^\n.]{3,50}',
        r'(?:bruise|contusion)\s+(?:on|of|over)\s+[^\n.]{3,50}',
        r'(?:burn|burns)\s+(?:on|of|over)\s+[^\n.]{3,50}',
    ]

    for pattern in injury_kw_patterns:
        matches = re.finditer(pattern, text, re.I)
        for match in matches:
            inj = match.group(0).strip()
            if inj not in injuries:
                injuries.append(inj)

    return injuries[:20]
