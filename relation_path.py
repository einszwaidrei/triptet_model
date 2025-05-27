from sentence_transformers import SentenceTransformer, util
from neo4j import GraphDatabase

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


def triplet_text(t):
    return f"{t['subject']} {t['predicate']} {t['object']}"


def find_closest_node(input_name, uri, user, password):
    query_emb = model.encode(input_name, convert_to_tensor=True)
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        cypher = "MATCH (e:Entity) RETURN DISTINCT e.name AS name"
        result = session.run(cypher)
        all_names = [record["name"] for record in result]

    if not all_names:
        return None

    embeddings = model.encode(all_names, convert_to_tensor=True)
    sims = util.cos_sim(query_emb, embeddings)[0]
    best_idx = sims.argmax().item()
    best_score = sims[best_idx].item()

    return all_names[best_idx] if best_score > 0.75 else None


def find_paths_between_entities(name1, name2, uri="bolt://localhost:7687", user="admin", password="admin123"):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        cypher = """
        MATCH path = shortestPath((a:Entity {name: $name1})-[*..6]-(b:Entity {name: $name2}))
        RETURN path
        """
        result = session.run(cypher, name1=name1, name2=name2)
        paths = [record["path"] for record in result]

    if not paths:
        print("Связей между объектами не найдено.")
        return

    for idx, path in enumerate(paths, 1):
        nodes = path.nodes
        rels = path.relationships
        steps = []
        for i in range(len(rels)):
            subj = nodes[i].get("name")
            pred = type(rels[i]).__name__ if hasattr(rels[i], "__name__") else rels[i].type
            obj = nodes[i+1].get("name")
            desc = rels[i].get("description", "")
            steps.append(f"{subj} —[{pred}]→ {obj} {'| ' + desc if desc else ''}")
        path_str = "\n".join(steps)
        print(f"\n[{idx}]\n{path_str}")



def query_relation_path():
    name1 = input("Введите первый объект: ").strip()
    name2 = input("Введите второй объект: ").strip()
    uri = "bolt://localhost:7687"
    user = "admin"
    password = "admin123"

    print("\n🔎 Поиск ближайших узлов по смыслу")
    node1 = find_closest_node(name1, uri, user, password)
    node2 = find_closest_node(name2, uri, user, password)

    if not node1 or not node2:
        print("Один или оба объекта не найдены по смыслу в графе.")
        return

    print(f"Найдены: '{node1}' и '{node2}' — поиск путей между ними")
    find_paths_between_entities(node1, node2, uri, user, password)