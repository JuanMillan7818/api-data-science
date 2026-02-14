#!/usr/bin/env python3
import sys
import os

# Agregar ruta del servicio para poder importarlo
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.centenarios import CentenariosService

def obtener_detalles_pacientes_problematicos():
    """
    Obtiene detalles completos de los pacientes con >30% y >50% missing.
    """
    print("Obteniendo detalles de pacientes problemáticos...\n")
    
    # Inicializar servicio
    service = CentenariosService()
    
    # Ejecutar análisis de missing por paciente
    resultados = service.analyze_missing_by_patient()
    
    # IDs de pacientes problemáticos
    ids_30pct = []
    ids_50pct = []
    
    # Obtener detalles de pacientes con >30% missing
    missing_by_patient = service.df_data.isnull().sum(axis=1)
    total_columns = len(service.df_data.columns)
    missing_pct_by_patient = (missing_by_patient / total_columns) * 100
    
    pacientes_30pct = missing_pct_by_patient[missing_pct_by_patient > 30]
    pacientes_50pct = missing_pct_by_patient[missing_pct_by_patient > 50]
    
    print("=" * 80)
    print("DETALLE DE PACIENTES CON >30% MISSING")
    print("=" * 80)
    
    for idx, missing_pct in pacientes_30pct.items():
        if 'Número' in service.df_data.columns:
            paciente_id = service.df_data.loc[idx, 'Número']
        else:
            paciente_id = f"Paciente_{idx}"
        
        ids_30pct.append(paciente_id)
        
        print(f"\nPaciente ID: {paciente_id}")
        print(f"  Índice: {idx}")
        print(f"  Missing: {missing_pct:.2f}%")
        print(f"  Datos válidos: {100 - missing_pct:.2f}%")
        
        # Mostrar primeras 10 variables con missing para este paciente
        paciente_data = service.df_data.loc[idx]
        missing_vars = paciente_data[paciente_data.isnull()].index.tolist()
        
        print(f"  Variables con missing ({len(missing_vars)}): {missing_vars[:10]}{'...' if len(missing_vars) > 10 else ''}")
        print("-" * 50)
    
    print(f"\nTotal pacientes con >30% missing: {len(pacientes_30pct)}")
    print(f"IDs: {ids_30pct}")
    
    print("\n" + "=" * 80)
    print("DETALLE DE PACIENTES CON >50% MISSING")
    print("=" * 80)
    
    for idx, missing_pct in pacientes_50pct.items():
        if 'Número' in service.df_data.columns:
            paciente_id = service.df_data.loc[idx, 'Número']
        else:
            paciente_id = f"Paciente_{idx}"
        
        ids_50pct.append(paciente_id)
        
        print(f"\nPaciente ID: {paciente_id}")
        print(f"  Índice: {idx}")
        print(f"  Missing: {missing_pct:.2f}%")
        print(f"  Datos válidos: {100 - missing_pct:.2f}%")
        
        # Mostrar todas las variables con missing para este paciente
        paciente_data = service.df_data.loc[idx]
        missing_vars = paciente_data[paciente_data.isnull()].index.tolist()
        
        print(f"  Variables con missing ({len(missing_vars)}):")
        for var in missing_vars:
            print(f"    - {var}")
        print("-" * 50)
    
    print(f"\nTotal pacientes con >50% missing: {len(pacientes_50pct)}")
    print(f"IDs: {ids_50pct}")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)
    print(f"Pacientes con >30% missing: {len(ids_30pct)}")
    print(f"Pacientes con >50% missing: {len(ids_50pct)}")
    print(f"IDs >30%: {ids_30pct}")
    print(f"IDs >50%: {ids_50pct}")
    
    # Guardar IDs en archivos
    with open('pacientes_30pct_missing.txt', 'w') as f:
        f.write("Pacientes con >30% missing:\n\n")
        for pid in ids_30pct:
            f.write(f"{pid}\n")
    
    with open('pacientes_50pct_missing.txt', 'w') as f:
        f.write("Pacientes con >50% missing:\n\n")
        for pid in ids_50pct:
            f.write(f"{pid}\n")
    
    print(f"\nArchivos generados:")
    print(f"  - pacientes_30pct_missing.txt ({len(ids_30pct)} IDs)")
    print(f"  - pacientes_50pct_missing.txt ({len(ids_50pct)} IDs)")

if __name__ == "__main__":
    obtener_detalles_pacientes_problematicos()
