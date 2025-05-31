from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def triplet_to_text(triplet: dict) -> str:
    return f"{triplet['subject']} {triplet['predicate']} {triplet['object']}"
