"""
Consistency Engine — AI-Assisted Forensic Evidence Validation
=============================================================
Runs rule-based consistency checks on every uploaded forensic report.
Detects:
  - Injury severity vs. narrative mismatches
  - Missing critical forensic entities
  - Temporal inconsistencies
  - Medical term contradictions
  - Narrative-entity alignment issues
  - Missing toxicology / lab references

Each flag includes an 'explanation' list for the Explainability Module (Upgrade 3).
"""

import re
from datetime import datetime


# ─── Severity descriptor words (low → high) ───
LOW_SEVERITY_WORDS = [
    'minor', 'slight', 'superficial', 'small', 'trivial', 'insignificant',
    'mild', 'negligible', 'no significant', 'no major', 'simple',
]

HIGH_SEVERITY_WORDS = [
    'multiple fracture', 'compound fracture', 'comminuted', 'severe hemorrhage',
    'massive bleeding', 'crush injury', 'fatal', 'extensive', 'life-threatening',
    'critical', 'catastrophic', 'devastating', 'deep penetrating', 'organ rupture',
    'brain hemorrhage', 'exsanguination',
]

# ─── Medical contradiction pairs (term_a, term_b) ───
CONTRADICTION_PAIRS = [
    ('no external trauma', 'laceration'),
    ('no external trauma', 'abrasion'),
    ('no external trauma', 'contusion'),
    ('no external trauma', 'wound'),
    ('no external injury', 'fracture'),
    ('no external injury', 'laceration'),
    ('minor injury', 'multiple fractures'),
    ('minor injury', 'hemorrhage'),
    ('minor injury', 'organ damage'),
    ('minor injury', 'organ rupture'),
    ('no fracture', 'fracture of'),
    ('no fracture', 'fractured'),
    ('no bleeding', 'hemorrhage'),
    ('no bleeding', 'massive blood loss'),
    ('natural death', 'stab wound'),
    ('natural death', 'gunshot'),
    ('natural death', 'strangulation'),
    ('natural death', 'ligature marks'),
    ('suicide', 'defensive wound'),
    ('suicide', 'defense wound'),
    ('no poisoning', 'toxicology positive'),
    ('no drugs', 'drug overdose'),
]

# ─── Required forensic entities ───
REQUIRED_ENTITIES = [
    ('name', 'Name of deceased', 'CRITICAL'),
    ('cause_of_death', 'Cause of death', 'CRITICAL'),
    ('date_of_death', 'Date of death', 'HIGH'),
    ('examiner', 'Medical examiner / Doctor', 'HIGH'),
    ('age', 'Age of deceased', 'MEDIUM'),
    ('gender', 'Gender of deceased', 'MEDIUM'),
]


def run_consistency_analysis(text, forensic_info, entities, report_injuries):
    """
    Run all consistency checks on a forensic report.

    Args:
        text: str — full extracted text of the report
        forensic_info: dict — extracted key fields (name, age, COD, etc.)
        entities: list — NER entities [{'type': ..., 'value': ...}, ...]
        report_injuries: list — injury strings extracted from text

    Returns:
        dict with:
            consistency_score: int (0-100)
            confidence: str ('High'/'Medium'/'Low')
            flags: list of flag dicts
            checks_passed: int
            checks_total: int
            explanations_summary: list of summary strings
    """
    if not text:
        return {
            'consistency_score': 0,
            'confidence': 'Low',
            'flags': [{'type': 'empty_report', 'message': 'No text to analyze',
                       'severity': 'CRITICAL',
                       'explanation': ['The uploaded file produced no extractable text.',
                                       'Cannot perform consistency analysis.']}],
            'checks_passed': 0,
            'checks_total': 1,
            'explanations_summary': ['Empty report — no analysis possible.'],
        }

    all_flags = []

    # ── Check 1: Injury severity mismatch ──
    flags_1 = check_injury_severity_mismatch(text, report_injuries)
    all_flags.extend(flags_1)

    # ── Check 2: Missing entities ──
    flags_2 = check_missing_entities(forensic_info)
    all_flags.extend(flags_2)

    # ── Check 3: Temporal consistency ──
    flags_3 = check_temporal_consistency(forensic_info, text)
    all_flags.extend(flags_3)

    # ── Check 4: Medical contradictions ──
    flags_4 = check_medical_contradictions(text)
    all_flags.extend(flags_4)

    # ── Check 5: Narrative-entity alignment ──
    flags_5 = check_narrative_entity_alignment(text, entities, forensic_info)
    all_flags.extend(flags_5)

    # ── Check 6: Toxicology mention ──
    flags_6 = check_toxicology_mention(text, forensic_info)
    all_flags.extend(flags_6)

    # ── Scoring ──
    total_checks = 6
    failed_checks = 0
    if flags_1:
        failed_checks += 1
    if flags_2:
        failed_checks += 1
    if flags_3:
        failed_checks += 1
    if flags_4:
        failed_checks += 1
    if flags_5:
        failed_checks += 1
    if flags_6:
        failed_checks += 1

    checks_passed = total_checks - failed_checks

    # Weight by severity
    severity_penalty = 0
    for flag in all_flags:
        if flag['severity'] == 'CRITICAL':
            severity_penalty += 15
        elif flag['severity'] == 'HIGH':
            severity_penalty += 10
        elif flag['severity'] == 'MEDIUM':
            severity_penalty += 5
        else:
            severity_penalty += 2

    base_score = (checks_passed / total_checks) * 100
    consistency_score = max(0, min(100, int(base_score - severity_penalty)))

    # Confidence
    if len(all_flags) == 0:
        confidence = 'High'
    elif len(all_flags) <= 2 and all(f['severity'] in ('LOW', 'MEDIUM') for f in all_flags):
        confidence = 'High'
    elif len(all_flags) <= 3:
        confidence = 'Medium'
    else:
        confidence = 'Low'

    # Summary
    summary = []
    if flags_1:
        summary.append(f'Injury-description mismatch detected ({len(flags_1)} flag(s))')
    if flags_2:
        summary.append(f'Missing critical entities ({len(flags_2)} field(s))')
    if flags_3:
        summary.append(f'Temporal inconsistency ({len(flags_3)} issue(s))')
    if flags_4:
        summary.append(f'Medical contradictions found ({len(flags_4)} pair(s))')
    if flags_5:
        summary.append(f'Narrative-entity alignment issue ({len(flags_5)})')
    if flags_6:
        summary.append(f'Toxicology/lab reference issue ({len(flags_6)})')
    if not summary:
        summary.append('All consistency checks passed — report appears internally consistent.')

    return {
        'consistency_score': consistency_score,
        'confidence': confidence,
        'flags': all_flags,
        'checks_passed': checks_passed,
        'checks_total': total_checks,
        'explanations_summary': summary,
    }


# ════════════════════════════════════════════════════════════
# CHECK 1: Injury Severity Mismatch
# ════════════════════════════════════════════════════════════

def check_injury_severity_mismatch(text, report_injuries):
    """
    If narrative uses low-severity words but NER/extraction found
    high-severity injury terms → flag as mismatch.
    """
    flags = []
    text_lower = text.lower()

    low_found = [w for w in LOW_SEVERITY_WORDS if w in text_lower]
    high_found = [w for w in HIGH_SEVERITY_WORDS if w in text_lower]

    if low_found and high_found:
        flags.append({
            'type': 'injury_mismatch',
            'message': 'Injury-description severity mismatch detected',
            'severity': 'HIGH',
            'explanation': [
                f'Report narrative uses low-severity terms: {", ".join(low_found[:3])}',
                f'But also contains high-severity terms: {", ".join(high_found[:3])}',
                'Conflict detected in severity classification — '
                'the narrative description may downplay actual injury severity.',
            ],
        })

    # Check if report_injuries mention severe terms but narrative says "minor"
    if report_injuries:
        severe_injuries = [inj for inj in report_injuries
                          if any(h in inj.lower() for h in HIGH_SEVERITY_WORDS)]
        if severe_injuries and low_found:
            flags.append({
                'type': 'injury_mismatch',
                'message': 'Extracted injuries contradict narrative severity',
                'severity': 'HIGH',
                'explanation': [
                    f'NLP extracted severe injuries: {severe_injuries[0][:80]}...',
                    f'But narrative contains: "{low_found[0]}"',
                    'This mismatch suggests potential report manipulation.',
                ],
            })

    return flags


# ════════════════════════════════════════════════════════════
# CHECK 2: Missing Entity Detection
# ════════════════════════════════════════════════════════════

def check_missing_entities(forensic_info):
    """Check if critical forensic fields are missing from extraction."""
    flags = []

    for field_key, field_name, severity in REQUIRED_ENTITIES:
        value = forensic_info.get(field_key)
        if not value or value.strip() == '' or value.strip() == '—':
            flags.append({
                'type': 'missing_entity',
                'message': f'Missing: {field_name}',
                'severity': severity,
                'explanation': [
                    f'The field "{field_name}" was not found in the report.',
                    'A valid forensic/postmortem report should contain this information.',
                    f'Severity: {severity} — this field is '
                    f'{"essential" if severity == "CRITICAL" else "important"} for forensic validation.',
                ],
            })

    return flags


# ════════════════════════════════════════════════════════════
# CHECK 3: Temporal Consistency
# ════════════════════════════════════════════════════════════

def check_temporal_consistency(forensic_info, text):
    """
    Validate date/time coherence:
    - Date of death should be before or on autopsy date
    - Unreasonable time gaps
    """
    flags = []
    text_lower = text.lower()

    # Extract autopsy/PM date from text
    autopsy_date_str = None
    for pattern in [
        r'date of (?:autopsy|postmortem|post[\s-]?mortem|examination)[\s:]+([^\n]+)',
        r'(?:autopsy|postmortem|pm) (?:performed|conducted|done) on[\s:]+([^\n]+)',
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            autopsy_date_str = m.group(1).strip()
            break

    death_date_str = forensic_info.get('date_of_death', '')
    time_of_death = forensic_info.get('time_of_death', '')

    # Check for future dates mentioned (basic sanity)
    year_matches = re.findall(r'\b(20\d{2}|19\d{2})\b', text)
    current_year = datetime.now().year
    future_years = [y for y in year_matches if int(y) > current_year]
    if future_years:
        flags.append({
            'type': 'temporal_inconsistency',
            'message': 'Future date detected in report',
            'severity': 'HIGH',
            'explanation': [
                f'Report contains year(s): {", ".join(future_years[:3])}',
                f'Current year is {current_year}.',
                'Dates in the future indicate possible report fabrication or error.',
            ],
        })

    # Check if both death date and autopsy date exist but death date is after autopsy
    if death_date_str and autopsy_date_str:
        try:
            # Try common date formats
            death_parsed = _try_parse_date(death_date_str)
            autopsy_parsed = _try_parse_date(autopsy_date_str)
            if death_parsed and autopsy_parsed:
                if death_parsed > autopsy_parsed:
                    flags.append({
                        'type': 'temporal_inconsistency',
                        'message': 'Death date is after autopsy date',
                        'severity': 'CRITICAL',
                        'explanation': [
                            f'Date of death: {death_date_str}',
                            f'Date of autopsy: {autopsy_date_str}',
                            'Death cannot occur after the autopsy — '
                            'this is a critical temporal inconsistency.',
                        ],
                    })
                # Check for unreasonable gap (>30 days)
                gap = (autopsy_parsed - death_parsed).days
                if gap > 30:
                    flags.append({
                        'type': 'temporal_inconsistency',
                        'message': f'Unusual gap ({gap} days) between death and autopsy',
                        'severity': 'MEDIUM',
                        'explanation': [
                            f'Death date: {death_date_str}',
                            f'Autopsy date: {autopsy_date_str}',
                            f'Gap: {gap} days — typical autopsy is within 1-3 days.',
                            'Extended delay may indicate procedural irregularity.',
                        ],
                    })
        except Exception:
            pass  # Could not parse dates — skip this check

    return flags


def _try_parse_date(date_str):
    """Try to parse a date string in common formats."""
    formats = [
        '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y',
        '%d %B %Y', '%d %b %Y', '%B %d, %Y', '%b %d, %Y',
        '%d.%m.%Y', '%Y/%m/%d',
    ]
    # Clean up
    clean = date_str.strip().split('\n')[0].strip()
    # Remove day names
    clean = re.sub(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)[,\s]*',
                   '', clean, flags=re.I).strip()

    for fmt in formats:
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    return None


# ════════════════════════════════════════════════════════════
# CHECK 4: Medical Contradictions
# ════════════════════════════════════════════════════════════

def check_medical_contradictions(text):
    """Detect contradictory medical terms in the same report."""
    flags = []
    text_lower = text.lower()

    for term_a, term_b in CONTRADICTION_PAIRS:
        if term_a in text_lower and term_b in text_lower:
            flags.append({
                'type': 'medical_contradiction',
                'message': f'Contradictory terms: "{term_a}" vs "{term_b}"',
                'severity': 'HIGH',
                'explanation': [
                    f'Report contains: "{term_a}"',
                    f'But also contains: "{term_b}"',
                    'These terms are medically contradictory and cannot '
                    'logically coexist in a consistent forensic report.',
                    'This may indicate report manipulation or error.',
                ],
            })

    return flags


# ════════════════════════════════════════════════════════════
# CHECK 5: Narrative-Entity Alignment
# ════════════════════════════════════════════════════════════

def check_narrative_entity_alignment(text, entities, forensic_info):
    """
    Check if NER-extracted persons appear in structured header fields.
    If NER finds people not in the header → could be unlisted witnesses/parties.
    """
    flags = []

    person_entities = [e['value'] for e in entities if e.get('type') == 'PERSON']
    known_names = []
    if forensic_info.get('name'):
        known_names.append(forensic_info['name'].lower())
    if forensic_info.get('examiner'):
        known_names.append(forensic_info['examiner'].lower())

    # Find persons mentioned in text but not in structured fields
    unmatched = []
    for person in person_entities:
        person_lower = person.lower().strip()
        if len(person_lower) < 4:
            continue
        if not any(person_lower in known or known in person_lower
                   for known in known_names if known):
            unmatched.append(person)

    if len(unmatched) > 3:
        flags.append({
            'type': 'narrative_alignment',
            'message': f'{len(unmatched)} persons in text not in structured fields',
            'severity': 'LOW',
            'explanation': [
                f'NER detected {len(unmatched)} person name(s) in the text:',
                f'  {", ".join(unmatched[:5])}',
                'These names are not found in the extracted header fields '
                '(deceased name, examiner).',
                'This is informational — may include witnesses, police officers, etc.',
            ],
        })

    return flags


# ════════════════════════════════════════════════════════════
# CHECK 6: Toxicology Mention Check
# ════════════════════════════════════════════════════════════

def check_toxicology_mention(text, forensic_info):
    """
    If COD suggests poisoning or drug-related death but no toxicology
    results are mentioned → flag.
    """
    flags = []
    text_lower = text.lower()
    cod = (forensic_info.get('cause_of_death') or '').lower()

    poison_keywords = ['poison', 'toxicity', 'overdose', 'drug',
                       'chemical', 'substance', 'intoxication', 'cyanide',
                       'organophosphate', 'arsenic']

    tox_results_keywords = ['toxicology', 'tox report', 'tox screen',
                            'blood test', 'chemical analysis',
                            'viscera preserved', 'viscera sent']

    cod_suggests_poison = any(kw in cod for kw in poison_keywords)
    text_suggests_poison = any(kw in text_lower for kw in poison_keywords)
    has_tox_results = any(kw in text_lower for kw in tox_results_keywords)

    if (cod_suggests_poison or text_suggests_poison) and not has_tox_results:
        flags.append({
            'type': 'missing_toxicology',
            'message': 'Poisoning/drug terms found but no toxicology results',
            'severity': 'HIGH',
            'explanation': [
                'Report mentions poisoning or drug-related terms.',
                'But no toxicology results or viscera preservation is mentioned.',
                'A forensic report claiming or suspecting poisoning should '
                'include toxicology screening results.',
                'This omission may indicate incomplete investigation.',
            ],
        })

    return flags
