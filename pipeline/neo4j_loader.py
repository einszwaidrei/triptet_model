from neo4j import GraphDatabase

def insert_triplets_to_neo4j(triplets, uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        for triplet in triplets:
            subject = triplet['subject']
            predicate = triplet['predicate']
            object_ = triplet['object']
            description = triplet.get('description', '')

            query = f"""
            MERGE (s:Entity {{name: $subject}})
            MERGE (o:Entity {{name: $object}})
            MERGE (s)-[r:`{predicate}`]->(o)
            SET r.description = $description
            """

            session.run(query, subject=subject, object=object_, description=description)

    driver.close()
