#!/usr/bin/env python3
import sys
import os
import pandas as pd
import numpy as np

# Agregar ruta del servicio para poder importarlo
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.centenarios import CentenariosService

def analizar_impacto_eliminacion():
    """
    Analiza el impacto en los porcentajes de missing de variables si eliminamos
    todos los pacientes con >20% missing.
    """
    print("Analizando impacto de eliminación de pacientes con >20% missing...\n")
    
    # Inicializar servicio
    service = CentenariosService()
    
    print("=" * 80)
    print("ANÁLISIS DE IMPACTO DE ELIMINACIÓN")
    print("=" * 80)
    
    # Dataset actual
    df_actual = service.df_data.copy()
    print(f"Dataset actual: {df_actual.shape[0]} pacientes × {df_actual.shape[1]} variables")
    
    # Identificar pacientes con >20% missing
    missing_by_patient = df_actual.isnull().sum(axis=1)
    total_columns = len(df_actual.columns)
    missing_pct_by_patient = (missing_by_patient / total_columns) * 100
    
    pacientes_alto_missing = missing_pct_by_patient[missing_pct_by_patient > 20]
    
    print(f"\nPacientes con >20% missing: {len(pacientes_alto_missing)}")
    
    # Obtener detalles de pacientes a eliminar
    pacientes_eliminar = []
    for idx, missing_pct in pacientes_alto_missing.items():
        if 'Número' in df_actual.columns:
            paciente_id = df_actual.loc[idx, 'Número']
        else:
            paciente_id = f"Paciente_{idx}"
        
        pacientes_eliminar.append({
            'indice': idx,
            'numero': paciente_id,
            'missing_pct': missing_pct,
            'missing_count': missing_by_patient[idx]
        })
    
    # Ordenar por missing descendente
    pacientes_eliminar.sort(key=lambda x: x['missing_pct'], reverse=True)
    
    print("\nPacientes a eliminar:")
    for i, pac in enumerate(pacientes_eliminar, 1):
        print(f"{i}. Paciente {pac['numero']} (índice {pac['indice']}): {pac['missing_pct']:.2f}% missing")
    
    # Crear dataset sin estos pacientes
    indices_eliminar = [pac['indice'] for pac in pacientes_eliminar]
    df_filtrado = df_actual.drop(indices_eliminar)
    
    print(f"\nDataset filtrado: {df_filtrado.shape[0]} pacientes × {df_filtrado.shape[1]} variables")
    print(f"Pacientes eliminados: {len(pacientes_eliminar)}")
    print(f"Porcentaje eliminación: {(len(pacientes_eliminar)/len(df_actual))*100:.1f}%")
    
    # Calcular completitud de variables antes y después
    print("\n" + "=" * 80)
    print("COMPARACIÓN DE COMPLETITUD DE VARIABLES")
    print("=" * 80)
    
    # Completitud actual
    completitud_actual = (df_actual.count() / len(df_actual)) * 100
    completitud_filtrada = (df_filtrado.count() / len(df_filtrado)) * 100
    
    # Crear DataFrame de comparación
    comparacion = pd.DataFrame({
        'Variable': df_actual.columns,
        'Completitud_Actual': completitud_actual,
        'Completitud_Filtrada': completitud_filtrada,
        'Diferencia': completitud_filtrada - completitud_actual,
        'Mejora_Porcentual': ((completitud_filtrada - completitud_actual) / completitud_actual) * 100
    })
    
    # Ordenar por mayor mejora
    comparacion = comparacion.sort_values('Diferencia', ascending=False)
    
    # Estadísticas generales
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"   Completitud promedio actual: {completitud_actual.mean():.2f}%")
    print(f"   Completitud promedio filtrada: {completitud_filtrada.mean():.2f}%")
    print(f"   Mejora promedio: {comparacion['Diferencia'].mean():.2f}%")
    print(f"   Mejora máxima: {comparacion['Diferencia'].max():.2f}%")
    print(f"   Variables con mejora: {(comparacion['Diferencia'] > 0).sum()}")
    print(f"   Variables sin cambio: {(comparacion['Diferencia'] == 0).sum()}")
    
    # Variables con mayor mejora
    print(f"\n🔝 VARIABLES CON MAYOR MEJORA (>5%):")
    variables_mejora = comparacion[comparacion['Diferencia'] > 5]
    if len(variables_mejora) > 0:
        for i, (_, row) in enumerate(variables_mejora.head(10).iterrows(), 1):
            print(f"{i:2d}. {row['Variable']}: {row['Completitud_Actual']:.2f}% → {row['Completitud_Filtrada']:.2f}% "
                  f"(+{row['Diferencia']:.2f}%)")
    else:
        print("   Ninguna variable mejora más del 5%")
    
    # Variables que empeoran
    print(f"\n⚠️  VARIABLES QUE EMPEORAN:")
    variables_empeoran = comparacion[comparacion['Diferencia'] < 0]
    if len(variables_empeoran) > 0:
        for i, (_, row) in enumerate(variables_empeoran.head(10).iterrows(), 1):
            print(f"{i:2d}. {row['Variable']}: {row['Completitud_Actual']:.2f}% → {row['Completitud_Filtrada']:.2f}% "
                  f"({row['Diferencia']:.2f}%)")
    else:
        print("   Ninguna variable empeora")
    
    # Análisis por rangos de completitud
    print(f"\n📈 DISTRIBUCIÓN POR RANGOS DE COMPLETITUD:")
    
    rangos = [
        (0, 50, "Muy baja"),
        (50, 70, "Baja"),
        (70, 85, "Media"),
        (85, 95, "Alta"),
        (95, 100, "Muy alta")
    ]
    
    for min_rango, max_rango, nombre in rangos:
        vars_actual = ((completitud_actual >= min_rango) & (completitud_actual < max_rango)).sum()
        vars_filtrada = ((completitud_filtrada >= min_rango) & (completitud_filtrada < max_rango)).sum()
        cambio = vars_filtrada - vars_actual
        
        print(f"   {nombre} ({min_rango}-{max_rango}%): {vars_actual} → {vars_filtrada} "
              f"({cambio:+d} variables)")
    
    # Exportar resultados
    print(f"\n💾 EXPORTANDO RESULTADOS...")
    
    with open('analisis_impacto_eliminacion.txt', 'w', encoding='utf-8') as f:
        f.write("ANÁLISIS DE IMPACTO DE ELIMINACIÓN DE PACIENTES CON >20% MISSING\n")
        f.write("="*80 + "\n\n")
        
        f.write("RESUMEN GENERAL:\n")
        f.write(f"   Dataset actual: {df_actual.shape[0]} pacientes × {df_actual.shape[1]} variables\n")
        f.write(f"   Dataset filtrado: {df_filtrado.shape[0]} pacientes × {df_filtrado.shape[1]} variables\n")
        f.write(f"   Pacientes eliminados: {len(pacientes_eliminar)}\n")
        f.write(f"   Porcentaje eliminación: {(len(pacientes_eliminar)/len(df_actual))*100:.1f}%\n\n")
        
        f.write("PACIENTES ELIMINADOS:\n")
        for i, pac in enumerate(pacientes_eliminar, 1):
            f.write(f"   {i}. Paciente {pac['numero']} (índice {pac['indice']}): {pac['missing_pct']:.2f}% missing\n")
        
        f.write("\nESTADÍSTICAS DE COMPLETITUD:\n")
        f.write(f"   Completitud promedio actual: {completitud_actual.mean():.2f}%\n")
        f.write(f"   Completitud promedio filtrada: {completitud_filtrada.mean():.2f}%\n")
        f.write(f"   Mejora promedio: {comparacion['Diferencia'].mean():.2f}%\n")
        f.write(f"   Variables con mejora: {(comparacion['Diferencia'] > 0).sum()}\n")
        f.write(f"   Variables sin cambio: {(comparacion['Diferencia'] == 0).sum()}\n")
        
        f.write("\nTOP 20 VARIABLES CON MAYOR MEJORA:\n")
        f.write("-"*100 + "\n")
        f.write(f"{'Variable':<30} {'Actual':<10} {'Filtrada':<10} {'Diferencia':<12} {'Mejora %'}\n")
        f.write("-"*100 + "\n")
        
        for i, (_, row) in enumerate(comparacion.head(20).iterrows(), 1):
            f.write(f"{row['Variable']:<30} {row['Completitud_Actual']:<10.2f} "
                   f"{row['Completitud_Filtrada']:<10.2f} {row['Diferencia']:<12.2f} "
                   f"{row['Mejora_Porcentual']:<10.2f}\n")
        
        f.write("\nDISTRIBUCIÓN POR RANGOS DE COMPLETITUD:\n")
        for min_rango, max_rango, nombre in rangos:
            vars_actual = ((completitud_actual >= min_rango) & (completitud_actual < max_rango)).sum()
            vars_filtrada = ((completitud_filtrada >= min_rango) & (completitud_filtrada < max_rango)).sum()
            cambio = vars_filtrada - vars_actual
            
            f.write(f"   {nombre} ({min_rango}-{max_rango}%): {vars_actual} → {vars_filtrada} "
                   f"({cambio:+d} variables)\n")
        
        f.write("\nCONCLUSIÓN:\n")
        if comparacion['Diferencia'].mean() > 1:
            f.write("   La eliminación de pacientes con >20% missing mejora significativamente\n")
            f.write("   la calidad general de los datos. Se recomienda proceder con el filtrado.\n")
        elif comparacion['Diferencia'].mean() > 0.5:
            f.write("   La eliminación mejora moderadamente la calidad de los datos.\n")
            f.write("   Considerar el filtrado según los objetivos del análisis.\n")
        else:
            f.write("   La eliminación tiene un impacto mínimo en la calidad de los datos.\n")
            f.write("   Evaluar si el filtrado justifica la pérdida de pacientes.\n")
    
    print(f"✅ Resultados exportados a 'analisis_impacto_eliminacion.txt'")
    
    return {
        'pacientes_eliminar': pacientes_eliminar,
        'comparacion': comparacion,
        'mejora_promedio': comparacion['Diferencia'].mean(),
        'variables_mejora': (comparacion['Diferencia'] > 0).sum()
    }

if __name__ == "__main__":
    analizar_impacto_eliminacion()
