"""
Injury Analysis Engine — Rule-based Medical Logic
Maps injuries → probable causes of death using forensic medical knowledge.
Assigns severity scores and determines independent cause-of-death.
"""

# ============================================================
# INJURY SEVERITY SCORES (1-10)
# ============================================================
SEVERITY_MAP = {
    'minor': 2,
    'moderate': 5,
    'severe': 8,
    'critical': 10,
    'fatal': 10,
}

# ============================================================
# INJURY TYPE → PROBABLE CAUSE OF DEATH MAPPING
# Medical knowledge rules
# ============================================================
INJURY_CAUSE_RULES = {
    # Head / Brain injuries
    'skull_fracture': {
        'probable_causes': ['Traumatic brain injury', 'Blunt force head trauma'],
        'severity_weight': 9,
        'body_parts': ['head', 'skull', 'cranium', 'temple', 'forehead'],
        'keywords': ['skull fracture', 'cranial fracture', 'skull crack', 'depressed fracture'],
        'assault_indicators': ['depressed fracture', 'multiple impact points', 'occipital trauma'],
        'accident_indicators': ['linear fracture', 'single impact', 'frontal injury'],
    },
    'cerebral_hemorrhage': {
        'probable_causes': ['Intracranial hemorrhage', 'Traumatic brain injury'],
        'severity_weight': 10,
        'body_parts': ['brain', 'head', 'skull'],
        'keywords': ['cerebral hemorrhage', 'brain hemorrhage', 'intracranial bleeding',
                     'subdural hematoma', 'epidural hematoma', 'subarachnoid hemorrhage'],
        'assault_indicators': ['subdural hematoma', 'multiple hemorrhage sites'],
        'accident_indicators': ['epidural hematoma', 'single hemorrhage site'],
    },
    'concussion': {
        'probable_causes': ['Traumatic brain injury'],
        'severity_weight': 5,
        'body_parts': ['head', 'brain'],
        'keywords': ['concussion', 'loss of consciousness', 'unconscious'],
    },

    # Neck injuries
    'neck_fracture': {
        'probable_causes': ['Cervical spine injury', 'Neck trauma'],
        'severity_weight': 10,
        'body_parts': ['neck', 'cervical', 'spine'],
        'keywords': ['neck fracture', 'cervical fracture', 'broken neck', 'spinal fracture',
                     'cervical spine injury', 'neck broken'],
        'assault_indicators': ['ligature marks', 'compression marks', 'strangulation marks',
                              'manual compression'],
        'accident_indicators': ['hyperextension', 'whiplash', 'deceleration injury'],
    },
    'strangulation': {
        'probable_causes': ['Asphyxia due to strangulation', 'Homicidal strangulation'],
        'severity_weight': 10,
        'body_parts': ['neck', 'throat'],
        'keywords': ['strangulation', 'ligature marks', 'compression marks', 'throttling',
                     'hanging marks', 'rope marks', 'petechial hemorrhage in eyes'],
        'assault_indicators': ['ligature marks', 'fingerprint bruises on neck',
                              'hyoid bone fracture', 'petechial hemorrhage'],
    },

    # Chest / Torso injuries
    'rib_fracture': {
        'probable_causes': ['Blunt force trauma to chest', 'Chest trauma'],
        'severity_weight': 7,
        'body_parts': ['chest', 'ribs', 'thorax', 'torso'],
        'keywords': ['rib fracture', 'broken ribs', 'fractured ribs', 'chest fracture',
                     'flail chest'],
        'assault_indicators': ['multiple rib fractures', 'bilateral fractures', 'posterior fractures'],
        'accident_indicators': ['unilateral fracture', 'steering wheel injury'],
    },
    'internal_bleeding': {
        'probable_causes': ['Internal hemorrhage', 'Hemorrhagic shock'],
        'severity_weight': 9,
        'body_parts': ['abdomen', 'chest', 'torso', 'internal'],
        'keywords': ['internal bleeding', 'internal hemorrhage', 'hemoperitoneum',
                     'hemothorax', 'splenic rupture', 'liver laceration',
                     'organ rupture', 'internal organ damage'],
        'assault_indicators': ['splenic rupture without seat belt', 'liver laceration with blunt object'],
        'accident_indicators': ['splenic rupture with seat belt', 'deceleration injury'],
    },
    'organ_damage': {
        'probable_causes': ['Multiple organ failure', 'Organ trauma'],
        'severity_weight': 9,
        'body_parts': ['liver', 'spleen', 'kidney', 'lung', 'heart', 'abdomen'],
        'keywords': ['organ damage', 'organ rupture', 'organ failure', 'organ laceration',
                     'liver damage', 'spleen damage', 'kidney damage', 'lung collapse',
                     'pneumothorax', 'cardiac tamponade'],
    },

    # Limb injuries
    'limb_fracture': {
        'probable_causes': ['Skeletal trauma', 'Multiple fractures with shock'],
        'severity_weight': 5,
        'body_parts': ['arm', 'leg', 'femur', 'tibia', 'fibula', 'humerus',
                      'radius', 'ulna', 'pelvis', 'hip', 'shoulder', 'wrist',
                      'ankle', 'knee', 'elbow', 'hand', 'foot'],
        'keywords': ['fracture', 'broken bone', 'compound fracture', 'open fracture',
                     'displaced fracture', 'comminuted fracture'],
    },

    # Cuts / Wounds
    'deep_cut': {
        'probable_causes': ['Hemorrhagic shock due to sharp force trauma', 'Exsanguination'],
        'severity_weight': 8,
        'body_parts': ['any'],
        'keywords': ['deep cut', 'laceration', 'stab wound', 'incised wound',
                     'slash wound', 'sharp force injury', 'knife wound',
                     'penetrating wound'],
        'assault_indicators': ['multiple stab wounds', 'defensive wounds on hands',
                              'deep penetrating wound', 'stab wound to chest/abdomen'],
        'accident_indicators': ['glass laceration', 'metal shard wound'],
    },
    'superficial_wound': {
        'probable_causes': ['Surface trauma'],
        'severity_weight': 2,
        'body_parts': ['any'],
        'keywords': ['abrasion', 'scrape', 'scratch', 'superficial cut', 'graze',
                     'brush burn', 'road rash'],
    },

    # Burns
    'burn_injury': {
        'probable_causes': ['Burn injury', 'Smoke inhalation', 'Thermal injury'],
        'severity_weight': 8,
        'body_parts': ['any'],
        'keywords': ['burn', 'thermal injury', 'chemical burn', 'electrical burn',
                     'scald', 'charring', 'incineration'],
        'assault_indicators': ['pour pattern', 'splash pattern', 'chemical burn on specific area',
                              'cigarette burns'],
        'accident_indicators': ['uniform burn pattern', 'kitchen burn', 'electrical burn'],
    },

    # Bleeding
    'excessive_bleeding': {
        'probable_causes': ['Hemorrhagic shock', 'Exsanguination'],
        'severity_weight': 9,
        'body_parts': ['any'],
        'keywords': ['excessive bleeding', 'massive blood loss', 'hemorrhage',
                     'exsanguination', 'blood loss', 'arterial bleeding',
                     'uncontrolled bleeding'],
    },

    # Drowning
    'drowning_signs': {
        'probable_causes': ['Drowning', 'Asphyxia due to drowning'],
        'severity_weight': 10,
        'body_parts': ['lungs', 'chest', 'airway'],
        'keywords': ['drowning', 'froth at mouth', 'waterlogged lungs',
                     'pulmonary edema', 'diatoms', 'wet lungs'],
        'assault_indicators': ['injuries inconsistent with drowning', 'ligature marks + drowning',
                              'bruises before drowning'],
    },

    # Poisoning
    'poisoning_signs': {
        'probable_causes': ['Poisoning', 'Toxic substance ingestion'],
        'severity_weight': 10,
        'body_parts': ['internal', 'stomach', 'blood'],
        'keywords': ['poisoning', 'toxicology positive', 'poison', 'drug overdose',
                     'cyanide', 'organophosphate', 'arsenic', 'chemical ingestion',
                     'froth at mouth with odor'],
        'assault_indicators': ['forced ingestion', 'no suicide note', 'no history of substance use'],
    },

    # Bruising / Contusion
    'bruising': {
        'probable_causes': ['Blunt force trauma'],
        'severity_weight': 4,
        'body_parts': ['any'],
        'keywords': ['bruise', 'contusion', 'ecchymosis', 'hematoma',
                     'discoloration', 'swelling'],
        'assault_indicators': ['patterned bruising', 'grip marks', 'defense injuries',
                              'multiple ages of bruising', 'bruising on both arms'],
    },

    # Crush injuries
    'crush_injury': {
        'probable_causes': ['Crush injury syndrome', 'Traumatic asphyxia'],
        'severity_weight': 9,
        'body_parts': ['chest', 'abdomen', 'pelvis', 'any'],
        'keywords': ['crush injury', 'crushed', 'compression injury',
                     'run over', 'trampled', 'vehicle rollover'],
    },
}

# ============================================================
# RED FLAG PATTERNS — Indicate possible foul play / tampering
# ============================================================
RED_FLAG_PATTERNS = [
    {
        'name': 'Natural death with trauma',
        'condition': lambda report_cod, injuries: (
            report_cod and
            any(w in report_cod.lower() for w in ['natural', 'cardiac', 'heart attack', 'heart failure']) and
            any(i.get('severity', '').lower() in ['severe', 'critical', 'fatal'] for i in injuries)
        ),
        'message': 'Report claims natural death, but severe traumatic injuries observed on body.',
        'severity': 'CRITICAL',
    },
    {
        'name': 'Accident with assault patterns',
        'condition': lambda report_cod, injuries: (
            report_cod and
            'accident' in report_cod.lower() and
            any(
                i.get('injury_type', '').lower() in ['strangulation', 'stab wound', 'multiple stab wounds',
                                                      'ligature marks', 'defensive wounds']
                for i in injuries
            )
        ),
        'message': 'Report claims accident, but injury patterns indicate possible assault.',
        'severity': 'CRITICAL',
    },
    {
        'name': 'Missing critical injuries',
        'condition': lambda report_cod, injuries: False,  # Will be checked separately
        'message': 'Critical injuries observed at scene but not mentioned in the forensic report.',
        'severity': 'HIGH',
    },
    {
        'name': 'COD mismatch with injuries',
        'condition': lambda report_cod, injuries: False,  # Checked by cross-verifier
        'message': 'Stated cause of death does not match the observed injury pattern.',
        'severity': 'HIGH',
    },
    {
        'name': 'Suicide claim with defensive wounds',
        'condition': lambda report_cod, injuries: (
            report_cod and
            any(w in report_cod.lower() for w in ['suicide', 'self-inflicted', 'self harm']) and
            any(
                any(kw in i.get('description', '').lower() for kw in ['defensive wound', 'defense wound',
                                                                       'defensive injuries'])
                for i in injuries
            )
        ),
        'message': 'Report claims suicide, but defensive wounds found on body — indicating possible homicide.',
        'severity': 'CRITICAL',
    },
    {
        'name': 'Single impact accident with multiple injury sites',
        'condition': lambda report_cod, injuries: (
            report_cod and
            'accident' in report_cod.lower() and
            len(set(i.get('body_part', '').lower() for i in injuries if i.get('severity', '').lower() in ['severe', 'critical'])) >= 4
        ),
        'message': 'Single accident claimed, but severe injuries found on 4+ different body parts — unusual for single-impact accident.',
        'severity': 'HIGH',
    },
]


def analyze_injuries(injuries):
    """
    Analyze a list of body condition injuries and determine:
    - Matched injury rules
    - Probable causes of death
    - Overall severity assessment
    - Assault vs accident indicators

    Args:
        injuries: list of dicts with keys: injury_type, body_part, severity, description

    Returns:
        dict with analysis results
    """
    if not injuries:
        return {
            'matched_rules': [],
            'probable_causes': [],
            'severity_score': 0,
            'assault_indicators': [],
            'accident_indicators': [],
            'overall_assessment': 'No injuries reported',
        }

    matched_rules = []
    probable_causes = set()
    total_severity = 0
    assault_indicators = []
    accident_indicators = []
    max_severity = 0

    for injury in injuries:
        inj_type = (injury.get('injury_type') or '').lower()
        body_part = (injury.get('body_part') or '').lower()
        severity = (injury.get('severity') or 'moderate').lower()
        description = (injury.get('description') or '').lower()
        combined_text = f"{inj_type} {body_part} {description}"

        severity_score = SEVERITY_MAP.get(severity, 5)

        for rule_key, rule in INJURY_CAUSE_RULES.items():
            # Check if any keyword matches
            keyword_match = any(kw in combined_text for kw in rule['keywords'])
            # Check if body part matches
            body_match = ('any' in rule['body_parts'] or
                         any(bp in body_part for bp in rule['body_parts']) or
                         any(bp in combined_text for bp in rule['body_parts']))

            if keyword_match or (body_match and severity_score >= 5):
                effective_severity = min(10, (severity_score + rule['severity_weight']) / 2)
                matched_rules.append({
                    'rule': rule_key,
                    'injury': injury,
                    'probable_causes': rule['probable_causes'],
                    'severity': effective_severity,
                })
                for cause in rule['probable_causes']:
                    probable_causes.add(cause)

                total_severity += effective_severity
                if effective_severity > max_severity:
                    max_severity = effective_severity

                # Check assault indicators
                if 'assault_indicators' in rule:
                    for ai in rule['assault_indicators']:
                        if ai.lower() in combined_text:
                            assault_indicators.append({
                                'indicator': ai,
                                'injury': injury.get('description', inj_type),
                                'rule': rule_key,
                            })

                # Check accident indicators
                if 'accident_indicators' in rule:
                    for ai in rule['accident_indicators']:
                        if ai.lower() in combined_text:
                            accident_indicators.append({
                                'indicator': ai,
                                'injury': injury.get('description', inj_type),
                                'rule': rule_key,
                            })

    # Determine overall assessment
    avg_severity = total_severity / max(len(matched_rules), 1)
    if max_severity >= 9:
        overall = 'FATAL — Injuries are life-threatening and likely cause of death'
    elif max_severity >= 7:
        overall = 'CRITICAL — Severe injuries that could be fatal without immediate treatment'
    elif max_severity >= 5:
        overall = 'SERIOUS — Significant injuries requiring hospitalization'
    elif max_severity >= 3:
        overall = 'MODERATE — Injuries requiring medical attention'
    else:
        overall = 'MINOR — Superficial injuries'

    return {
        'matched_rules': matched_rules,
        'probable_causes': list(probable_causes),
        'severity_score': round(avg_severity, 1),
        'max_severity': max_severity,
        'assault_indicators': assault_indicators,
        'accident_indicators': accident_indicators,
        'overall_assessment': overall,
    }


def determine_ai_cause_of_death(injuries, report_info=None):
    """
    Independently determine the most likely cause of death based on injuries.

    Args:
        injuries: list of injury dicts
        report_info: dict of extracted report info (optional, for context)

    Returns:
        dict with ai_cause, confidence, reasoning
    """
    analysis = analyze_injuries(injuries)

    if not analysis['probable_causes']:
        return {
            'ai_cause': 'Insufficient injury data to determine cause',
            'confidence': 0,
            'reasoning': ['No significant injuries reported or matched.'],
            'analysis': analysis,
        }

    # Score each probable cause
    cause_scores = {}
    for rule_match in analysis['matched_rules']:
        for cause in rule_match['probable_causes']:
            if cause not in cause_scores:
                cause_scores[cause] = {'score': 0, 'evidence': []}
            cause_scores[cause]['score'] += rule_match['severity']
            inj = rule_match['injury']
            evidence = f"{inj.get('injury_type', 'Unknown')} on {inj.get('body_part', 'unknown')} ({inj.get('severity', 'unknown')} severity)"
            cause_scores[cause]['evidence'].append(evidence)

    # Sort by score
    sorted_causes = sorted(cause_scores.items(), key=lambda x: x[1]['score'], reverse=True)
    top_cause = sorted_causes[0]
    top_score = top_cause[1]['score']

    # Confidence based on evidence strength
    max_possible = analysis['max_severity'] * len(analysis['matched_rules'])
    confidence = min(95, int((top_score / max(max_possible, 1)) * 100))

    # Build reasoning
    reasoning = []
    reasoning.append(f"Primary determination: {top_cause[0]}")
    reasoning.append(f"Based on {len(top_cause[1]['evidence'])} injury findings:")
    for ev in top_cause[1]['evidence']:
        reasoning.append(f"  • {ev}")

    if analysis['assault_indicators']:
        reasoning.append(f"⚠️ {len(analysis['assault_indicators'])} assault indicator(s) detected")
        for ai in analysis['assault_indicators']:
            reasoning.append(f"  • {ai['indicator']} — from: {ai['injury']}")

    if analysis['accident_indicators']:
        reasoning.append(f"Accident indicator(s): {len(analysis['accident_indicators'])}")

    # Additional causes
    if len(sorted_causes) > 1:
        reasoning.append("Other possible causes:")
        for cause, data in sorted_causes[1:3]:
            reasoning.append(f"  • {cause} (evidence score: {data['score']:.0f})")

    return {
        'ai_cause': top_cause[0],
        'confidence': confidence,
        'reasoning': reasoning,
        'analysis': analysis,
        'all_causes': sorted_causes,
    }


def detect_red_flags(report_cod, injuries):
    """
    Detect red flags that suggest possible tampering or foul play.

    Args:
        report_cod: str — cause of death stated in the report
        injuries: list of injury dicts from body condition form

    Returns:
        list of red flag dicts
    """
    flags = []
    for pattern in RED_FLAG_PATTERNS:
        try:
            if pattern['condition'](report_cod, injuries):
                flags.append({
                    'name': pattern['name'],
                    'message': pattern['message'],
                    'severity': pattern['severity'],
                })
        except Exception:
            continue

    return flags
