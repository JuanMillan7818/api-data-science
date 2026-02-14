#!/usr/bin/env python3
import sys
import os

# Agregar ruta del servicio para poder importarlo
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.centenarios import CentenariosService

def verificar_variables_dicc_vs_dataset():
    """
    Identifica qué variables del diccionario no existen en el dataset.
    """
    print("Verificando variables del diccionario vs dataset...\n")
    
    # Inicializar servicio
    service = CentenariosService()
    
    # Obtener variables del diccionario
    dict_vars_result = service.get_variables_from_dictionary()
    dict_vars = {v['variable'] for v in dict_vars_result}
    
    # Obtener variables del dataset
    dataset_vars = set(service.df_data.columns)
    
    # Variables del diccionario que NO existen en el dataset
    dict_not_in_dataset = dict_vars - dataset_vars
    
    # Variables del dataset que NO están en el diccionario
    dataset_not_in_dict = dataset_vars - dict_vars
    
    print("=" * 80)
    print("ANÁLISIS: VARIABLES DEL DICCIONARIO VS DATASET")
    print("=" * 80)
    
    print(f"\n📊 RESUMEN:")
    print(f"   Variables en diccionario: {len(dict_vars)}")
    print(f"   Variables en dataset: {len(dataset_vars)}")
    print(f"   Variables en ambos: {len(dict_vars & dataset_vars)}")
    print(f"   Diccionario no en dataset: {len(dict_not_in_dataset)}")
    print(f"   Dataset no en diccionario: {len(dataset_not_in_dict)}")
    
    print(f"\n🔍 VARIABLES DEL DICCIONARIO QUE NO EXISTEN EN EL DATASET ({len(dict_not_in_dataset)}):")
    for i, var in enumerate(sorted(dict_not_in_dataset), 1):
        print(f"   {i:3d}. {var}")
    
    print(f"\n📋 VARIABLES DEL DATASET QUE NO ESTÁN EN EL DICCIONARIO ({len(dataset_not_in_dict)}):")
    for i, var in enumerate(sorted(dataset_not_in_dict), 1):
        print(f"   {i:3d}. {var}")
    
    # Guardar resultados en archivos
    with open('variables_dicc_no_en_dataset.txt', 'w') as f:
        f.write("Variables del diccionario que NO existen en el dataset:\n\n")
        for var in sorted(dict_not_in_dataset):
            f.write(f"{var}\n")
    
    with open('variables_dataset_no_en_dicc.txt', 'w') as f:
        f.write("Variables del dataset que NO están en el diccionario:\n\n")
        for var in sorted(dataset_not_in_dict):
            f.write(f"{var}\n")
    
    print(f"\n💾 Archivos generados:")
    print(f"   - variables_dicc_no_en_dataset.txt ({len(dict_not_in_dataset)} variables)")
    print(f"   - variables_dataset_no_en_dicc.txt ({len(dataset_not_in_dict)} variables)")
    
    return {
        'dict_vars_count': len(dict_vars),
        'dataset_vars_count': len(dataset_vars),
        'dict_not_in_dataset': sorted(dict_not_in_dataset),
        'dataset_not_in_dict': sorted(dataset_not_in_dict),
        'dict_not_in_dataset_count': len(dict_not_in_dataset),
        'dataset_not_in_dict_count': len(dataset_not_in_dict)
    }

if __name__ == "__main__":
    verificar_variables_dicc_vs_dataset()
