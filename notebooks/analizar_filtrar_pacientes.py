#!/usr/bin/env python3
import sys
import os
import pandas as pd

# Agregar ruta del servicio para poder importarlo
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.centenarios import CentenariosService

def analizar_y_filtrar_pacientes():
    """
    Analiza el missing por paciente y sugiere qué filas eliminar.
    """
    print("Analizando missing por paciente y sugiriendo filtrado...\n")
    
    # Inicializar servicio
    service = CentenariosService()
    
    # Ejecutar análisis de missing por paciente
    resultados = service.analyze_missing_by_patient()
    
    print("=" * 80)
    print("ANÁLISIS DE MISSING POR PACIENTE")
    print("=" * 80)
    
    # Obtener detalles de pacientes con >20% missing
    missing_by_patient = service.df_data.isnull().sum(axis=1)
    total_columns = len(service.df_data.columns)
    missing_pct_by_patient = (missing_by_patient / total_columns) * 100
    
    pacientes_alto_missing = missing_pct_by_patient[missing_pct_by_patient > 20]
    
    print(f"\nPacientes con >20% missing: {len(pacientes_alto_missing)}")
    print("\nDetalles de pacientes con >20% missing:")
    
    # Obtener número de paciente si existe la columna
    pacientes_detalles = []
    for idx, missing_pct in pacientes_alto_missing.items():
        if 'Número' in service.df_data.columns:
            paciente_id = service.df_data.loc[idx, 'Número']
        else:
            paciente_id = f"Paciente_{idx}"
        
        pacientes_detalles.append({
            'indice': idx,
            'numero': paciente_id,
            'missing_pct': missing_pct,
            'missing_count': missing_by_patient[idx],
            'total_vars': total_columns,
            'valid_vars': total_columns - missing_by_patient[idx]
        })
    
    # Ordenar por missing descendente
    pacientes_detalles.sort(key=lambda x: x['missing_pct'], reverse=True)
    
    # Mostrar detalles
    for i, pac in enumerate(pacientes_detalles, 1):
        print(f"{i:2d}. Paciente {pac['numero']} (índice {pac['indice']})")
        print(f"    Missing: {pac['missing_pct']:.2f}% ({pac['missing_count']}/{pac['total_vars']})")
        print(f"    Válidos: {pac['valid_vars']}/{pac['total_vars']} ({100-pac['missing_pct']:.2f}%)")
        print()
    
    # Sugerencias de filtrado
    print("\n" + "=" * 80)
    print("SUGERENCIAS DE FILTRADO")
    print("=" * 80)
    
    # Criterios sugeridos
    criterios = [
        {
            'descripcion': 'Missing extremo (>50%)',
            'criterio': 'missing_pct > 50',
            'pacientes': [p for p in pacientes_detalles if p['missing_pct'] > 50],
            'accion': 'Eliminar - Pacientes con datos casi nulos',
            'razon': 'No aportan valor al análisis'
        },
        {
            'descripcion': 'Missing alto (>30-50%)',
            'criterio': '30 < missing_pct <= 50',
            'pacientes': [p for p in pacientes_detalles if 30 < p['missing_pct'] <= 50],
            'accion': 'Evaluar caso por caso - Revisar si hay patrón sistemático',
            'razon': 'Pueden tener problemas específicos de recolección'
        },
        {
            'descripcion': 'Missing moderado (>20-30%)',
            'criterio': '20 < missing_pct <= 30',
            'pacientes': [p for p in pacientes_detalles if 20 < p['missing_pct'] <= 30],
            'accion': 'Considerar mantener - Revisar calidad de datos',
            'razon': 'Pueden ser válidos pero con limitaciones'
        },
        {
            'descripcion': 'Missing bajo (<=20%)',
            'criterio': 'missing_pct <= 20',
            'pacientes': [p for p in pacientes_detalles if p['missing_pct'] <= 20],
            'accion': 'Mantener - Pacientes con datos aceptables',
            'razon': 'Calidad de datos adecuada'
        }
    ]
    
    # Mostrar sugerencias
    for criterio in criterios:
        print(f"\n{criterio['descripcion'].upper()}:")
        print(f"  Pacientes: {len(criterio['pacientes'])}")
        print(f"  Acción: {criterio['accion']}")
        print(f"  Razón: {criterio['razon']}")
        if criterio['pacientes']:
            print(f"  IDs: {[p['numero'] for p in criterio['pacientes']]}")
    
    # Generar script de filtrado
    print("\n" + "=" * 80)
    print("SCRIPT DE FILTRADO SUGERIDO")
    print("=" * 80)
    
    print("\n# Filas a eliminar (agregar a preprocess_centenarios.py):")
    print("rows_to_drop = [7, 17, 33, 123]  # Existentes")
    
    # Agregar filas con >50% missing
    filas_extremas = [p['indice'] for p in pacientes_detalles if p['missing_pct'] > 50]
    if filas_extremas:
        print(f"# Agregar filas con >50% missing: {filas_extremas}")
        print("rows_to_drop.extend(filas_extremas)")
    else:
        print("# No hay filas con >50% missing")
    
    # Agregar filas con >30% missing (opcional)
    filas_altas = [p['indice'] for p in pacientes_detalles if 30 < p['missing_pct'] <= 50]
    if filas_altas:
        print(f"\n# Opcional: filas con 30-50% missing: {filas_altas}")
        print("# rows_to_drop.extend(filas_altas)  # Descomentar si se desea eliminar")
    else:
        print("\n# No hay filas con 30-50% missing")
    
    # Generar lista final de filas a eliminar
    print("\n# Lista completa de filas a eliminar:")
    print("filas_a_eliminar = [7, 17, 33, 123]")
    if filas_extremas:
        print(f"filas_a_eliminar.extend({filas_extremas})")
    if filas_altas:
        print(f"filas_a_eliminar.extend({filas_altas})")
    
    print(f"\n# Total filas a eliminar: {len([7, 17, 33, 123] + filas_extremas + filas_altas)}")
    
    # Estadísticas finales
    total_pacientes = len(service.df_data)
    pacientes_filtrados = len([7, 17, 33, 123] + filas_extremas + filas_altas)
    pacientes_restantes = total_pacientes - pacientes_filtrados
    
    print(f"\n# Estadísticas finales:")
    print(f"# Total original: {total_pacientes} pacientes")
    print(f"# Total filtrados: {pacientes_filtrados} pacientes")
    print(f"# Total restantes: {pacientes_restantes} pacientes")
    print(f"# Porcentaje filtrado: {(pacientes_filtrados/total_pacientes)*100:.1f}%")
    
    return {
        'total_pacientes': total_pacientes,
        'pacientes_filtrados': pacientes_filtrados,
        'pacientes_restantes': pacientes_restantes,
        'filas_extremas': filas_extremas,
        'filas_altas': filas_altas,
        'detalles_pacientes': pacientes_detalles
    }

if __name__ == "__main__":
    analizar_y_filtrar_pacientes()
