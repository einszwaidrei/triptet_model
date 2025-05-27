from pipeline.graph_preprocessing import normalize_triplets, filter_triplets, filter_triplets_by_component_size
from pipeline.neo4j_loader import insert_triplets_to_neo4j
from buffer import load_buffered_triplets, clear_buffer
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
import pytz

from neo4j import GraphDatabase

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


def triplet_to_text(t):
    return f"{t['subject']} {t['predicate']} {t['object']}"


def find_similar_in_graph(triplet, uri, user, password, threshold=0.85):
    text_query = triplet_to_text(triplet)
    query_emb = model.encode(text_query, convert_to_tensor=True)

    driver = GraphDatabase.driver(uri, auth=(user, password))
    results = []

    with driver.session() as session:
        cypher = """
        MATCH (s:Entity)-[r]->(o:Entity)
        RETURN s.name AS subject, type(r) AS predicate, o.name AS object, r.description AS description, r.date_added AS date_added
        """
        records = session.run(cypher)
        all_triplets = [dict(record) for record in records]

    texts = [triplet_to_text(t) for t in all_triplets]
    embeddings = model.encode(texts, convert_to_tensor=True)

    sims = util.cos_sim(query_emb, embeddings)[0]

    for i, sim in enumerate(sims):
        if sim >= threshold:
            results.append((all_triplets[i], sim.item()))

    return sorted(results, key=lambda x: -x[1])


def update_graph_with_buffer(uri="bolt://localhost:7687", user="admin", password="admin123"):
    buffer = load_buffered_triplets()
    if not buffer:
        print("Буфер пуст — обновление не требуется.")
        return

    print(f"Загружено {len(buffer)} триплетов из буфера. Выполняется фильтрация и обновление...")

    triplets = normalize_triplets(buffer, threshold=0.75)
    triplets_df = filter_triplets(triplets, theme_query="информационная безопасность", theme_threshold=0.4)
    triplets_filtered = filter_triplets_by_component_size(triplets_df.to_dict(orient="records"), min_nodes=8)

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        for triplet in triplets_filtered:
            similar = find_similar_in_graph(triplet, uri, user, password, threshold=0.85)
            for old_triplet, sim in similar:
                old_date = old_triplet.get("date_added")
                new_date = triplet.get("date_added") or datetime.utcnow().isoformat()
                if old_date and old_date < new_date:
                    session.run("""
                        MATCH (s:Entity {name: $subject})-[r:`""" + old_triplet["predicate"] + """`]->(o:Entity {name: $object})
                        DELETE r
                    """, subject=old_triplet["subject"], object=old_triplet["object"])

    insert_triplets_to_neo4j(triplets_filtered, uri=uri, user=user, password=password)
    clear_buffer()
    print(f"Граф обновлён. Загружено {len(triplets_filtered)} триплетов.")
