from buffer import save_to_buffer
from sentence_transformers import SentenceTransformer, util
from neo4j import GraphDatabase
from datetime import datetime

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def triplet_to_text(t):
    return f"{t['subject']} {t['predicate']} {t['object']}"

def find_similar_triplets(triplet, uri, user, password, threshold=0.8, top_k=5):
    query_text = triplet_to_text(triplet)
    query_emb = model.encode(query_text, convert_to_tensor=True)

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

    return sorted(results, key=lambda x: -x[1])[:top_k]

def process_manual_triplet(triplet, uri="bolt://localhost:7687", user="admin", password="admin123"):
    triplet = triplet.copy()
    triplet["date_added"] = datetime.utcnow().isoformat()

    print("\n Ищем похожие триплеты в графе...")
    similar = find_similar_triplets(triplet, uri, user, password)

    if not similar:
        print("Похожих триплетов не найдено. Сохраняем в буфер по умолчанию.")
        save_to_buffer(triplet)
        return

    print("\n  Найдены похожие триплеты:")
    for idx, (sim_tr, score) in enumerate(similar, 1):
        print(f"[{idx}] ({score:.2f}) {sim_tr['subject']} —[{sim_tr['predicate']}]-> {sim_tr['object']} | {sim_tr.get('description', '')}")

    print("\nВыберите действие:")
    print("[a] Добавить новый триплет в буфер")
    print("[u] Обновить существующий (заменить один из найденных)")
    print("[d] Удалить один или несколько найденных")
    print("[n] Ничего не делать")

    choice = input("Введите команду (a/u/d/n): ").strip().lower()

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        if choice == "a":
            save_to_buffer(triplet)
            print(" Триплет добавлен в буфер.")

        elif choice == "u":
            idx = int(input("Введите номер триплета для замены: ")) - 1
            if 0 <= idx < len(similar):
                old = similar[idx][0]
                session.run("""
                    MATCH (s:Entity {name: $subject})-[r:`""" + old["predicate"] + """`]->(o:Entity {name: $object})
                    DELETE r
                """, subject=old["subject"], object=old["object"])
                save_to_buffer(triplet)
                print(" Старый триплет удалён. Новый сохранён в буфер.")

        elif choice == "d":
            ids = input("Введите номера для удаления через пробел: ").strip().split()
            for idx in ids:
                i = int(idx) - 1
                if 0 <= i < len(similar):
                    t = similar[i][0]
                    session.run("""
                        MATCH (s:Entity {name: $subject})-[r:`""" + t["predicate"] + """`]->(o:Entity {name: $object})
                        DELETE r
                    """, subject=t["subject"], object=t["object"])
            print("Указанные триплеты удалены.")

        elif choice == "n":
            print("Действие отменено.")
