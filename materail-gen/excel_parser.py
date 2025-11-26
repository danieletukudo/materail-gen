"""
Excel Parser for Construction Materials Database
Extracts hierarchical structure of main materials and their sub-materials
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class SubMaterial:
    """Represents a sub-material or component"""
    codigo: Optional[str]
    tipo: Optional[str]
    ud: Optional[str]
    resumen: str
    cantidad: Optional[float]
    precio: Optional[float]
    importe: Optional[float]
    row_index: int


@dataclass
class MainMaterial:
    """Represents a main material with its sub-materials"""
    codigo: str
    tipo: str
    ud: str
    resumen: str
    precio: float
    row_index: int
    sub_materials: List[SubMaterial]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'codigo': self.codigo,
            'tipo': self.tipo,
            'ud': self.ud,
            'resumen': self.resumen,
            'precio': self.precio,
            'row_index': self.row_index,
            'sub_materials': [asdict(sm) for sm in self.sub_materials]
        }


class ExcelDatabaseParser:
    """Parser for construction materials Excel database"""
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = None
        self.materials: List[MainMaterial] = []
        
    def load_excel(self):
        """Load Excel file and prepare dataframe"""
        # Read Excel without header, we'll identify columns manually
        self.df = pd.read_excel(self.excel_path, sheet_name=0, header=None)
        
        # Find the header row (contains "Código", "Tipo", "Ud", etc.)
        header_row_idx = None
        for idx, row in self.df.iterrows():
            if row[0] == 'Código' and row[1] == 'Tipo':
                header_row_idx = idx
                break
        
        if header_row_idx is None:
            raise ValueError("Could not find header row in Excel file")
        
        # Set proper column names
        self.df.columns = self.df.iloc[header_row_idx].values
        # Drop rows before and including header
        self.df = self.df.iloc[header_row_idx + 1:].reset_index(drop=True)
        
        # Clean up column names
        self.df.columns = ['Código', 'Tipo', 'Ud', 'Resumen', 'Cantidad', 'Precio (€)', 'Importe (€)']
        
        print(f"Loaded Excel with {len(self.df)} rows")
        
    def is_main_material(self, row: pd.Series, idx: int) -> bool:
        """
        Determine if a row is a main material (bold in Excel)
        Main materials have:
        - Non-null Código
        - Tipo = 'Partida'
        - Non-null Precio
        - NOT a common sub-material code (like moc-std1-generico, mo-salarial-, etc.)
        """
        codigo = row['Código']
        tipo = row['Tipo']
        precio = row['Precio (€)']
        
        # Check if it's a valid main material
        if pd.isna(codigo) or pd.isna(tipo):
            return False
            
        # Main materials are typically "Partida" type with a price
        if tipo == 'Partida' and not pd.isna(precio):
            codigo_str = str(codigo).strip().lower()
            
            # Exclude common sub-material codes that also have Tipo='Partida'
            # These are crew/labor codes that appear as sub-materials
            excluded_prefixes = ('moc-', 'mo-salarial', 'alq-', 'm.o.')
            
            if not codigo_str.startswith(excluded_prefixes):
                # This is likely a main material
                return True
                
        return False
    
    def extract_sub_materials(self, start_idx: int) -> List[SubMaterial]:
        """
        Extract all sub-materials following a main material
        Sub-materials continue until we hit another main material or chapter
        """
        sub_materials = []
        current_idx = start_idx + 1
        
        while current_idx < len(self.df):
            row = self.df.iloc[current_idx]
            
            # Stop if we hit another main material
            if self.is_main_material(row, current_idx):
                break
            
            # Stop if we hit a chapter
            if row['Tipo'] == 'Capítulo':
                break
            
            codigo = row['Código']
            tipo = row['Tipo']
            resumen = row['Resumen']
            
            # Skip completely empty rows
            if pd.isna(codigo) and pd.isna(tipo) and pd.isna(resumen):
                current_idx += 1
                continue
            
            # Create sub-material entry with error handling for numeric fields
            try:
                cantidad = None if pd.isna(row['Cantidad']) else float(row['Cantidad'])
            except (ValueError, TypeError):
                cantidad = None
                
            try:
                precio = None if pd.isna(row['Precio (€)']) else float(row['Precio (€)'])
            except (ValueError, TypeError):
                precio = None
                
            try:
                importe = None if pd.isna(row['Importe (€)']) else float(row['Importe (€)'])
            except (ValueError, TypeError):
                importe = None
            
            sub_material = SubMaterial(
                codigo=None if pd.isna(codigo) else str(codigo),
                tipo=None if pd.isna(tipo) else str(tipo),
                ud=None if pd.isna(row['Ud']) else str(row['Ud']),
                resumen='' if pd.isna(resumen) else str(resumen),
                cantidad=cantidad,
                precio=precio,
                importe=importe,
                row_index=current_idx
            )
            
            sub_materials.append(sub_material)
            current_idx += 1
        
        return sub_materials
    
    def parse_materials(self):
        """Parse all main materials and their sub-materials"""
        self.materials = []
        
        for idx, row in self.df.iterrows():
            if self.is_main_material(row, idx):
                # Extract main material info with error handling
                try:
                    precio = float(row['Precio (€)'])
                except (ValueError, TypeError):
                    precio = 0.0  # Default to 0 if price can't be parsed
                
                main_material = MainMaterial(
                    codigo=str(row['Código']).strip(),
                    tipo=str(row['Tipo']),
                    ud=str(row['Ud']) if not pd.isna(row['Ud']) else '',
                    resumen=str(row['Resumen']).strip() if not pd.isna(row['Resumen']) else '',
                    precio=precio,
                    row_index=idx,
                    sub_materials=[]
                )
                
                # Extract sub-materials
                main_material.sub_materials = self.extract_sub_materials(idx)
                
                self.materials.append(main_material)
                
                print(f"Found main material: {main_material.codigo} with {len(main_material.sub_materials)} sub-materials")
        
        print(f"\nTotal main materials extracted: {len(self.materials)}")
        
    def get_materials(self) -> List[MainMaterial]:
        """Return list of all parsed materials"""
        return self.materials
    
    def save_to_json(self, output_path: str):
        """Save parsed materials to JSON for inspection"""
        materials_dict = [m.to_dict() for m in self.materials]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(materials_dict, f, ensure_ascii=False, indent=2)
        print(f"Saved parsed materials to {output_path}")


def main():
    """Test the parser"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python excel_parser.py <database_path>")
        print("Example: python excel_parser.py database.xlsx")
        sys.exit(1)
    
    database_path = sys.argv[1]
    parser = ExcelDatabaseParser(database_path)
    parser.load_excel()
    parser.parse_materials()
    parser.save_to_json('parsed_materials.json')
    
    # Print sample
    if parser.materials:
        print("\n" + "="*80)
        print("SAMPLE MATERIAL:")
        print("="*80)
        sample = parser.materials[0]
        print(f"Código: {sample.codigo}")
        print(f"Resumen: {sample.resumen}")
        print(f"Precio: {sample.precio}€")
        print(f"\nSub-materials ({len(sample.sub_materials)}):")
        for sm in sample.sub_materials[:5]:  # Show first 5
            print(f"  - {sm.codigo or 'N/A'}: {sm.resumen[:60]}...")


if __name__ == '__main__':
    main()

