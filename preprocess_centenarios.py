import pandas as pd
import sys
import os

# Agregar ruta del servicio para poder importarlo
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def calculate_completeness_like_api(df):
    """
    Calcula completitud exactamente como lo hace get_variable_completeness() en la API.
    """
    total_rows = len(df)
    completeness_map = {}
    
    for col in df.columns:
        non_null = int(df[col].count())
        null_count = total_rows - non_null
        pct = (non_null / total_rows) * 100 if total_rows > 0 else 0.0
        
        key = str(col).strip()
        completeness_map[key] = {
            "valid_percentage": pct,
            "null_count": null_count,
            "non_null_count": non_null,
            "total_rows": total_rows
        }
    
    return completeness_map

def preprocess_centenarios_data(input_path, output_path=None):
    """
    Preprocesa el dataset centenarios_metabolomica.xlsx:
    
    1. Elimina filas específicas: [7, 17, 33, 123]
    2. Elimina columnas de inmunología (patterns_to_drop)
    3. Elimina variables 'apellido' y 'nombre'
    
    Args:
        input_path (str): Ruta al archivo Excel de entrada
        output_path (str): Ruta al archivo Excel de salida (opcional)
    
    Returns:
        pd.DataFrame: DataFrame preprocesado
    """
    print("Iniciando preprocesamiento del dataset...")
    
    # 1. Cargar datos
    try:
        df = pd.read_excel(input_path)
        print(f"Dataset cargado: {df.shape[0]} filas × {df.shape[1]} columnas")
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return None
    
    # 2. Eliminar filas específicas
    rows_to_drop = [7, 17, 33, 123]
    original_rows = len(df)
    
    # Resetear índices y eliminar filas (exactamente como en exploracion.py)
    df = df.reset_index(drop=True)
    df = df[~df.index.isin(rows_to_drop)]
    
    print(f"Filas eliminadas: {original_rows - len(df)} ({rows_to_drop})")
    print(f"Filas restantes: {len(df)}")
    
    """
    # 3. Eliminar columnas de inmunología
    patterns_to_drop = [
        'Lymphocytes', 'B cells', 'T cells', 'CD3', 'CD4', 'CD8',
        'TEMRA', 'NAIVE', 'EM ', 'CM ', 'KLRG1', 'CD27', 'CD28', 'CD95', 'CD57'
    ]
    
    immune_cols = [col for col in df.columns if any(pat in col for pat in patterns_to_drop)]
    original_cols = len(df.columns)
    
    df = df.drop(columns=immune_cols)
    
    print(f"Columnas de inmunología eliminadas: {len(immune_cols)}")
    print(f"Columnas restantes: {len(df.columns)}")"""
    
    # 4. Eliminar columnas 'apellido' y 'nombre'
    personal_cols = [col for col in df.columns if col.lower() in ['apellido', 'nombre']]
    if personal_cols:
        df = df.drop(columns=personal_cols)
        print(f"Columnas personales eliminadas: {personal_cols}")
    
    # 5. Resumen final
    print(f"\nRESUMEN DEL PREPROCESAMIENTO:")
    print(f"   Dimensiones finales: {df.shape[0]} filas × {df.shape[1]} columnas")
    print(f"   Filas eliminadas: {original_rows - len(df)}")
    print(f"   Columnas eliminadas: {original_cols - len(df.columns)}")
    
    # 6. Guardar si se especifica output_path
    if output_path:
        try:
            df.to_excel(output_path, index=False)
            print(f"Dataset guardado en: {output_path}")
        except Exception as e:
            print(f"Error al guardar el archivo: {e}")
    
    return df

if __name__ == "__main__":
    # Configuración de rutas
    input_file = "centenarios/centenarios_metabolomica.xlsx"
    output_file = "centenarios/centenarios_metabolomica_clean.xlsx"
    
    # Ejecutar preprocesamiento (sin eliminación por completitud)
    df_clean = preprocess_centenarios_data(input_file, output_file)
    
    if df_clean is not None:
        print(f"\nPreprocesamiento completado exitosamente!")
        print(f"Archivo limpio guardado en: {output_file}")
    else:
        print(f"\nError en el preprocesamiento")
