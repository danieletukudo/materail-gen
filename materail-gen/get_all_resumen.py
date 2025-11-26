#!/usr/bin/env python3
"""
Simple function to get all "Resumen" (descriptions) from the database
"""

from excel_parser import ExcelDatabaseParser
from typing import List, Dict


def get_all_resumen(database_path: str) -> List[Dict[str, str]]:
    """
    Get all "Resumen" (descriptions) from the construction materials database
    
    Args:
        database_path: Path to the Excel database file
        
    Returns:
        List of dictionaries with 'codigo' and 'resumen' for each material
        
    Example:
        >>> resumenes = get_all_resumen('/path/to/DATABSE.xlsx')
        >>> for item in resumenes:
        >>>     print(f"{item['codigo']}: {item['resumen']}")
    """
    # Parse the database
    parser = ExcelDatabaseParser(database_path)
    parser.load_excel()
    parser.parse_materials()
    
    # Extract all resumen
    all_resumen = []
    
    for material in parser.get_materials():
        all_resumen.append({
            'codigo': material.codigo,
            'resumen': material.resumen
        })
    
    return all_resumen


def get_all_resumen_text_only(database_path: str) -> List[str]:
    """
    Get all "Resumen" (descriptions) as a simple list of strings
    
    Args:
        database_path: Path to the Excel database file
        
    Returns:
        List of resumen strings
        
    Example:
        >>> resumenes = get_all_resumen_text_only('/path/to/DATABSE.xlsx')
        >>> for resumen in resumenes:
        >>>     print(resumen)
    """
    # Parse the database
    parser = ExcelDatabaseParser(database_path)
    parser.load_excel()
    parser.parse_materials()
    
    # Extract all resumen as text only
    return [material.resumen for material in parser.get_materials()]


def get_all_resumen_with_details(database_path: str) -> List[Dict[str, any]]:
    """
    Get all "Resumen" with additional details (codigo, tipo, precio)
    
    Args:
        database_path: Path to the Excel database file
        
    Returns:
        List of dictionaries with full material details
        
    Example:
        >>> resumenes = get_all_resumen_with_details('/path/to/DATABSE.xlsx')
        >>> for item in resumenes:
        >>>     print(f"{item['codigo']}: {item['resumen']} - {item['precio']}€")
    """
    # Parse the database
    parser = ExcelDatabaseParser(database_path)
    parser.load_excel()
    parser.parse_materials()
    
    # Extract all resumen with details
    all_resumen = []
    
    for material in parser.get_materials():
        all_resumen.append({
            'codigo': material.codigo,
            'tipo': material.tipo,
            'ud': material.ud,
            'resumen': material.resumen,
            'precio': material.precio,
            'num_sub_materials': len(material.sub_materials)
        })
    
    return all_resumen


# Example usage
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python get_all_resumen.py <database_path>")
        print("Example: python get_all_resumen.py database.xlsx")
        sys.exit(1)
    
    database_path = sys.argv[1]
    
    print("="*100)
    print("OPTION 1: Get all Resumen with Codigo")
    print("="*100)
    
    resumenes = get_all_resumen(database_path)
    
    print(f"\nTotal materials: {len(resumenes)}\n")
    
    # Show first 5
    for i, item in enumerate(resumenes[:5], 1):
        print(f"{i}. {item['codigo']}")
        print(f"   {item['resumen'][:80]}...")
        print()
    
    print("\n" + "="*100)
    print("OPTION 2: Get all Resumen as text only")
    print("="*100)
    
    resumen_texts = get_all_resumen_text_only(database_path)
    
    print(f"\nTotal: {len(resumen_texts)}\n")
    
    # Show first 5
    for i, resumen in enumerate(resumen_texts[:5], 1):
        print(f"{i}. {resumen[:80]}...")
    
    print("\n" + "="*100)
    print("OPTION 3: Get all Resumen with full details")
    print("="*100)
    
    resumen_details = get_all_resumen_with_details(database_path)
    
    print(f"\nTotal: {len(resumen_details)}\n")
    
    # Show first 5
    for i, item in enumerate(resumen_details[:5], 1):
        print(f"{i}. {item['codigo']}")
        print(f"   Resumen: {item['resumen'][:60]}...")
        print(f"   Precio: {item['precio']}€")
        print(f"   Sub-materials: {item['num_sub_materials']}")
        print()
    
    print("\n" + "="*100)
    print("USAGE EXAMPLES")
    print("="*100)
    print("""
# Simple usage:
from get_all_resumen import get_all_resumen

resumenes = get_all_resumen('/path/to/DATABSE.xlsx')

for item in resumenes:
    print(f"{item['codigo']}: {item['resumen']}")

# Or just text:
from get_all_resumen import get_all_resumen_text_only

texts = get_all_resumen_text_only('/path/to/DATABSE.xlsx')

for text in texts:
    print(text)

# Or with details:
from get_all_resumen import get_all_resumen_with_details

details = get_all_resumen_with_details('/path/to/DATABSE.xlsx')

for item in details:
    print(f"{item['codigo']}: {item['resumen']} - {item['precio']}€")
    """)

