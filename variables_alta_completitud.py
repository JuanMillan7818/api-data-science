#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from app.services.centenarios import CentenariosService

def obtener_variables_alta_completitud():
    """
    Obtiene lista de variables con 72.2% o mas de completitud.
    """
    print("Analizando completitud de variables...\n")
    
    # Inicializar servicio
    service = CentenariosService()
    
    # Obtener todas las variables
    all_vars = service.get_all_variables()
    print(f"Total variables analizadas: {len(all_vars)}")
    
    # Filtrar variables con 72.2% o mas de completitud
    umbral = 70
    variables_filtradas = []
    
    for var in all_vars:
        completitud = var.get('valid_percentage', 0.0)
        if completitud >= umbral:
            variables_filtradas.append(var)
    
    # Ordenar por completitud descendente
    variables_filtradas.sort(key=lambda x: x['valid_percentage'], reverse=True)
    
    print(f"\nVariables con {umbral}% o mas de completitud: {len(variables_filtradas)}")
    print("=" * 60)
    
    # Mostrar resultados
    for i, var in enumerate(variables_filtradas, 1):
        print(f"{i:3d}. {var['variable']:25s} - {var['valid_percentage']:6.2f}% - {var['dtype']}")
    
    # Guardar en archivo
    with open('variables_72_2_percent_completitud.txt', 'w') as f:
        f.write(f"Variables con {umbral}% o mas de completitud ({len(variables_filtradas)}):\n\n")
        f.write("Variable".ljust(30) + "Completitud".ljust(15) + "Tipo\n")
        f.write("-" * 60 + "\n")
        
        for var in variables_filtradas:
            f.write(f"{var['variable']:<30} {var['valid_percentage']:>15.2f}% {var['dtype']}\n")
    
    # Estadisticas adicionales
    if variables_filtradas:
        avg_completitud = sum(v['valid_percentage'] for v in variables_filtradas) / len(variables_filtradas)
        max_completitud = max(v['valid_percentage'] for v in variables_filtradas)
        min_completitud = min(v['valid_percentage'] for v in variables_filtradas)
        
        print(f"\nEstadisticas:")
        print(f"  Promedio completitud: {avg_completitud:.2f}%")
        print(f"  Completitud maxima: {max_completitud:.2f}%")
        print(f"  Completitud minima: {min_completitud:.2f}%")
        
        # Por tipo
        tipos = {}
        for var in variables_filtradas:
            tipo = var['dtype']
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        print(f"\nDistribucion por tipo:")
        for tipo, count in tipos.items():
            print(f"  {tipo}: {count} variables")
    
    print(f"\nResultados guardados en: variables_72_2_percent_completitud.txt")

if __name__ == "__main__":
    obtener_variables_alta_completitud()
