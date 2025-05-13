from sentence_transformers import SentenceTransformer, util
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
import faiss
import umap
import hdbscan
import networkx as nx

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def normalize_triplets(triplets, threshold=0.75):
    all_phrases = [t['subject'] for t in triplets] + [t['object'] for t in triplets]
    unique_phrases = list(set(all_phrases))
    phrase_counts = Counter(all_phrases)
    embeddings = model.encode(unique_phrases, convert_to_tensor=True)

    groups = defaultdict(list)
    used = set()
    for i, phrase in enumerate(unique_phrases):
        if phrase in used:
            continue
        group = [phrase]
        used.add(phrase)
        for j in range(i + 1, len(unique_phrases)):
            if unique_phrases[j] in used:
                continue
            sim = util.cos_sim(embeddings[i], embeddings[j]).item()
            if sim >= threshold:
                group.append(unique_phrases[j])
                used.add(unique_phrases[j])
        most_common = max(group, key=lambda x: phrase_counts[x])
        for item in group:
            groups[item] = most_common

    normalized = []
    for t in triplets:
        norm_subj = groups.get(t['subject'], t['subject'])
        norm_obj = groups.get(t['object'], t['object'])
        normalized.append({
            'subject': norm_subj,
            'predicate': t['predicate'],
            'object': norm_obj,
            'description': t.get('description', '')
        })
    return normalized

def triplet_to_text(tr):
    return f"{tr['subject']} {tr['predicate']} {tr['object']}"

def filter_triplets(triplets, theme_query=None, model_name="paraphrase-multilingual-MiniLM-L12-v2"):
    texts = [triplet_to_text(t) for t in triplets]
    embeddings = model.encode(texts)
    
    if theme_query:
        theme_threshold = 0.5
        query_emb = model.encode(theme_query).reshape(1, -1)
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(np.array(embeddings))
        distances, indices = index.search(query_emb, len(embeddings))
        keep_idx = indices[0][distances[0] < theme_threshold]
        texts = [texts[i] for i in keep_idx]
        embeddings = [embeddings[i] for i in keep_idx]
        triplets = [triplets[i] for i in keep_idx]

    reducer = umap.UMAP(n_neighbors=5, min_dist=0.3, metric='cosine')
    embedding_2d = reducer.fit_transform(embeddings)
    clusterer = hdbscan.HDBSCAN(min_cluster_size=2, metric='euclidean')
    labels = clusterer.fit_predict(embedding_2d)

    df = pd.DataFrame(triplets)
    df["text"] = texts
    df["cluster"] = labels
    df_filtered = df[df["cluster"] != -1].copy()

    return df_filtered.reset_index(drop=True)


def filter_triplets_by_component_size(triplets, min_nodes=8):
    G = nx.Graph()
    for t in triplets:
        G.add_edge(t['subject'], t['object'])

    components = [c for c in nx.connected_components(G) if len(c) >= min_nodes]
    nodes_to_keep = set().union(*components)

    filtered = [
        t for t in triplets
        if t['subject'] in nodes_to_keep and t['object'] in nodes_to_keep
    ]
    return filtered