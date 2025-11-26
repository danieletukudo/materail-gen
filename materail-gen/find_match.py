import json
import re

def tokenize(text):
    if not text:
        return set()
    # Simple tokenization: lowercase, remove punctuation, split by whitespace
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return set(text.split())

def jaccard_similarity(set1, set2):
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union == 0:
        return 0
    return intersection / union

def find_best_match(query_text, json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    query_tokens = tokenize(query_text)
    if not query_tokens:
        print("Query text has no tokens.")
        return

    scores = []
    
    for i, item in enumerate(data):
        # Combine main summary and sub-material summaries
        full_text = str(item.get('resumen') or "")
        
        if item.get('sub_materials'):
            for sub in item['sub_materials']:
                if sub.get('resumen'):
                    full_text += " " + str(sub['resumen'])
        
        if full_text.strip():
            doc_tokens = tokenize(full_text)
            score = jaccard_similarity(query_tokens, doc_tokens)
            if score > 0:
                scores.append((score, item))
    
    # Sort by score descending
    scores.sort(key=lambda x: x[0], reverse=True)
    
    # Get top 5 matches
    top_k = 5
    print(f"Top {top_k} matches for query (searching main + sub-materials):\n'{query_text[:100]}...'\n")
    
    for rank, (score, item) in enumerate(scores[:top_k]):
        print(f"#{rank+1} (Score: {score:.4f})")
        print(f"Code: {item.get('codigo')}")
        print(f"Description: {item.get('resumen')}")
        
        if rank == 0 and item.get('sub_materials'):
             print("Sub-materials:")
             for sub in item['sub_materials']:
                 if sub.get('resumen'):
                    print(f"  - {sub['resumen'][:100]}...")
        print("-" * 40)

if __name__ == "__main__":
    query = """Repicado del revoco de mortero y pintura existente en en su totalidad  hasta llegar al soporte cerámico en buen estado limpio y sin residuos. Incluye retirada a vertedero de reciclaje y pago de cánon.

Fisuras en vierteaguas: 60.58 * 0.85 = 51.49"""
    
    json_file = "/Users/danielsamuel/PycharmProjects/RAG/materail-gen/DATABSE_parsed.json"
    find_best_match(query, json_file)
