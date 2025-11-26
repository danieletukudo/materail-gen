import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class MaterialMatcher:
    def __init__(self, json_path):
        self.json_path = json_path
        self.data = []
        self.documents = []
        self.indices = []
        self.vectorizer = TfidfVectorizer(stop_words=None, max_features=5000) # Reduced features to save memory if that was the issue
        self.tfidf_matrix = None
        self._load_data()

    def _load_data(self):
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self.documents = []
            self.indices = []
            
            for i, item in enumerate(self.data):
                # Construct a rich text representation for each item
                full_text = self._construct_full_text(item)
                if full_text:
                    self.documents.append(full_text)
                    self.indices.append(i)
            
            if self.documents:
                self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
                
        except Exception as e:
            print(f"Error loading data: {e}")

    def _construct_full_text(self, item):
        """
        Combines relevant fields from the material and its sub-materials
        into a single string for similarity matching.
        """
        parts = []
        
        # Main item fields
        if item.get('codigo'):
            parts.append(str(item['codigo']))
        if item.get('resumen'):
            parts.append(str(item['resumen']))
        
        # Sub-materials fields
        if item.get('sub_materials'):
            for sub in item['sub_materials']:
                if sub.get('codigo'):
                    parts.append(str(sub['codigo']))
                if sub.get('resumen'):
                    parts.append(str(sub['resumen']))
        
        return " ".join(parts)

    def find_best_match(self, query_text, top_k=3):
        if self.tfidf_matrix is None:
            return []
            
        query_vec = self.vectorizer.transform([query_text])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get top K matches
        related_docs_indices = similarities.argsort()[:-top_k-1:-1]
        
        results = []
        for idx in related_docs_indices:
            original_idx = self.indices[idx]
            item = self.data[original_idx]
            score = similarities[idx]
            results.append({
                'score': score,
                'item': item,
            })
            
        return results

if __name__ == "__main__":
    # Example Usage
    json_file = "/Users/danielsamuel/PycharmProjects/RAG/materail-gen/DATABSE_parsed.json"
    matcher = MaterialMatcher(json_file)
    
    query = """Acceso vertical a las zonas de trabajo mediante técnicas de acceso y posicionamiento por cuerdas ( Técnicas de Trabajo Vertical ) . Incluye el montaje y desmontaje de instalaciones de cabecera en la zona superior. Anclajes mediante "Cintas de anclaje regulables" A 795-B. O mediante cuerda semi-estática Ø 10.5 y elementos con suficiente capacidad portante. Incluidos anclajes expansivos de tracción y anclajes químicos. Incluye equipos de protección individual ( EPIS ) y de acceso y posicionamiento por cuerda. Los operarios estarán homologados y acreditados para realizar dicho trabajos. Teniendo que presentar previo al trabajo al director de obra.

Trabajos verticales en la fachada trasera, última planta: 12.44 * 3.00 = 37.32"""

    print(f"Querying for:\n{query[:100]}...\n")
    matches = matcher.find_best_match(query, top_k=5)
    
    for rank, match in enumerate(matches):
        print(f"Match #{rank+1} (Score: {match['score']:.4f})")
        print(f"Code: {match['item'].get('codigo')}")
        print(f"Summary: {match['item'].get('resumen')}")
        print("-" * 40)
