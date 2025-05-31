import re
import pymorphy2
morph = pymorphy2.MorphAnalyzer()

def validate_and_clean_triplets(triplets):
    valid = []
    for t in triplets:
        if not isinstance(t, dict):
            continue
        try:
            s = str(t['subject']).strip()
            p = str(t['predicate']).strip()
            o = str(t['object']).strip()
            d = str(t.get('description', '')).strip()
        except KeyError:
            continue
        if any(isinstance(x, list) for x in [s, p, o]):
            continue
        if not (s and p and o): 
            continue
        valid.append({
            "subject": s,
            "predicate": p,
            "object": o,
            "description": d
        })
    if not valid:
        return 'Заглушка'
    return valid


def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r'["\'\[\]{}()\\/.!?–—-]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_triplets(triplets):
    return [{
        'subject': clean_text(t['subject']),
        'predicate': clean_text(t['predicate']),
        'object': clean_text(t['object']),
        'description': clean_text(t.get('description', ''))
    } for t in triplets]

def move_verb_and_adjective(triplets):
    updated = []

    for t in triplets:
        t = t.copy()
        object_words = t['object'].split()
        predicate_words = t['predicate'].split()

        verb_part = []
        object_clean = []
        noun_found = False

        for word in object_words:
            parsed = morph.parse(word)[0]
            if not noun_found:
                if 'VERB' in parsed.tag or 'INFN' in parsed.tag:
                    verb_part.append(word)
                elif 'NOUN' in parsed.tag:
                    noun_found = True
                    object_clean.append(word)
                else:
                    verb_part.append(word)
            else:
                object_clean.append(word)

        if verb_part:
            t['predicate'] = f"{t['predicate']} {' '.join(verb_part)}".strip()
            t['object'] = " ".join(object_clean).strip()

        if predicate_words:
            last_word = predicate_words[-1]
            parsed = morph.parse(last_word)[0]
            if 'ADJF' in parsed.tag and len(predicate_words) > 1:
                predicate_words = predicate_words[:-1]
                t['predicate'] = " ".join(predicate_words).strip()
                t['object'] = f"{last_word} {t['object']}".strip()

        updated.append(t)

    return updated

def move_preposition_to_predicate(triplets):
    prepositions = {"в", "на", "по", "о", "об", "от", "с", "у", "к", "из", "за", "без", "для", "при", "через", "над", "под", "со"}
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
                inflected = parsed.inflect({'nomn'})
                result.append(inflected.word if inflected else word)
            elif 'NOUN' in parsed.tag:
                noun_found = True
                inflected = parsed.inflect({'nomn'})
                result.append(inflected.word if inflected else word)
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
