import json
import re
import sys

class SimpleMaterialMatcher:
    def __init__(self, json_path):
        self.json_path = json_path
        self.data = []
        self._load_data()

    def _load_data(self):
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            # Pre-tokenize all descriptions
            for item in self.data:
                item['tokens'] = self._tokenize(self._construct_full_text(item))
        except Exception as e:
            print(f"Error loading data: {e}")

    def _construct_full_text(self, item):
        parts = []
        if item.get('codigo'): parts.append(str(item['codigo']))
        if item.get('resumen'): parts.append(str(item['resumen']))
        if item.get('sub_materials'):
            for sub in item['sub_materials']:
                if sub.get('codigo'): parts.append(str(sub['codigo']))
                if sub.get('resumen'): parts.append(str(sub['resumen']))
        return " ".join(parts)

    def _tokenize(self, text):
        if not text: return set()
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return set(text.split())

    def find_best_match(self, query_text, top_k=3):
        query_tokens = self._tokenize(query_text)
        if not query_tokens: return []

        results = []
        for item in self.data:
            doc_tokens = item.get('tokens', set())
            if not doc_tokens: continue
            
            intersection = len(query_tokens.intersection(doc_tokens))
            union = len(query_tokens.union(doc_tokens))
            score = intersection / union if union > 0 else 0
            
            if score > 0:
                results.append((score, item))
        
        # Sort descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        return results[:top_k]

if __name__ == "__main__":
    json_file = "/Users/danielsamuel/PycharmProjects/RAG/materail-gen/DATABSE_parsed.json"
    matcher = SimpleMaterialMatcher(json_file)
    
    query = """Saneado a ambos lados de la grieta, eliminando todo el mortero en mal estado y abriendo la grieta 2-3 cm para un mejor rellenado.

Realización de regatas perpendiculares al sentido de la grieta de una longitud no inferior a 20 cm, repitiendo la operación cada 30 cm, dependiendo de la gravedad de la misma.

Obertura de orificios para la colocación de grapas en forma de "U" fabricadas con varillas de acero inoxidable de 8 mm de diámetro, ancladas mediante resina de Epoxi de dos componentes.

Una vez colocadas las grapas, las cuales quedarán embebidas totalmente en el paramento, se procederá al rellenado de las regatas y grietas con morteros especiales sin retracción Sika Top 122 y enmallado de la zona con malla antialcalis.

fisuras ladrillo fachada: 5.80"""

    print(f"Querying for:\n{query[:100]}...\n")
    matches = matcher.find_best_match(query, top_k=5)
    
    for rank, (score, item) in enumerate(matches):
        print(f"Match #{rank+1} (Score: {score:.4f})")
        print(f"Code: {item.get('codigo')}")
        print(f"Summary: {item.get('resumen')}")
        print("-" * 40)
