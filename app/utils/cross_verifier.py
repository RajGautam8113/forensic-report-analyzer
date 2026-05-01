"""
Cross-Verification Engine
Compares forensic report data with on-the-spot body conditions
to detect inconsistencies, tampering, and produce verification report.
"""

from utils.injury_analyzer import analyze_injuries, determine_ai_cause_of_death, detect_red_flags


def cross_verify(forensic_info, report_injuries_text, body_conditions, report_text='', evidence_texts=None):
    """
    Cross-verify forensic report against observed body conditions.

    Args:
        forensic_info: dict — extracted info from report (name, age, cause_of_death, etc.)
        report_injuries_text: list — injuries mentioned IN the report text
        body_conditions: list of dicts — injuries observed at the scene
            Each dict: {injury_type, body_part, severity, description, bleeding_level}
        report_text: str — full extracted text of the report
        evidence_texts: list of str — OCR text from uploaded evidence images/videos

    Returns:
        dict — complete verification result
    """
    report_cod = forensic_info.get('cause_of_death', '') or ''
    evidence_combined = '\n'.join(evidence_texts or []).lower()

    # 1. Analyze body conditions independently
    ai_result = determine_ai_cause_of_death(body_conditions, forensic_info)
    analysis = ai_result['analysis']

    # 2. Find matches and mismatches
    matches = []
    missing_from_report = []
    suspicious = []

    report_text_lower = (report_text or '').lower()

    for condition in body_conditions:
        inj_type = (condition.get('injury_type') or '').lower()
        body_part = (condition.get('body_part') or '').lower()
        severity = (condition.get('severity') or '').lower()
        description = (condition.get('description') or '').lower()

        # Check if this injury is mentioned in the report
        search_terms = [inj_type, body_part]
        if description:
            # Also check key phrases from description
            search_terms.extend(description.split()[:5])

        mentioned_in_report = any(term in report_text_lower for term in search_terms if len(term) > 3)

        # Also check if evidence media text corroborates this injury
        evidence_corroborates = False
        if evidence_combined:
            evidence_corroborates = any(
                term in evidence_combined for term in search_terms if len(term) > 3
            )

        if mentioned_in_report:
            note = f"{inj_type.title()} on {body_part} — found in both report and body condition"
            if evidence_corroborates:
                note += " (also corroborated by evidence media)"
            matches.append({
                'injury': condition,
                'status': 'MATCH',
                'evidence_corroborated': evidence_corroborates,
                'note': note,
            })
        else:
            if severity in ['severe', 'critical', 'fatal']:
                # Severe injury NOT in report = highly suspicious
                note = f"CRITICAL: {severity.upper()} {inj_type} on {body_part} observed at scene but NOT mentioned in forensic report"
                if evidence_corroborates:
                    note += " — CONFIRMED by uploaded evidence media!"
                suspicious.append({
                    'injury': condition,
                    'status': 'SUSPICIOUS',
                    'evidence_corroborated': evidence_corroborates,
                    'note': note,
                })
            else:
                note = f"{inj_type.title()} on {body_part} observed at scene but not in report"
                if evidence_corroborates:
                    note += " — supported by evidence media"
                missing_from_report.append({
                    'injury': condition,
                    'status': 'MISSING',
                    'evidence_corroborated': evidence_corroborates,
                    'note': note,
                })

    # 3. Check for injuries in report but NOT in body conditions
    extra_in_report = []
    for inj_text in report_injuries_text:
        inj_lower = inj_text.lower()
        found_in_body = False
        for condition in body_conditions:
            cond_text = f"{condition.get('injury_type', '')} {condition.get('body_part', '')} {condition.get('description', '')}".lower()
            if any(word in cond_text for word in inj_lower.split() if len(word) > 3):
                found_in_body = True
                break
        if not found_in_body:
            # Check if evidence media mentions this
            evidence_has = evidence_combined and any(
                word in evidence_combined for word in inj_lower.split() if len(word) > 3
            )
            note = f"Report mentions '{inj_text}' but not observed in body condition"
            if evidence_has:
                note += " — however, evidence media may show this"
            extra_in_report.append({
                'injury_text': inj_text,
                'status': 'EXTRA_IN_REPORT',
                'note': note,
            })

    # 4. COD consistency check
    cod_match = False
    cod_note = ''
    ai_cod = ai_result['ai_cause']

    if report_cod and ai_cod:
        # Check if they broadly agree
        report_words = set(report_cod.lower().split())
        ai_words = set(ai_cod.lower().split())
        common = report_words & ai_words
        # Also check substring match
        if (report_cod.lower() in ai_cod.lower() or
            ai_cod.lower() in report_cod.lower() or
            len(common) >= 2):
            cod_match = True
            cod_note = 'Report cause of death is consistent with injury analysis.'
        else:
            cod_match = False
            cod_note = f'MISMATCH: Report states "{report_cod}" but injury analysis suggests "{ai_cod}"'

    # 5. Calculate consistency score
    total_checks = max(len(body_conditions), 1)
    match_count = len(matches)
    mismatch_count = len(suspicious) + len(missing_from_report)

    # Base score from injury matching
    injury_score = (match_count / total_checks) * 60  # 60% weight

    # COD consistency (25% weight)
    cod_score = 25 if cod_match else 0

    # Penalty for suspicious findings (15% weight)
    suspicious_penalty = min(15, len(suspicious) * 5)
    missing_penalty = min(10, len(missing_from_report) * 2)
    extra_penalty = min(5, len(extra_in_report) * 2)

    consistency_score = max(0, min(100,
        injury_score + cod_score + 15 - suspicious_penalty - missing_penalty - extra_penalty
    ))

    # Evidence media bonus/penalty:
    # If evidence corroborates suspicious items, LOWER the consistency score (report is more suspicious)
    evidence_corroborated_suspicious = sum(
        1 for s in suspicious if s.get('evidence_corroborated')
    )
    if evidence_corroborated_suspicious > 0:
        consistency_score = max(0, consistency_score - (evidence_corroborated_suspicious * 8))

    # If evidence corroborates matches, slightly boost
    evidence_corroborated_matches = sum(
        1 for m in matches if m.get('evidence_corroborated')
    )
    if evidence_corroborated_matches > 0:
        consistency_score = min(100, consistency_score + (evidence_corroborated_matches * 2))

    # 6. Determine tampering risk
    red_flags = detect_red_flags(report_cod, body_conditions)

    # Add custom red flags based on cross-verification
    if len(suspicious) >= 2:
        red_flags.append({
            'name': 'Multiple unreported injuries',
            'message': f'{len(suspicious)} severe/critical injuries observed at scene but not mentioned in forensic report.',
            'severity': 'CRITICAL',
        })

    if not cod_match and report_cod:
        red_flags.append({
            'name': 'Cause of death mismatch',
            'message': cod_note,
            'severity': 'HIGH',
        })

    if len(extra_in_report) >= 2:
        red_flags.append({
            'name': 'Report mentions unobserved injuries',
            'message': f'Report describes {len(extra_in_report)} injuries not observed at the scene — possible fabrication.',
            'severity': 'MEDIUM',
        })

    # Evidence-specific red flags
    if evidence_corroborated_suspicious >= 1:
        red_flags.append({
            'name': 'Evidence confirms unreported injuries',
            'message': f'Uploaded evidence media confirms {evidence_corroborated_suspicious} injury/injuries that the forensic report did NOT mention. Strong indicator of report tampering.',
            'severity': 'CRITICAL',
        })

    # Determine risk level
    critical_flags = sum(1 for f in red_flags if f['severity'] == 'CRITICAL')
    high_flags = sum(1 for f in red_flags if f['severity'] == 'HIGH')
    medium_flags = sum(1 for f in red_flags if f['severity'] == 'MEDIUM')

    if critical_flags >= 1 or consistency_score < 25:
        tampering_risk = 'CRITICAL'
    elif high_flags >= 2 or consistency_score < 40:
        tampering_risk = 'HIGH'
    elif high_flags >= 1 or medium_flags >= 2 or consistency_score < 60:
        tampering_risk = 'MEDIUM'
    else:
        tampering_risk = 'LOW'

    # 7. Build verification summary
    summary_lines = []
    summary_lines.append(f"Analyzed {len(body_conditions)} body condition(s) against forensic report.")
    if evidence_texts:
        summary_lines.append(f"Evidence media analyzed: {len(evidence_texts)} file(s) with OCR text extracted.")
    summary_lines.append(f"Consistency Score: {consistency_score:.0f}%")
    summary_lines.append(f"Tampering Risk: {tampering_risk}")
    summary_lines.append(f"")
    summary_lines.append(f"Report's Cause of Death: {report_cod or 'Not stated'}")
    summary_lines.append(f"AI-Determined Cause of Death: {ai_cod}")
    summary_lines.append(f"AI Confidence: {ai_result['confidence']}%")
    summary_lines.append(f"COD Match: {'✅ Yes' if cod_match else '❌ No'}")
    summary_lines.append(f"")
    summary_lines.append(f"Matches: {len(matches)} | Missing from report: {len(missing_from_report)} | Suspicious: {len(suspicious)}")
    if red_flags:
        summary_lines.append(f"Red Flags: {len(red_flags)}")
        for rf in red_flags:
            summary_lines.append(f"  🚨 [{rf['severity']}] {rf['message']}")

    if analysis['assault_indicators']:
        summary_lines.append(f"")
        summary_lines.append(f"⚠️ Assault Indicators Detected: {len(analysis['assault_indicators'])}")
        for ai_ind in analysis['assault_indicators']:
            summary_lines.append(f"  • {ai_ind['indicator']}")

    return {
        'consistency_score': round(consistency_score, 1),
        'tampering_risk': tampering_risk,
        'ai_cause_of_death': ai_cod,
        'ai_confidence': ai_result['confidence'],
        'ai_reasoning': ai_result['reasoning'],
        'cod_match': cod_match,
        'cod_note': cod_note,
        'report_cod': report_cod,
        'matches': matches,
        'missing_from_report': missing_from_report,
        'suspicious': suspicious,
        'extra_in_report': extra_in_report,
        'red_flags': red_flags,
        'assault_indicators': analysis['assault_indicators'],
        'accident_indicators': analysis['accident_indicators'],
        'injury_analysis': analysis,
        'summary': '\n'.join(summary_lines),
        'evidence_texts_count': len(evidence_texts or []),
    }



def extract_injuries_from_report_text(text):
    """
    Extract injury mentions from the report text using keyword matching.
    This gives us a list of what the REPORT says about injuries.

    Returns:
        list of injury description strings found in the report
    """
    import re

    if not text:
        return []

    injuries_found = []
    text_lower = text.lower()

    # Patterns to find injury mentions
    injury_patterns = [
        r'(?:injury|injuries)[\s:]+([^\n.]{10,80})',
        r'(?:fracture|fractured)[\s:]*(?:of\s+)?([^\n.]{5,60})',
        r'(?:wound|wounds)[\s:]+([^\n.]{10,80})',
        r'(?:laceration|lacerations)[\s:]*(?:on\s+|of\s+)?([^\n.]{5,60})',
        r'(?:bleeding|hemorrhage)[\s:]*(?:from\s+|in\s+|of\s+)?([^\n.]{5,60})',
        r'(?:bruise|bruises|contusion|contusions)[\s:]*(?:on\s+|of\s+)?([^\n.]{5,60})',
        r'(?:abrasion|abrasions)[\s:]*(?:on\s+|of\s+)?([^\n.]{5,60})',
        r'(?:burn|burns)[\s:]*(?:on\s+|of\s+)?([^\n.]{5,60})',
        r'(?:swelling|edema)[\s:]*(?:on\s+|of\s+|in\s+)?([^\n.]{5,60})',
        r'(?:cut|cuts)[\s:]+([^\n.]{5,60})',
        r'(?:stab wound|stab wounds)[\s:]*([^\n.]{5,60})',
        r'(?:crush|crushed)[\s:]*([^\n.]{5,60})',
    ]

    # Section-based extraction
    injury_section = re.search(
        r'(?:injury\s*list|injuries\s*(?:found|observed|noted)|external\s*examination|'
        r'injuries\s*on\s*body|physical\s*examination)[\s:]*\n((?:.*\n){1,20})',
        text, re.I
    )
    if injury_section:
        section_text = injury_section.group(1)
        lines = section_text.strip().split('\n')
        for line in lines:
            line = line.strip(' -•*')
            if len(line) > 5:
                injuries_found.append(line)

    # Pattern-based extraction
    for pattern in injury_patterns:
        matches = re.finditer(pattern, text, re.I)
        for match in matches:
            injury_text = match.group(0).strip()
            if len(injury_text) > 5 and injury_text not in injuries_found:
                injuries_found.append(injury_text)

    # Deduplicate
    seen = set()
    unique = []
    for inj in injuries_found:
        inj_clean = inj.strip()
        if inj_clean.lower() not in seen and len(inj_clean) > 3:
            seen.add(inj_clean.lower())
            unique.append(inj_clean)

    return unique[:20]  # Cap at 20
