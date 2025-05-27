from neo4j import GraphDatabase

def insert_triplets_to_neo4j(triplets, uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        for triplet in triplets:
            subject = str(triplet['subject']).strip()
            predicate = str(triplet['predicate']).strip()
            object_ = str(triplet['object']).strip()
            description = str(triplet.get('description', '')).strip()

            if not subject or not predicate or not object_:
                continue
            if subject == object_:
                continue

            query = """
            MERGE (s:Entity {name: $subject})
            MERGE (o:Entity {name: $object})
            MERGE (s)-[r:`%s`]->(o)
            SET r.description = $description
            """ % predicate

            session.run(query, subject=subject, object=object_, description=description)
    driver.close()

