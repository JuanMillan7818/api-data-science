#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from app.services.centenarios import CentenariosService

def comparar_variables():
    """
    Compara variables entre el dataset y el diccionario.
    """
    print("Analizando variables...\n")
    
    # Inicializar servicio
    service = CentenariosService()
    
    # Obtener variables del dataset
    dataset_vars = set(service.df_data.columns)
    print(f"Variables en dataset: {len(dataset_vars)}")
    
    # Obtener variables del diccionario
    dict_vars_result = service.get_variables_from_dictionary()
    dict_vars = {v['variable'] for v in dict_vars_result}
    print(f"Variables en diccionario: {len(dict_vars)}")
    
    # Variables en dataset pero NO en diccionario
    solo_dataset = sorted(dataset_vars - dict_vars)
    print(f"\nVariables SOLO en dataset ({len(solo_dataset)}):")
    for var in solo_dataset:
        print(f"  - {var}")
    
    # Variables en diccionario pero NO en dataset
    solo_diccionario = sorted(dict_vars - dataset_vars)
    print(f"\nVariables SOLO en diccionario ({len(solo_diccionario)}):")
    for var in solo_diccionario:
        print(f"  - {var}")
    
    # Variables en ambos
    en_ambos = sorted(dataset_vars & dict_vars)
    print(f"\nVariables en AMBOS ({len(en_ambos)}):")
    print(f"  Total: {len(en_ambos)} variables")
    
    # Guardar resultados en archivos
    with open('variables_solo_dataset.txt', 'w') as f:
        f.write("Variables que están en el dataset pero NO en el diccionario:\n\n")
        for var in solo_dataset:
            f.write(f"{var}\n")
    
    with open('variables_solo_diccionario.txt', 'w') as f:
        f.write("Variables que están en el diccionario pero NO en el dataset:\n\n")
        for var in solo_diccionario:
            f.write(f"{var}\n")
    
    print(f"\nResultados guardados en:")
    print(f"  - variables_solo_dataset.txt ({len(solo_dataset)} variables)")
    print(f"  - variables_solo_diccionario.txt ({len(solo_diccionario)} variables)")

if __name__ == "__main__":
    comparar_variables()
