import re
import pymorphy2
morph = pymorphy2.MorphAnalyzer()

def validate_and_clean_triplets(triplets):
    valid = []
    for t in triplets:
        if not isinstance(t, dict):
            continue
        try:
            s, p, o = t['subject'], t['predicate'], t['object']
        except KeyError:
            continue
        if not (s and p and o):
            continue
        valid.append({
            "subject": s.strip(),
            "predicate": p.strip(),
            "object": o.strip(),
            "description": t.get("description", "").strip() if t.get("description") else ""
        })

    if not valid:
        valid = 'Заглушка'

    return valid

def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r'[«»"\'\[\]{}()\\/.,;:!?–—-]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_triplets(triplets):
    return [{
        'subject': clean_text(t['subject']),
        'predicate': clean_text(t['predicate']),
        'object': clean_text(t['object']),
        'description': clean_text(t.get('description', ''))
    } for t in triplets]

def move_preposition_to_predicate(triplets):
    prepositions = {"в", "на", "по", "о", "об", "от", "с", "у", "к", "из", "за", "без", "для", "при", "через", "над", "под"}
    updated = []
    for t in triplets:
        words = t['object'].split()
        if words and words[0].lower() in prepositions:
            prep = words[0]
            new_object = " ".join(words[1:]).strip()
            new_predicate = f"{t['predicate']} {prep}".strip()
            t = t.copy()
            t['predicate'] = new_predicate
            t['object'] = new_object
        updated.append(t)
    return updated

def normalize_phrase_to_nominative(text):
    words = text.split()
    result = []
    noun_found = False
    for word in words:
        parsed = morph.parse(word)[0]
        if not noun_found:
            if 'ADJF' in parsed.tag or 'PRTF' in parsed.tag:
                result.append(parsed.inflect({'nomn'}).word)
            elif 'NOUN' in parsed.tag:
                noun_found = True
                result.append(parsed.inflect({'nomn'}).word)
            else:
                result.append(word)
        else:
            result.append(word)
    return ' '.join(result)

def normalize_triplets_to_nominative(triplets):
    normalized = []
    for t in triplets:
        t_norm = t.copy()
        t_norm['subject'] = normalize_phrase_to_nominative(t['subject'])
        t_norm['object'] = normalize_phrase_to_nominative(t['object'])
        normalized.append(t_norm)
    return normalized
