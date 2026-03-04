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
    print(f"Índices a eliminar: {rows_to_drop}")
    
    # Mostrar números de pacientes que corresponden a esos índices
    if 'Número' in df.columns:
        pacientes_a_eliminar = []
        for idx in rows_to_drop:
            if idx < len(df):
                paciente_num = df.loc[idx, 'Número']
                pacientes_a_eliminar.append(paciente_num)
        print(f"Números de pacientes a eliminar por índice: {pacientes_a_eliminar}")
        
        # Agregar condición para eliminar pacientes con número 43 y 103
        pacientes_por_numero = [43, 103, 33, 106]
        pacientes_43_103_33 = df[df['Número'].isin(pacientes_por_numero)]
        if not pacientes_43_103_33.empty:
            print(f"Números de pacientes a eliminar por número: {pacientes_por_numero}")
            pacientes_a_eliminar.extend(pacientes_por_numero)
        
        print(f"Todos los números de pacientes a eliminar: {pacientes_a_eliminar}")
    else:
        print("Columna 'Número' no encontrada en el dataset")
    
    original_rows = len(df)
    
    # Resetear índices y eliminar filas por índice
    df = df.reset_index(drop=True)
    df = df[~df.index.isin(rows_to_drop)]
    
    # Eliminar filas por número (43, 103, 33 y 106)
    if 'Número' in df.columns:
        df = df[~df['Número'].isin([43, 103, 33, 106])]
        print(f"Filas eliminadas por número 43, 103, 33 y 106")
    
    print(f"Filas eliminadas: {original_rows - len(df)} ({rows_to_drop})")
    print(f"Filas restantes: {len(df)}")
    
    
    # 3. Eliminar columnas de inmunología
    patterns_to_drop = [
        'Lymphocytes', 'B cells', 'T cells', 'CD3', 'CD4', 'CD8',
        'TEMRA', 'NAIVE', 'EM ', 'CM ', 'KLRG1', 'CD27', 'CD28', 'CD95', 'CD57'
    ]
    
    immune_cols = [col for col in df.columns if any(pat in col for pat in patterns_to_drop)]
    original_cols = len(df.columns)
    
    df = df.drop(columns=immune_cols)
    
    print(f"Columnas de inmunología eliminadas: {len(immune_cols)}")
    print(f"Columnas restantes: {len(df.columns)}")
    
    # 4. Eliminar columnas 'apellido' y 'nombre'
    personal_cols = [col for col in df.columns if col.lower() in ['apellido', 'nombre']]
    if personal_cols:
        df = df.drop(columns=personal_cols)
        print(f"Columnas personales eliminadas: {personal_cols}")
    
    # 5. Eliminar variables con baja completitud (<73%)
    print("Calculando completitud de variables...")
    
    # Usar la función existente para calcular completitud
    completeness_map = calculate_completeness_like_api(df)
    
    # Identificar variables con completitud < 73%
    variables_baja_completitud = []
    for var_name, comp_data in completeness_map.items():
        if comp_data['valid_percentage'] < 73.0:
            variables_baja_completitud.append(var_name)
    
    print(f"Variables con <73% completitud: {len(variables_baja_completitud)}")
    
    # Eliminar variables con baja completitud
    if variables_baja_completitud:
        df = df.drop(columns=variables_baja_completitud)
        print(f"Variables eliminadas por baja completitud: {len(variables_baja_completitud)}")
    
    # 6. Eliminar variables relacionadas a COVID
    print("Eliminando variables relacionadas a COVID...")
    
    # Patrones para identificar variables COVID
    covid_patterns = [
        'covid', 'COVID', 'Corona', 'corona', 'SARS', 'sars',
        'vac', 'Vac', 'VAC', 'vacuna', 'Vacuna', 'dosis', 'Dosis',
        'positivo', 'Positivo', 'negativo', 'Negativo', 'PCR', 'pcr',
        'anticuerpo', 'Anticuerpo', 'serologia', 'Serologia',
        'sintoma', 'Sintoma', 'sintomas', 'Sintomas',
        'fiebre', 'Fiebre', 'tos', 'Tos', 'disnea', 'Disnea',
        'ageusia', 'Ageusia', 'anosmia', 'Anosmia',
        'cefalea', 'Cefalea', 'migraña', 'Migraña',
        'dolor', 'Dolor', 'fatiga', 'Fatiga', 'cansancio', 'Cansancio',
        'congestion', 'Congestion', 'rinorrea', 'Rinorrea',
        'odinofagia', 'Odinofagia', 'dolorgarganta', 'Dolorgarganta',
        'diarrea', 'Diarrea', 'vomito', 'Vomito', 'nauseas', 'Nauseas',
        'cuarentena', 'Cuarentena', 'aislamiento', 'Aislamiento',
        'hospital', 'Hospital', 'uci', 'UCI', 'terapia', 'Terapia',
        'oxigeno', 'Oxigeno', 'ventilacion', 'Ventilacion',
        'recuperacion', 'Recuperacion', 'secuela', 'Secuela',
        'mortalidad', 'Mortalidad', 'letalidad', 'Letalidad'
    ]
    
    # Identificar columnas relacionadas con COVID
    covid_cols = []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(pattern.lower() in col_lower for pattern in covid_patterns):
            covid_cols.append(col)
    
    print(f"Variables COVID identificadas: {len(covid_cols)}")
    
    # Eliminar variables COVID
    if covid_cols:
        df = df.drop(columns=covid_cols)
        print(f"Variables COVID eliminadas: {len(covid_cols)}")
    
    # 7. Resumen final
    original_cols = 648  # Número original de columnas
    print(f"\nRESUMEN DEL PREPROCESAMIENTO:")
    print(f"   Dimensiones finales: {df.shape[0]} filas × {df.shape[1]} columnas")
    print(f"   Filas eliminadas: {original_rows - len(df)}")
    print(f"   Columnas eliminadas: {original_cols - len(df.columns)}")
    
    # 8. Guardar si se especifica output_path
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
