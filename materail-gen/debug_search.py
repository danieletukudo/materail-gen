import json

def find_code_by_description():
    json_path = "/Users/danielsamuel/PycharmProjects/RAG/materail-gen/DATABSE_parsed.json"
    
    # Key phrases from your description to search for
    target_phrases = [
        "Reparación de revestimiento de mortero",
        "fisuras generalizadas",
        "módulo de elasticidad de 15000"
    ]
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"Searching {len(data)} items...")
        
        for item in data:
            full_text = str(item.get('resumen', '')).lower()
            if item.get('sub_materials'):
                for sub in item['sub_materials']:
                    full_text += " " + str(sub.get('resumen', '')).lower()
            
            # Check if any significant part of the query exists in the item
            # We'll check for "15000" as it's a very specific number
            if "15000" in full_text and "mortero" in full_text:
                print("\nPotential Match Found:")
                print(f"Code: {item.get('codigo')}")
                print(f"Summary: {item.get('resumen')}")
                print("-" * 40)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_code_by_description()

