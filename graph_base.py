pip install neo4j

from neo4j import GraphDatabase

import pandas as pd

file_path = 'handTripleting.xlsx' 
df = pd.read_excel(file_path)

df = df[required_columns].fillna("")

triplets = df.to_dict(orient='records')

uri = "bolt://localhost:7687"  # Адрес Neo4j сервера
username = "admin"  # Ваше имя пользователя Neo4j
password = "admin123"  # Ваш пароль

driver = GraphDatabase.driver(uri, auth=(username, password))

def insert_triplets_to_neo4j__with_desc(triplets):
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



insert_triplets_to_neo4j__with_desc(triplets)

driver.close()
