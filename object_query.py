from sentence_transformers import SentenceTransformer, util
from neo4j import GraphDatabase

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


def find_closest_node(input_name, uri, user, password, threshold=0.75):
    query_emb = model.encode(input_name, convert_to_tensor=True)

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        cypher = "MATCH (e:Entity) RETURN DISTINCT e.name AS name"
        result = session.run(cypher)
        all_names = [record["name"] for record in result]

    if not all_names:
        print("Граф пуст или не содержит узлов.")
        return None

    embeddings = model.encode(all_names, convert_to_tensor=True)
    sims = util.cos_sim(query_emb, embeddings)[0]

    best_idx = sims.argmax().item()
    best_score = sims[best_idx].item()

    if best_score < threshold:
        print(f"Нет подходящего узла (макс. похожесть: {best_score:.2f})")
        return None

    best_match = all_names[best_idx]
    print(f"Ближайший по смыслу узел: '{best_match}' (похожесть {best_score:.2f})")
    return best_match


def get_all_relations_of_node(node_name, uri="bolt://localhost:7687", user="admin", password="admin123"):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        cypher = """
        MATCH (s:Entity {name: $name})-[r]->(o:Entity)
        RETURN s.name AS subject, type(r) AS predicate, o.name AS object, r.description AS description
        UNION
        MATCH (s:Entity)-[r]->(o:Entity {name: $name})
        RETURN s.name AS subject, type(r) AS predicate, o.name AS object, r.description AS description
        """
        records = session.run(cypher, name=node_name)
        triples = [dict(record) for record in records]

    if not triples:
        print("Связей не найдено.")
        return

    print(f"\n Найдено {len(triples)} связей:")
    for t in triples:
        print(f"{t['subject']} —[{t['predicate']}]-> {t['object']} | {t.get('description', '')}")


def query_object_relations():
    user_input = input("Введите имя объекта для поиска связей: ").strip()
    node = find_closest_node(user_input, uri="bolt://localhost:7687", user="admin", password="admin123")
    if node:
        get_all_relations_of_node(node)
