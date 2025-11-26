"""
RAG System for Construction Materials Database
Uses semantic search to find materials by their descriptions (Resumen)
and returns complete hierarchical information with sub-materials
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json
from excel_parser import ExcelDatabaseParser, MainMaterial
from tabulate import tabulate
import os


class MaterialRAGSystem:
    """RAG system for querying construction materials database"""
    
    def __init__(self, 
                 excel_path: str,
                 collection_name: str = "construction_materials",
                 embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2",
                 persist_directory: str = "./chroma_db"):
        """
        Initialize the RAG system
        
        Args:
            excel_path: Path to Excel database file
            collection_name: Name for ChromaDB collection
            embedding_model: Sentence transformer model for embeddings
            persist_directory: Directory to persist ChromaDB
        """
        self.excel_path = excel_path
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize sentence transformer for multilingual support (Spanish)
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB
        print(f"Initializing ChromaDB at: {persist_directory}")
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Parse materials
        self.parser = ExcelDatabaseParser(excel_path)
        self.materials: List[MainMaterial] = []
        
    def build_database(self, force_rebuild: bool = False):
        """
        Build or load the vector database
        
        Args:
            force_rebuild: If True, rebuild database even if it exists
        """
        # Check if collection exists
        try:
            if force_rebuild:
                print("Force rebuild requested, deleting existing collection...")
                self.chroma_client.delete_collection(self.collection_name)
                raise ValueError("Force rebuild")
            
            self.collection = self.chroma_client.get_collection(self.collection_name)
            print(f"Loaded existing collection: {self.collection_name}")
            print(f"Collection contains {self.collection.count()} documents")
            
            # Load materials from JSON if available
            json_path = self.excel_path.replace('.xlsx', '_parsed.json')
            if os.path.exists(json_path):
                print(f"Loading materials from {json_path}")
                with open(json_path, 'r', encoding='utf-8') as f:
                    materials_dict = json.load(f)
                # Note: We'll need to reconstruct MainMaterial objects if needed
                print(f"Loaded {len(materials_dict)} materials from cache")
            
        except Exception as e:
            print(f"Building new collection: {e}")
            
            # Parse Excel file
            print("Parsing Excel database...")
            self.parser.load_excel()
            self.parser.parse_materials()
            self.materials = self.parser.get_materials()
            
            # Save parsed materials
            json_path = self.excel_path.replace('.xlsx', '_parsed.json')
            self.parser.save_to_json(json_path)
            
            # Create collection
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Construction materials database with hierarchical structure"}
            )
            
            # Prepare documents for embedding
            print("Creating embeddings...")
            documents = []
            metadatas = []
            ids = []
            
            for idx, material in enumerate(self.materials):
                # Create rich text for embedding
                # Include codigo and resumen for better semantic search
                doc_text = f"{material.codigo}: {material.resumen}"
                
                # Add sub-materials context for richer embeddings
                sub_materials_text = []
                for sm in material.sub_materials:
                    if sm.resumen and sm.resumen.strip():
                        sub_materials_text.append(sm.resumen)
                
                if sub_materials_text:
                    # Add first few sub-materials to context (limit to avoid too long text)
                    doc_text += " | Componentes: " + " | ".join(sub_materials_text[:5])
                
                documents.append(doc_text)
                
                # Store metadata
                metadata = {
                    "codigo": material.codigo,
                    "tipo": material.tipo,
                    "ud": material.ud,
                    "resumen": material.resumen,
                    "precio": material.precio,
                    "row_index": material.row_index,
                    "num_sub_materials": len(material.sub_materials)
                }
                metadatas.append(metadata)
                # Use unique ID combining index and codigo to handle duplicates
                ids.append(f"{idx}_{material.codigo}")
            
            # Generate embeddings
            print(f"Generating embeddings for {len(documents)} materials...")
            embeddings = self.embedding_model.encode(
                documents,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            # Add to ChromaDB
            print("Adding to ChromaDB...")
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"Successfully indexed {len(documents)} materials")
    
    def query(self, 
              query_text: str, 
              top_k: int = 5,
              return_full_details: bool = True) -> List[Dict[str, Any]]:
        """
        Query the database with natural language
        
        Args:
            query_text: Natural language query (e.g., "limpieza de alicatado")
            top_k: Number of results to return
            return_full_details: If True, include full sub-materials details
            
        Returns:
            List of matching materials with their details
        """
        print(f"\nSearching for: '{query_text}'")
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query_text,
            convert_to_numpy=True
        )
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        
        for i in range(len(results['ids'][0])):
            result = {
                'codigo': results['metadatas'][0][i]['codigo'],
                'resumen': results['metadatas'][0][i]['resumen'],
                'tipo': results['metadatas'][0][i]['tipo'],
                'ud': results['metadatas'][0][i]['ud'],
                'precio': results['metadatas'][0][i]['precio'],
                'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                'num_sub_materials': results['metadatas'][0][i]['num_sub_materials']
            }
            
            # Get full material details if requested
            if return_full_details:
                # Find the material in our parsed materials
                material = self._find_material_by_codigo(result['codigo'])
                if material:
                    result['sub_materials'] = [
                        {
                            'codigo': sm.codigo,
                            'tipo': sm.tipo,
                            'ud': sm.ud,
                            'resumen': sm.resumen,
                            'cantidad': sm.cantidad,
                            'precio': sm.precio,
                            'importe': sm.importe
                        }
                        for sm in material.sub_materials
                    ]
            
            formatted_results.append(result)
        
        return formatted_results
    
    def _find_material_by_codigo(self, codigo: str) -> Optional[MainMaterial]:
        """Find a material by its codigo"""
        # Reload materials if not in memory
        if not self.materials:
            print("Reloading materials from Excel...")
            self.parser.load_excel()
            self.parser.parse_materials()
            self.materials = self.parser.get_materials()
        
        for material in self.materials:
            if material.codigo == codigo:
                return material
        return None
    
    def display_result(self, result: Dict[str, Any], show_sub_materials: bool = True):
        """
        Display a single result in a formatted table
        
        Args:
            result: Result dictionary from query
            show_sub_materials: Whether to show sub-materials table
        """
        print("\n" + "="*120)
        print(f"MATERIAL: {result['codigo']}")
        print("="*120)
        
        # Main material info
        main_info = [
            ["Código", result['codigo']],
            ["Tipo", result['tipo']],
            ["Unidad", result['ud']],
            ["Resumen", result['resumen']],
            ["Precio (€)", f"{result['precio']:.2f}"],
            ["Similarity Score", f"{result['similarity_score']:.4f}"],
            ["Sub-materials", result['num_sub_materials']]
        ]
        
        print(tabulate(main_info, tablefmt="grid"))
        
        # Sub-materials table - COMPLETE with all columns
        if show_sub_materials and 'sub_materials' in result:
            print("\n" + "-"*120)
            print("SUB-MATERIALS (Complete Details):")
            print("-"*120)
            
            sub_materials_table = []
            for sm in result['sub_materials']:
                # Format each field properly
                codigo = sm['codigo'] if sm['codigo'] else ''
                tipo = sm['tipo'] if sm['tipo'] else ''
                ud = sm['ud'] if sm['ud'] else ''
                resumen = sm['resumen'] if sm['resumen'] else ''
                
                # Format numbers with proper handling of None
                if sm['cantidad'] is not None:
                    cantidad = f"{sm['cantidad']:.5f}"
                else:
                    cantidad = ''
                
                if sm['precio'] is not None:
                    precio = f"{sm['precio']:.2f}"
                else:
                    precio = ''
                
                if sm['importe'] is not None:
                    importe = f"{sm['importe']:.2f}"
                else:
                    importe = ''
                
                sub_materials_table.append([
                    codigo,
                    tipo,
                    ud,
                    resumen[:80] + '...' if len(resumen) > 80 else resumen,
                    cantidad,
                    precio,
                    importe
                ])
            
            headers = ["Código", "Tipo", "Ud", "Resumen", "Cantidad", "Precio (€)", "Importe (€)"]
            print(tabulate(sub_materials_table, headers=headers, tablefmt="grid", maxcolwidths=[25, 15, 8, 80, 12, 12, 12]))
    
    def display_results(self, results: List[Dict[str, Any]], show_sub_materials: bool = True):
        """Display multiple results"""
        print(f"\n{'='*100}")
        print(f"FOUND {len(results)} MATCHING MATERIALS")
        print(f"{'='*100}")
        
        for i, result in enumerate(results, 1):
            print(f"\n[{i}]")
            self.display_result(result, show_sub_materials=show_sub_materials)
    
    def export_result_to_excel(self, result: Dict[str, Any], output_path: str):
        """
        Export a single result to Excel format matching the original database structure
        
        Args:
            result: Result dictionary from query
            output_path: Path to save Excel file
        """
        import pandas as pd
        
        # Create rows for Excel
        rows = []
        
        # Main material row
        rows.append({
            'Código': result['codigo'],
            'Tipo': result['tipo'],
            'Ud': result['ud'],
            'Resumen': result['resumen'],
            'Cantidad': None,
            'Precio (€)': result['precio'],
            'Importe (€)': None
        })
        
        # Sub-materials rows
        if 'sub_materials' in result:
            for sm in result['sub_materials']:
                rows.append({
                    'Código': sm['codigo'],
                    'Tipo': sm['tipo'],
                    'Ud': sm['ud'],
                    'Resumen': sm['resumen'],
                    'Cantidad': sm['cantidad'],
                    'Precio (€)': sm['precio'],
                    'Importe (€)': sm['importe']
                })
        
        # Create DataFrame and save
        df = pd.DataFrame(rows)
        df.to_excel(output_path, index=False)
        print(f"\nExported to: {output_path}")


def main():
    """Demo usage of the RAG system"""
    # Initialize RAG system
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rag_system.py <database_path>")
        print("Example: python rag_system.py database.xlsx")
        sys.exit(1)
    
    excel_path = sys.argv[1]
    
    rag = MaterialRAGSystem(
        excel_path=excel_path,
        persist_directory='./chroma_db'
    )
    
    # Build database (only first time, or force_rebuild=True)
    rag.build_database(force_rebuild=False)
    
    # Example queries
    queries = [
        "limpieza de alicatado cerámico",
        "demolición de aplacado pétreo",
        "revoco decorativo",
    ]
    
    for query in queries:
        results = rag.query(query, top_k=3)
        rag.display_results(results, show_sub_materials=True)
        
        # Export first result
        if results:
            output_path = f"result_{query.replace(' ', '_')}.xlsx"
            rag.export_result_to_excel(results[0], output_path)


if __name__ == '__main__':
    main()

