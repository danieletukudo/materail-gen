import json
from openai import OpenAI
import numpy as np
from typing import List, Dict
import os
import re

# Initialize OpenAI client
# Ensure OPENAI_API_KEY is set in your environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AI_MaterialMatcher:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.data = []
        self._load_data()

    def _load_data(self):
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")

    def _construct_full_text(self, item: Dict) -> str:
        """
        Constructs a comprehensive description string for an item.
        """
        parts = []
        if item.get('codigo'): parts.append(f"Code: {item['codigo']}")
        if item.get('resumen'): parts.append(f"Description: {item['resumen']}")
        
        sub_materials_text = []
        if item.get('sub_materials'):
            for sub in item['sub_materials']:
                sub_desc = sub.get('resumen', '')
                if sub_desc:
                    sub_materials_text.append(sub_desc)
        
        if sub_materials_text:
            parts.append("Sub-materials: " + "; ".join(sub_materials_text))
            
        return "\n".join(parts)

    def find_best_match(self, user_query: str, top_k: int = 3):
        """
        Uses OpenAI's Chat Completion to find the best match from a shortlist.
        """
        
        # Step 1: Fast pre-filtering (Keyword/Jaccard overlap)
        candidates = self._pre_filter(user_query, top_n=20)
        
        if not candidates:
            print("No relevant candidates found in database.")
            return None

        # Step 2: AI Selection
        return self._ask_ai_to_select(user_query, candidates)

    def _pre_filter(self, query: str, top_n: int = 20) -> List[Dict]:
        # Simple token overlap search to reduce search space for AI
        query_tokens = set(re.findall(r'\w+', query.lower()))
        scored_candidates = []
        
        for item in self.data:
            full_text = self._construct_full_text(item).lower()
            item_tokens = set(re.findall(r'\w+', full_text))
            
            if not item_tokens: continue
            
            # Jaccard similarity
            intersection = len(query_tokens.intersection(item_tokens))
            union = len(query_tokens.union(item_tokens))
            score = intersection / union if union > 0 else 0
            
            if score > 0:
                scored_candidates.append((score, item))
        
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scored_candidates[:top_n]]

    def _ask_ai_to_select(self, query: str, candidates: List[Dict]):
        candidate_text = ""
        for i, item in enumerate(candidates):
            code = item.get('codigo', 'N/A')
            desc = item.get('resumen', 'N/A')
            # Include a snippet of sub-materials to give context without blowing up token context
            sub_preview = ""
            if item.get('sub_materials'):
                sub_preview = " | ".join([s.get('resumen', '') for s in item['sub_materials'][:5]]) # Increased context
            
            candidate_text += f"Option {i+1}:\nCode: {code}\nDescription: {desc}\nDetails: {sub_preview[:500]}...\n\n"

        prompt = f"""
        You are an expert construction quantity surveyor. 
        
        USER REQUEST:
        "{query}"
        
        Based on the user's request, select the single best matching material code from the list below.
        Consider the specific brand names (BASF, MasterSeal) and system type (polyurethane waterproofing) carefully.
        
        CANDIDATE LIST:
        {candidate_text}
        
        INSTRUCTIONS:
        1. Analyze which option best fits the user's specific requirements.
        2. Return ONLY a JSON object with the following format:
           {{
             "best_code": "CODE_HERE",
             "reasoning": "Brief explanation why this is the best fit."
           }}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"AI Error: {e}")
            return None

if __name__ == "__main__":
    json_file = "/Users/danielsamuel/PycharmProjects/RAG/materail-gen/DATABSE_parsed.json"
    matcher = AI_MaterialMatcher(json_file)
    
    query = """Impermeabilización de cubiertas, realizada mediante el sistema visto MasterSeal 640 "BASF Construction Chemical", con DITE - 05/0197, compuesta por: membrana elástica impermeabilizante a base de poliuretano, MasterSeal M 640 "BASF Construction Chemical", aplicada mediante brocha, rodillo o pistola; y capa de acabado con revestimiento elástico a base de poliuretano alifático, MasterSeal TC 640 "BASF Construction Chemical", aplicada mediante brocha, rodillo o pistola; previa imprimación con MasterSeal P 640 "BASF Construction Chemical", aplicada con brocha, rodillo o pistola.

Adecuación generalizada: 50.25 * 1.00 * 0.10 = 5.03

Perimetros y zócalos: 35.56 * 1.00 * 0.30 = 10.67"""
    
    print(f"Asking AI to match:\n'{query[:100]}...'\n")
    result = matcher.find_best_match(query)
    
    if result:
        print("\nAI Selected Match:")
        print(f"Code: {result.get('best_code')}")
        print(f"Reasoning: {result.get('reasoning')}")
