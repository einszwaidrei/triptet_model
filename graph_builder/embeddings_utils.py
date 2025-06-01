from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer('rubert-base-sentence')

def triplet_to_text(triplet: dict) -> str:
    return f"{triplet['subject']} {triplet['predicate']} {triplet['object']}"
