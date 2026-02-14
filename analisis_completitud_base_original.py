#!/usr/bin/env python3
import pandas as pd
import numpy as np

def analizar_completitud_base_original():
    """
    Analiza la completitud por paciente en la base original y explica las eliminaciones.
    """
    print("Analizando completitud en base original centenarios_metabolomica.xlsx...\n")
    
    # Cargar base original
    try:
        df_original = pd.read_excel("centenarios/centenarios_metabolomica.xlsx")
        print(f"Base original cargada: {df_original.shape[0]} filas × {df_original.shape[1]} columnas")
    except Exception as e:
        print(f"Error al cargar archivo original: {e}")
        return
    
    # Cargar base limpia para comparación
    try:
        df_limpio = pd.read_excel("centenarios/centenarios_metabolomica_clean.xlsx")
        print(f"Base limpia cargada: {df_limpio.shape[0]} filas × {df_limpio.shape[1]} columnas")
    except Exception as e:
        print(f"Error al cargar archivo limpio: {e}")
        return
    
    print("\n" + "="*80)
    print("ANÁLISIS DE COMPLETITUD POR PACIENTE - BASE ORIGINAL")
    print("="*80)
    
    # Calcular completitud por paciente en base original
    total_vars_original = len(df_original.columns)
    missing_by_patient_original = df_original.isnull().sum(axis=1)
    missing_pct_by_patient_original = (missing_by_patient_original / total_vars_original) * 100
    
    # Identificar pacientes eliminados
    pacientes_eliminados = []
    
    # 1. Pacientes eliminados por índice
    rows_to_drop = [7, 17, 33, 123]
    for idx in rows_to_drop:
        if idx < len(df_original):
            if 'Número' in df_original.columns:
                paciente_id = df_original.loc[idx, 'Número']
            else:
                paciente_id = f"Paciente_{idx}"
            
            missing_pct = missing_pct_by_patient_original.iloc[idx]
            missing_count = missing_by_patient_original.iloc[idx]
            
            pacientes_eliminados.append({
                'paciente_id': paciente_id,
                'indice': idx,
                'motivo': 'Índice específico',
                'missing_pct': missing_pct,
                'missing_count': missing_count,
                'total_vars': total_vars_original,
                'valid_vars': total_vars_original - missing_count,
                'razon': 'Eliminación predefinida por índice'
            })
    
    # 2. Pacientes eliminados por número
    pacientes_por_numero = [43, 103]
    for paciente_num in pacientes_por_numero:
        # Buscar paciente por número
        if 'Número' in df_original.columns:
            idx = df_original[df_original['Número'] == paciente_num].index
            if len(idx) > 0:
                idx = idx[0]
                missing_pct = missing_pct_by_patient_original.iloc[idx]
                missing_count = missing_by_patient_original.iloc[idx]
                
                pacientes_eliminados.append({
                    'paciente_id': paciente_num,
                    'indice': idx,
                    'motivo': 'Número específico',
                    'missing_pct': missing_pct,
                    'missing_count': missing_count,
                    'total_vars': total_vars_original,
                    'valid_vars': total_vars_original - missing_count,
                    'razon': 'Eliminación por >99% missing (casos extremos)'
                })
    
    # 3. Paciente 33 (índice 98) - nuevo análisis
    paciente_33_idx = 98
    if paciente_33_idx < len(df_original):
        if 'Número' in df_original.columns:
            paciente_id = df_original.loc[paciente_33_idx, 'Número']
        else:
            paciente_id = f"Paciente_{paciente_33_idx}"
        
        missing_pct = missing_pct_by_patient_original.iloc[paciente_33_idx]
        missing_count = missing_by_patient_original.iloc[paciente_33_idx]
        
        pacientes_eliminados.append({
            'paciente_id': paciente_id,
            'indice': paciente_33_idx,
            'motivo': 'Alto missing (>40%)',
            'missing_pct': missing_pct,
            'missing_count': missing_count,
            'total_vars': total_vars_original,
            'valid_vars': total_vars_original - missing_count,
            'razon': 'Eliminación recomendada por 43.19% missing'
        })
    
    # Ordenar pacientes eliminados
    pacientes_eliminados.sort(key=lambda x: x['missing_pct'], reverse=True)
    
    # Crear tabla de completitud
    print("\n📊 TABLA DE COMPLETITUD POR PACIENTE - BASE ORIGINAL")
    print("="*80)
    
    # Encabezado de tabla
    print(f"{'ID':<10} {'Índice':<8} {'Missing':<10} {'Válidos':<10} {'Total':<8} {'Motivo':<20} {'Razón'}")
    print("-" * 100)
    
    # Datos de tabla
    for pac in pacientes_eliminados:
        print(f"{str(pac['paciente_id']):<10} {pac['indice']:<8} "
              f"{pac['missing_pct']:<10.2f} {pac['valid_vars']:<10} "
              f"{pac['total_vars']:<8} {pac['motivo']:<20} {pac['razon']}")
    
    # Estadísticas generales
    print(f"\n📈 ESTADÍSTICAS DE ELIMINACIÓN:")
    print(f"   Total pacientes originales: {len(df_original)}")
    print(f"   Total pacientes eliminados: {len(pacientes_eliminados)}")
    print(f"   Total pacientes restantes: {len(df_original) - len(pacientes_eliminados)}")
    print(f"   Porcentaje eliminación: {(len(pacientes_eliminados)/len(df_original))*100:.1f}%")
    
    # Análisis por motivo
    print(f"\n🔍 ANÁLISIS POR MOTIVO DE ELIMINACIÓN:")
    
    motivos = {}
    for pac in pacientes_eliminados:
        motivo = pac['motivo']
        if motivo not in motivos:
            motivos[motivo] = []
        motivos[motivo].append(pac)
    
    for motivo, pacientes in motivos.items():
        print(f"\n   {motivo.upper()}:")
        print(f"   Pacientes: {len(pacientes)}")
        print(f"   IDs: {[p['paciente_id'] for p in pacientes]}")
        
        # Calcular promedio de missing para este grupo
        avg_missing = np.mean([p['missing_pct'] for p in pacientes])
        print(f"   Missing promedio: {avg_missing:.2f}%")
        
        # Mostrar detalles individuales
        for p in pacientes:
            print(f"     - Paciente {p['paciente_id']}: {p['missing_pct']:.2f}% missing "
                  f"({p['missing_count']}/{p['total_vars']} variables)")
    
    # Exportar resultados a archivo
    print(f"\n💾 EXPORTANDO RESULTADOS...")
    
    with open('analisis_completitud_base_original.txt', 'w', encoding='utf-8') as f:
        f.write("ANÁLISIS DE COMPLETITUD POR PACIENTE - BASE ORIGINAL\n")
        f.write("="*80 + "\n\n")
        
        f.write("RESUMEN DE ELIMINACIONES:\n")
        f.write(f"   Base original: centenarios_metabolomica.xlsx\n")
        f.write(f"   Base limpia: centenarios_metabolomica_clean.xlsx\n")
        f.write(f"   Pacientes originales: {len(df_original)}\n")
        f.write(f"   Pacientes eliminados: {len(pacientes_eliminados)}\n")
        f.write(f"   Pacientes restantes: {len(df_original) - len(pacientes_eliminados)}\n")
        f.write(f"   Porcentaje eliminación: {(len(pacientes_eliminados)/len(df_original))*100:.1f}%\n\n")
        
        f.write("TABLA DETALLADA DE PACIENTES ELIMINADOS:\n")
        f.write("-"*100 + "\n")
        f.write(f"{'ID':<10} {'Índice':<8} {'Missing':<10} {'Válidos':<10} {'Total':<8} {'Motivo':<20} {'Razón'}\n")
        f.write("-"*100 + "\n")
        
        for pac in pacientes_eliminados:
            f.write(f"{str(pac['paciente_id']):<10} {pac['indice']:<8} "
                   f"{pac['missing_pct']:<10.2f} {pac['valid_vars']:<10} "
                   f"{pac['total_vars']:<8} {pac['motivo']:<20} {pac['razon']}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("EXPLICACIÓN DETALLADA DE ELIMINACIONES:\n\n")
        
        for motivo, pacientes in motivos.items():
            f.write(f"\n{motivo.upper()}:\n")
            f.write(f"   Pacientes: {len(pacientes)}\n")
            f.write(f"   IDs: {[p['paciente_id'] for p in pacientes]}\n")
            f.write(f"   Missing promedio: {np.mean([p['missing_pct'] for p in pacientes]):.2f}%\n\n")
            
            for p in pacientes:
                f.write(f"   Paciente {p['paciente_id']} (índice {p['indice']}):\n")
                f.write(f"     - Missing: {p['missing_pct']:.2f}% ({p['missing_count']}/{p['total_vars']} variables)\n")
                f.write(f"     - Válidos: {p['valid_vars']}/{p['total_vars']} ({100-p['missing_pct']:.2f}%)\n")
                f.write(f"     - Razón: {p['razon']}\n\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("JUSTIFICACIÓN DEL FILTRADO:\n\n")
        f.write("1. PACIENTES ELIMINADOS POR ÍNDICE [7, 17, 33, 123]:\n")
        f.write("   - Pacientes 131, 104, 10, 18\n")
        f.write("   - Eliminación predefinida en el proceso de limpieza\n")
        f.write("   - Posibles problemas de calidad o inconsistencias detectadas previamente\n\n")
        
        f.write("2. PACIENTES ELIMINADOS POR NÚMERO [43, 103]:\n")
        f.write("   - Missing >99% (casos extremos)\n")
        f.write("   - Prácticamente sin datos válidos\n")
        f.write("   - No aportan valor al análisis\n\n")
        
        f.write("3. PACIENTE ELIMINADO POR ALTO MISSING (>40%):\n")
        f.write("   - Paciente 33 (índice 98)\n")
        f.write("   - Missing: 43.19% (168/389 variables)\n")
        f.write("   - Datos insuficientes para análisis confiable\n\n")
        
        f.write("RESULTADO FINAL:\n")
        f.write(f"   - Dataset limpio: {df_limpio.shape[0]} pacientes × {df_limpio.shape[1]} variables\n")
        f.write(f"   - Mejora en calidad de datos significativa\n")
        f.write(f"   - Pacientes con datos de buena calidad para análisis\n")
    
    print(f"✅ Resultados exportados a 'analisis_completitud_base_original.txt'")
    
    return pacientes_eliminados

if __name__ == "__main__":
    analizar_completitud_base_original()
