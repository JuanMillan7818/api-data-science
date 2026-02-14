#!/usr/bin/env python3
import sys
import os

# Agregar ruta del servicio para poder importarlo
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.centenarios import CentenariosService

def analizar_missing_pacientes():
    """
    Ejecuta el análisis de missing por paciente.
    """
    print("Iniciando análisis de missing por paciente...\n")
    
    # Inicializar servicio
    service = CentenariosService()
    
    # Ejecutar análisis de missing por paciente
    resultados = service.analyze_missing_by_patient()
    
    # Generar histograma (opcional)
    try:
        service.plot_missing_by_patient()
    except:
        print("\nNo se pudo generar el histograma (matplotlib no disponible)")
    
    print(f"\n✅ Análisis completado")
    print(f"📊 Resultados clave:")
    print(f"   - Pacientes con >50% missing: {resultados['patients_above_50pct']}")
    print(f"   - Missing promedio: {resultados['mean_missing_pct']:.2f}%")
    print(f"   - Missing máximo: {resultados['max_missing_pct']:.2f}%")
    
    return resultados

if __name__ == "__main__":
    analizar_missing_pacientes()
