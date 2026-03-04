#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script que simula la misma lógica que usa CentenariosService
Carga el archivo completo y calcula completeness_map como el servicio
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Agregar ruta del servicio para poder importarlo
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def simular_completitud():
    """
    Simula la lógica de CentenariosService cargando archivo completo
    """
    print("🔍 SIMULANDO LÓGICA DE COMPLETITUD")
    print("📁 Cargando archivo completo directamente...")
    
    # Cargar el archivo completo como lo hace el servicio
    excel_file = "/Users/natali/api-data-science/centenarios/CENTENARIOS_COMPLETO_PRE.xlsx"
    
    try:
        # Cargar con header=1 (ignorar primera fila)
        df_data = pd.read_excel(excel_file, header=1)
        print(f"   ✅ Archivo cargado: {df_data.shape[0]} filas × {df_data.shape[1]} columnas")
        
        # Calcular completeness_map exactamente como el servicio
        completeness_map = {}
        total_rows = len(df_data)
        
        print(f"\n📊 Calculando completitud para {total_rows} pacientes y {df_data.shape[1]} variables...")
        
        for col in df_data.columns:
            non_null = int(df_data[col].count())
            null_count = total_rows - non_null
            pct = (non_null / total_rows) * 100 if total_rows > 0 else 0.0
            
            completeness_map[col] = {
                "valid_percentage": pct,
                "null_count": null_count,
                "non_null_count": non_null,
                "total_rows": total_rows
            }
        
        print(f"   ✅ Completitud calculada para {len(completeness_map)} variables")
        
        # Identificar pacientes problemáticos
        pacientes_problematicos = []
        ids_30pct = []
        ids_50pct = []
        
        for idx, patient in df_data.iterrows():
            # Calcular completitud por paciente
            total_vars = len(patient)
            datos_validos = patient.count()
            datos_missing = total_vars - datos_validos
            pct_missing = (datos_missing / total_vars) * 100 if total_vars > 0 else 0.0
            
            # Clasificar paciente
            if pct_missing >= 40:  # ALTO
                categoria = "ALTO"
                nivel_alerta = "🚨"
                problema = "COMPLETITUD ALTA (>40%)"
            elif pct_missing >= 20:  # MEDIO
                categoria = "MEDIO"
                nivel_alerta = "⚠️"
                problema = "COMPLETITUD MEDIA (20-40%)"
            elif pct_missing >= 5:  # BAJO
                categoria = "BAJO"
                nivel_alerta = "📋"
                problema = "COMPLETITUD BAJA (<5%)"
            else:
                categoria = "ACEPTABLE"
                nivel_alerta = "✅"
                problema = None
            
            # Identificar paciente (priorizar cédula)
            paciente_id = None
            id_columns = ['Cedula', 'CEDULA', 'Cédula', 'Número', 'Numero']
            
            for col in id_columns:
                if col in df_data.columns:
                    paciente_id = patient[col]
                    if pd.notna(paciente_id):
                        break
            
            if paciente_id is None or pd.isna(paciente_id):
                if 'Número' in df_data.columns:
                    paciente_id = patient['Número']
                else:
                    paciente_id = f"Paciente_{idx}"
            else:
                # Convertir a string si es tipo pandas
                if hasattr(paciente_id, 'item'):
                    paciente_id = paciente_id.item()
                paciente_id = str(paciente_id)
            
            # Clasificar como problemático
            if categoria != "ACEPTABLE":
                pacientes_problematicos.append({
                    'indice': idx,
                    'cedula': paciente_id,
                    'categoria_completitud': categoria,
                    'pct_missing': round(pct_missing, 2),
                    'total_variables': total_vars,
                    'datos_validos': datos_validos,
                    'datos_missing': datos_missing,
                    'nivel_alerta': nivel_alerta,
                    'variables_missing': [],
                    'problema': problema
                })
                
                # Contar por categoría
                if pct_missing >= 40:
                    ids_50pct.append(paciente_id)
                elif pct_missing >= 20:
                    ids_30pct.append(paciente_id)
        
        # Estadísticas generales
        total_pacientes = len(df_data)
        pct_bajo = len([p for p in pacientes_problematicos if p['categoria_completitud'] == 'BAJO'])
        pct_medio = len([p for p in pacientes_problematicos if p['categoria_completitud'] == 'MEDIO'])
        pct_alto = len([p for p in pacientes_problematicos if p['categoria_completitud'] == 'ALTO'])
        
        print(f"\n📈 ESTADÍSTICAS GENERALES:")
        print(f"   Total pacientes: {total_pacientes}")
        print(f"   Pacientes problemáticos: {len(pacientes_problematicos)} ({len(pacientes_problematicos)/total_pacientes*100:.1f}%)")
        print(f"   - Completitud BAJA: {pct_bajo} ({pct_bajo/total_pacientes*100:.1f}%)")
        print(f"   - Completitud MEDIA: {pct_medio} ({pct_medio/total_pacientes*100:.1f}%)")
        print(f"   - Completitud ALTA: {pct_alto} ({pct_alto/total_pacientes*100:.1f}%)")
        
        # Mostrar pacientes problemáticos con sus detalles
        print(f"\n📋 PACIENTES PROBLEMÁTICOS DETALLADOS:")
        for i, paciente in enumerate(pacientes_problematicos[:10], 1):
            print(f"{i:2d}. {paciente['cedula']} - {paciente['problema']}")
            print(f"     Missing: {paciente['pct_missing']}%")
            
            if i < len(pacientes_problematicos):
                print(f"     Variables con missing: {len(paciente['variables_missing'])}")
                for j, var in enumerate(paciente['variables_missing'][:5], 1):
                    print(f"       {j+1}. {var}")
                if len(paciente['variables_missing']) > 5:
                    print(f"       ... y {len(paciente['variables_missing'])-5} más")
        
        # Generar archivos
        with open('simulacion_pacientes.txt', 'w', encoding='utf-8') as f:
            f.write("SIMULACIÓN DE COMPLETITUD DE PACIENTES\n")
            f.write("=" * 60)
            f.write(f"Fecha: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Archivo: {excel_file}\n")
            f.write(f"Pacientes totales: {total_pacientes}\n")
            f.write(f"Variables analizadas: {df_data.shape[1]}\n")
            f.write(f"Pacientes problemáticos: {len(pacientes_problematicos)}\n")
            f.write(f"   - BAJA: {pct_bajo} ({pct_bajo/total_pacientes*100:.1f}%)\n")
            f.write(f"   - MEDIO: {pct_medio} ({pct_medio/total_pacientes*100:.1f}%)\n")
            f.write(f"   - ALTO: {pct_alto} ({pct_alto/total_pacientes*100:.1f}%)\n")
            
            f.write("\nDETALLE DE PACIENTES PROBLEMÁTICOS:\n")
            for i, paciente in enumerate(pacientes_problematicos, 1):
                f.write(f"{i+1}. {paciente['cedula']} - {paciente['problema']} - {paciente['pct_missing']}%\n")
                if len(paciente['variables_missing']) > 0:
                    f.write(f"   Variables: {', '.join(paciente['variables_missing'])}\n")
        
        print(f"\n✅ Simulación completada. Reporte guardado en: simulacion_pacientes.txt")
    
    return {
        'total_pacientes': total_pacientes,
        'pacientes_problematicos': pacientes_problematicos,
        'completeness_map': completeness_map
    }
    
    except Exception as e:
        print(f"❌ Error en la simulación: {str(e)}")
        return {
            'total_pacientes': 0,
            'pacientes_problematicos': [],
            'completeness_map': {},
            'error': str(e)
        }

if __name__ == "__main__":
    simulacion_completitud()
