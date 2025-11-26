#!/usr/bin/env python3
"""
Generate a formatted text file of all materials for use with GPT matcher
"""

from get_all_resumen import get_all_resumen
import os

def generate_materials_text_file(database_path: str, output_path: str):
    """
    Generate a formatted text file from the database for GPT matcher
    
    Args:
        database_path: Path to the Excel database file
        output_path: Path where to save the text file
    """
    print("Loading materials from database...")
    materials = get_all_resumen(database_path)
    
    print(f"Found {len(materials)} materials")
    print(f"Generating text file at: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Total Materials: {len(materials)}\n")
        f.write("=" * 100 + "\n\n")
        
        for i, material in enumerate(materials, 1):
            f.write(f"{i}. {material['codigo']}\n")
            f.write(f"   {material['resumen']}\n\n")
    
    print(f"✅ Successfully generated {output_path}")
    print(f"   File size: {os.path.getsize(output_path) / 1024:.2f} KB")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python generate_materials_list.py <database_path> <output_path>")
        print("Example: python generate_materials_list.py database.xlsx materials_list.txt")
        sys.exit(1)
    
    database_path = sys.argv[1]
    output_path = sys.argv[2]
    
    generate_materials_text_file(database_path, output_path)

