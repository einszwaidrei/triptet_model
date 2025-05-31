from sentence_transformers import SentenceTransformer, util
from neo4j import GraphDatabase

from graph_builder.embeddings_utils import embedding_model, triplet_to_text

def find_most_similar_triplets(user_triplet, uri="bolt://localhost:7687", user="admin", password="admin123", top_k=5):
    query_text = triplet_to_text(user_triplet)
    query_emb = embedding_model.encode(query_text, convert_to_tensor=True)

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        cypher = """
        MATCH (s:Entity)-[r]->(o:Entity)
        RETURN s.name AS subject, type(r) AS predicate, o.name AS object, r.description AS description
        """
        result = session.run(cypher)
        all_triplets = [dict(record) for record in result]

    if not all_triplets:
        print(" В графе пока нет триплетов.")
        return

    texts = [triplet_to_text(t) for t in all_triplets]
    embeddings = embedding_model.encode(texts, convert_to_tensor=True)
    sims = util.cos_sim(query_emb, embeddings)[0]

    scored = [(all_triplets[i], sims[i].item()) for i in range(len(sims))]
    top_matches = sorted(scored, key=lambda x: -x[1])[:top_k]

    print("\n Топ похожих триплетов:")
    for idx, (tr, score) in enumerate(top_matches, 1):
        print(f"[{idx}] ({score:.2f}) {tr['subject']} —[{tr['predicate']}]-> {tr['object']} | {tr.get('description', '')}")

def query_similar_triplet():
    subj = input("Введите субъект: ").strip()
    pred = input("Введите предикат: ").strip()
    obj = input("Введите объект: ").strip()
    user_triplet = {"subject": subj, "predicate": pred, "object": obj}
    find_most_similar_triplets(user_triplet)
