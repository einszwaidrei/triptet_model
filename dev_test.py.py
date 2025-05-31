import inspect

if not hasattr(inspect, 'getargspec'):
    from collections import namedtuple
    def getargspec(func):
        argspec = inspect.getfullargspec(func)
        ArgSpec = namedtuple('ArgSpec', 'args varargs keywords defaults')
        return ArgSpec(argspec.args, argspec.varargs, argspec.varkw, argspec.defaults)
    inspect.getargspec = getargspec

from graph_builder.postprocessing import (
    validate_and_clean_triplets,
    clean_triplets,
    move_preposition_to_predicate,
    normalize_triplets_to_nominative,
    move_verb_and_adjective  
)

from graph_builder.graph_preprocessing import (
    normalize_triplets,
    filter_triplets,
    filter_triplets_by_component_size
)
from graph_builder.neo4j_loader import insert_triplets_to_neo4j
from graph_builder.yandex_gpt_integration import get_triplets_from_yandex

def full_graph_builder(text_input):
    raw_triplets = get_triplets_from_yandex(text_input)
    triplets = validate_and_clean_triplets(raw_triplets)
    triplets = clean_triplets(triplets)
    triplets = move_verb_and_adjective(triplets) 
    triplets = move_preposition_to_predicate(triplets)
    triplets = normalize_triplets_to_nominative(triplets)
    return triplets

def graph_pipeline(triplets):
    triplets = normalize_triplets(triplets, threshold=0.75)
    triplets_df = filter_triplets(triplets, theme_query="информационная безопасность", theme_threshold=0.4)
    triplets_filtered = filter_triplets_by_component_size(triplets_df.to_dict(orient="records"), min_nodes=8)
    insert_triplets_to_neo4j(triplets_filtered, uri="bolt://localhost:7687", user="admin", password="admin123")

if __name__ == "__main__":
    text = input("Введите текст: ")
    triplets = full_graph_builder(text)
    print("\n Обработанные триплеты ===")
    for t in triplets:
        print(t)

    graph_pipeline(triplets)
    print("\nГраф успешно построен в Neo4j.")
