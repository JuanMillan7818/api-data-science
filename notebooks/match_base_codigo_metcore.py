import pandas as pd
from pathlib import Path

class MetCoreMatcher:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent / "centenarios"
        self.df_original = None
        self.df_metcore = None
        self.df_ids = None
        
    def load_data(self):
        """Carga los archivos necesarios"""
        try:
            print("📂 Cargando archivos...")
            
            # Cargar base original
            original_path = self.base_path / "centenarios_metabolomica.xlsx"
            self.df_original = pd.read_excel(original_path)
            print(f"✅ Base original: {len(self.df_original)} filas")
            
            # Cargar archivo con IDs MetCore
            ids_path = self.base_path / "Centenarios_metabolomica_IDs.xlsx"
            self.df_ids = pd.read_excel(ids_path)
            print(f"✅ Archivo IDs: {len(self.df_ids)} filas")
            
            return True
            
        except Exception as e:
            print(f"❌ Error cargando archivos: {str(e)}")
            return False
    
    def extract_name_from_metcore(self, metcore_code):
        """Extrae nombre y apellido del código MetCore"""
        if pd.isna(metcore_code):
            return None, None
            
        code_str = str(metcore_code).strip()
        
        # Patrones comunes de códigos MetCore
        # g1_001, g2_123, etc.
        if '_' in code_str:
            parts = code_str.split('_')
            if len(parts) >= 2:
                prefix = parts[0]  # g1, g2, etc.
                number = parts[1]  # 001, 123, etc.
                
                # Buscar coincidencia en la base original
                matching_rows = self.df_original[self.df_original['Número'] == int(number)]
                
                if not matching_rows.empty:
                    row = matching_rows.iloc[0]
                    return row.get('Nombre'), row.get('Apellido')
        
        return None, None
    
    def match_and_verify(self):
        """Realiza el matching y verificación"""
        if self.df_original is None or self.df_ids is None:
            print("❌ Error: Datos no cargados")
            return
        
        print("\n🔍 REALIZANDO MATCH Y VERIFICACIÓN...")
        print("=" * 60)
        
        # Analizar estructura del archivo IDs
        print("📋 Columnas en archivo IDs:")
        for col in self.df_ids.columns:
            print(f"  • {col}")
        
        # Buscar columna que contiene los códigos MetCore
        metcore_col = None
        for col in self.df_ids.columns:
            if 'metcore' in col.lower() or 'código' in col.lower():
                metcore_col = col
                break
        
        if metcore_col is None:
            print("❌ No se encontró columna con códigos MetCore")
            print("Columnas disponibles:", list(self.df_ids.columns))
            return
        
        print(f"\n🎯 Usando columna: {metcore_col}")
        
        # Crear resultados
        results = []
        matches = 0
        no_matches = 0
        
        for idx, row in self.df_ids.iterrows():
            metcore_code = row[metcore_col]
            number_from_code = None
            name_match = None
            surname_match = None
            
            # Extraer número del código MetCore
            if pd.notna(metcore_code):
                code_str = str(metcore_code).strip()
                if '_' in code_str:
                    number_from_code = code_str.split('_')[1]
                    try:
                        number_from_code = int(number_from_code)
                    except ValueError:
                        number_from_code = None
            
            # Buscar en base original
            if number_from_code is not None:
                matching_rows = self.df_original[self.df_original['Número'] == number_from_code]
                
                if not matching_rows.empty:
                    matches += 1
                    original_row = matching_rows.iloc[0]
                    name_match = original_row.get('Nombre')
                    surname_match = original_row.get('Apellido')
                else:
                    no_matches += 1
            
            results.append({
                'fila_ids': idx + 2,  # +2 porque Excel empieza en 1 y hay header
                'codigo_metcore': metcore_code,
                'numero_extraido': number_from_code,
                'nombre_original': name_match,
                'apellido_original': surname_match,
                'estado': 'MATCH' if name_match else 'NO MATCH'
            })
        
        # Crear DataFrame con resultados
        df_results = pd.DataFrame(results)
        
        # Mostrar resumen
        print(f"\n📊 RESUMEN DEL MATCH:")
        print(f"  • Total registros: {len(df_results)}")
        print(f"  • Con match: {matches}")
        print(f"  • Sin match: {no_matches}")
        print(f"  • Tasa de match: {(matches/len(df_results)*100):.1f}%")
        
        # Mostrar primeros ejemplos
        print(f"\n🔍 EJEMPLOS DE MATCHING:")
        print("-" * 80)
        
        # Mostrar primeros 10 resultados
        for i, row in df_results.head(10).iterrows():
            codigo_str = str(row['codigo_metcore']) if pd.notna(row['codigo_metcore']) else 'N/A'
            numero_str = str(row['numero_extraido']) if pd.notna(row['numero_extraido']) else 'N/A'
            estado_str = str(row['estado']) if pd.notna(row['estado']) else 'N/A'
            
            print(f"Fila {row['fila_ids']:3d}: {codigo_str:12s} → N°{numero_str:3s} → {estado_str:8s}")
            if row['estado'] == 'MATCH':
                nombre = str(row['nombre_original']) if pd.notna(row['nombre_original']) else 'N/A'
                apellido = str(row['apellido_original']) if pd.notna(row['apellido_original']) else 'N/A'
                print(f"         Nombre: {nombre} {apellido}")
            print()
        
        # Mostrar errores
        errores = df_results[df_results['estado'] == 'NO MATCH']
        if not errores.empty:
            print(f"\n❌ ERRORES DE MATCHING ({len(errores)}):")
            print("-" * 60)
            for _, row in errores.head(10).iterrows():
                codigo_str = str(row['codigo_metcore']) if pd.notna(row['codigo_metcore']) else 'N/A'
                numero_str = str(row['numero_extraido']) if pd.notna(row['numero_extraido']) else 'N/A'
                print(f"Fila {row['fila_ids']:3d}: {codigo_str:12s} → N°{numero_str:3s} → SIN COINCIDENCIA")
        
        return df_results
    
    def save_results(self, df_results):
        """Guarda los resultados en archivos Excel"""
        try:
            output_path = Path("resultados_matching_metcore.xlsx")
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Hoja 1: Resultados completos
                df_results.to_excel(writer, sheet_name='Matching_Resultados', index=False)
                
                # Hoja 2: Solo errores
                errores = df_results[df_results['estado'] == 'NO MATCH']
                if not errores.empty:
                    errores.to_excel(writer, sheet_name='Errores_Matching', index=False)
                
                # Hoja 3: Estadísticas
                stats_data = {
                    'Métrica': ['Total registros', 'Con match', 'Sin match', 'Tasa de match'],
                    'Valor': [
                        len(df_results),
                        len(df_results[df_results['estado'] == 'MATCH']),
                        len(df_results[df_results['estado'] == 'NO MATCH']),
                        f"{(len(df_results[df_results['estado'] == 'MATCH'])/len(df_results)*100):.1f}%"
                    ]
                }
                df_stats = pd.DataFrame(stats_data)
                df_stats.to_excel(writer, sheet_name='Estadísticas', index=False)
            
            print(f"\n💾 Resultados guardados en: {output_path}")
            print("📋 Hojas generadas:")
            print("  • Matching_Resultados: Todos los resultados")
            print("  • Errores_Matching: Solo los errores")
            print("  • Estadísticas: Resumen numérico")
            
        except Exception as e:
            print(f"❌ Error guardando resultados: {str(e)}")
    
    def analyze_patterns(self):
        """Analiza patrones en los códigos MetCore"""
        if self.df_ids is None:
            return
        
        print("\n🔬 ANÁLISIS DE PATRONES EN CÓDIGOS METCORE:")
        print("=" * 60)
        
        # Buscar columna con códigos
        metcore_col = None
        for col in self.df_ids.columns:
            if 'metcore' in col.lower() or 'código' in col.lower():
                metcore_col = col
                break
        
        if metcore_col is None:
            print("❌ No se encontró columna con códigos")
            return
        
        # Extraer códigos no nulos
        codigos = self.df_ids[metcore_col].dropna()
        codigos_str = [str(c).strip() for c in codigos if str(c).strip() != '']
        
        print(f"Total códigos analizados: {len(codigos_str)}")
        
        # Analizar patrones
        prefijos = {}
        numeros = []
        
        for codigo in codigos_str:
            if '_' in codigo:
                partes = codigo.split('_')
                if len(partes) >= 2:
                    prefijo = partes[0]
                    numero = partes[1]
                    
                    prefijos[prefijo] = prefijos.get(prefijo, 0) + 1
                    try:
                        numeros.append(int(numero))
                    except ValueError:
                        pass
        
        print(f"\n📊 PREFIJOS ENCONTRADOS:")
        for prefijo, count in sorted(prefijos.items()):
            print(f"  • {prefijo}: {count} códigos")
        
        if numeros:
            print(f"\n📈 ANÁLISIS DE NÚMEROS:")
            print(f"  • Rango: {min(numeros)} - {max(numeros)}")
            print(f"  • Promedio: {sum(numeros)/len(numeros):.1f}")
            print(f"  • Números únicos: {len(set(numeros))}")

def main():
    matcher = MetCoreMatcher()
    
    # Cargar datos
    if not matcher.load_data():
        return
    
    # Analizar patrones
    matcher.analyze_patterns()
    
    # Realizar matching
    df_results = matcher.match_and_verify()
    
    # Guardar resultados
    if df_results is not None:
        matcher.save_results(df_results)

if __name__ == "__main__":
    main()