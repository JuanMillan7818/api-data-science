import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font

# Importar el servicio para usar la misma lógica que la API
sys.path.append(str(Path(__file__).parent))
from app.services.centenarios import CentenariosService

class OutlierDetector:
    def __init__(self, dataset_path):
        self.dataset_path = Path(dataset_path)
        self.data = None
        self.outliers_dict = {}
        self.numeric_cols = []
        
    def load_data(self):
        """Carga el dataset con header=1 como el servicio"""
        try:
            print(f"Cargando dataset: {self.dataset_path}")
            # Cargar con header=1 como lo hace el servicio
            self.data = pd.read_excel(self.dataset_path, header=1)
            print(f"Dataset cargado: {len(self.data)} filas, {len(self.data.columns)} columnas")
            return True
        except Exception as e:
            print(f"Error cargando dataset: {str(e)}")
            return False
    
    def detect_outliers(self):
        """Detecta outliers en variables numéricas usando la misma lógica que la API"""
        if self.data is None:
            print("❌ Error: Dataset no cargado")
            return
        
        # Usar el servicio para obtener las variables numéricas como lo hace la API
        print("🔧 Usando la misma lógica que /api/v1/graph/numeric/stats...")
        
        # Crear una instancia del servicio (usará el dataset ya cargado)
        service = CentenariosService()
        service.df_data = self.data  # Usar nuestros datos ya cargados
        
        # Obtener variables numéricas como lo hace el endpoint numeric/stats
        numeric_stats = service.get_numeric_stats()
        numeric_vars_info = numeric_stats["variables"]
        
        # Extraer solo los nombres de variables numéricas
        self.numeric_cols = [v["variable"] for v in numeric_vars_info]
        
        print(f"\n🔍 Analizando {len(self.numeric_cols)} variables numéricas (según API)...")
        
        # Excluir variables que no deben analizarse
        exclude_cols = ["CEDULA", "Número"]
        self.numeric_cols = [col for col in self.numeric_cols if col not in exclude_cols]
        
        print(f"Variables numéricas a analizar: {len(self.numeric_cols)}")
        
        outliers_dict = {}
        outliers_summary = {}
        
        for col in self.numeric_cols:
            # Calcular cuartiles y IQR
            Q1 = self.data[col].quantile(0.25)
            Q3 = self.data[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Identificar outliers
            outliers = self.data[(self.data[col] < lower_bound) | (self.data[col] > upper_bound)]
            
            if len(outliers) > 0:
                # Guardar outliers con CÉDULA y Número si existen
                cols_to_show = ["CEDULA", "Número", col]
                available_cols = [c for c in cols_to_show if c in self.data.columns]
                outliers_dict[col] = outliers[available_cols]
                
                # Guardar resumen
                outliers_summary[col] = {
                    'total_outliers': len(outliers),
                    'percentage': (len(outliers) / len(self.data)) * 100,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound,
                    'Q1': Q1,
                    'Q3': Q3,
                    'IQR': IQR
                }
        
        self.outliers_dict = outliers_dict
        
        # Mostrar resumen
        print(f"\n📊 VARIABLES NUMÉRICAS CON OUTLIERS: {len(outliers_dict)}")
        print("=" * 60)
        
        for col, summary in outliers_summary.items():
            print(f"\n🔸 {col}:")
            print(f"   • Outliers: {summary['total_outliers']} ({summary['percentage']:.2f}%)")
            print(f"   • Rango normal: [{summary['lower_bound']:.2f}, {summary['upper_bound']:.2f}]")
            print(f"   • IQR: {summary['IQR']:.2f}")
        
        return outliers_dict, outliers_summary
    
    def show_outliers_by_variable(self, variable_name):
        """Muestra outliers de una variable específica con detalles explícitos"""
        if variable_name not in self.outliers_dict:
            print(f"❌ La variable '{variable_name}' no tiene outliers o no existe")
            return
        
        outliers_df = self.outliers_dict[variable_name]
        
        # Calcular límites para mostrar qué valores son outliers
        data = self.data.copy()
        Q1 = data[variable_name].quantile(0.25)
        Q3 = data[variable_name].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        print(f"\n📋 OUTLIERS DE '{variable_name}' ({len(outliers_df)} registros):")
        print("=" * 60)
        print(f"Rango normal: [{lower_bound:.2f}, {upper_bound:.2f}]")
        print(f"Valores < {lower_bound:.2f} o > {upper_bound:.2f} son outliers\n")
        
        # Mostrar cada outlier con su valor específico
        for idx, row in outliers_df.iterrows():
            outlier_value = row[variable_name]
            
            # Determinar si es outlier por debajo o por encima
            if outlier_value < lower_bound:
                outlier_type = "↓ BAJO"
                diff = outlier_value - lower_bound
            else:
                outlier_type = "↑ ALTO"
                diff = outlier_value - upper_bound
            
            print(f"🔴 FILA {idx}: {outlier_type}")
            
            # Mostrar información del paciente si está disponible
            if 'CEDULA' in row and pd.notna(row['CEDULA']):
                print(f"   📋 CÉDULA: {row['CEDULA']}")
            if 'Número' in row and pd.notna(row['Número']):
                print(f"   🏥 NÚMERO: {row['Número']}")
            
            print(f"   💊 VALOR OUTLIER: {outlier_value}")
            print(f"   📏 DIFERENCIA: {abs(diff):.2f} fuera del rango normal")
            print("-" * 40)
        
        return outliers_df
    
    def highlight_outliers_in_excel(self, output_filename="centenarios_completo_outliers.xlsx"):
        """Crea una copia del Excel con los outliers marcados con colores"""
        if not self.outliers_dict:
            print("❌ No hay outliers para marcar")
            return
        
        print(f"\n🎨 Marcando outliers en Excel...")
        
        # Copiar el archivo original
        output_path = Path(output_filename)
        
        try:
            # Guardar datos como Excel primero
            self.data.to_excel(output_path, index=False)
            
            # Cargar con openpyxl para aplicar estilos
            wb = load_workbook(output_path)
            ws = wb.active
            
            # Definir colores
            red_fill = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
            yellow_fill = PatternFill(start_color="FFD93D", end_color="FFD93D", fill_type="solid")
            red_font = Font(color="FFFFFF", bold=True)
            yellow_font = Font(color="000000", bold=True)
            
            # Para cada variable con outliers
            for col_name, outliers_df in self.outliers_dict.items():
                if col_name not in self.data.columns:
                    continue
                
                # Encontrar la columna en el Excel (basado en el header)
                col_idx = None
                for cell in ws[1]:  # Primera fila (headers)
                    if cell.value == col_name:
                        col_idx = cell.column
                        break
                
                if col_idx is None:
                    print(f"⚠️ Columna '{col_name}' no encontrada en el Excel")
                    continue
                
                # Calcular límites para esta variable
                data = self.data.copy()
                Q1 = data[col_name].quantile(0.25)
                Q3 = data[col_name].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Marcar cada outlier
                for idx, row in outliers_df.iterrows():
                    # Encontrar la fila en el Excel (índice + 2 porque Excel empieza en 1 y header es fila 1)
                    excel_row = idx + 2
                    
                    # Obtener el valor
                    cell_value = ws.cell(row=excel_row, column=col_idx).value
                    
                    if cell_value is not None:
                        # Determinar tipo de outlier y aplicar color
                        if cell_value < lower_bound:
                            # Outlier por debajo - amarillo
                            ws.cell(row=excel_row, column=col_idx).fill = yellow_fill
                            ws.cell(row=excel_row, column=col_idx).font = yellow_font
                            outlier_type = "BAJO"
                        elif cell_value > upper_bound:
                            # Outlier por encima - rojo
                            ws.cell(row=excel_row, column=col_idx).fill = red_fill
                            ws.cell(row=excel_row, column=col_idx).font = red_font
                            outlier_type = "ALTO"
                        
                        # Agregar comentario con detalles
                        comment_text = f"OUTLIER {outlier_type}\n"
                        comment_text += f"Valor: {cell_value}\n"
                        comment_text += f"Rango normal: [{lower_bound:.2f}, {upper_bound:.2f}]"
                        
                        # Crear comentario si no existe
                        cell = ws.cell(row=excel_row, column=col_idx)
                        if not cell.comment:
                            from openpyxl.comments import Comment
                            cell.comment = Comment(comment_text, "OutlierDetector")
            
            # Guardar el archivo modificado
            wb.save(output_path)
            
            print(f"✅ Excel con outliers marcados guardado en: {output_path}")
            print(f"🔴 Rojo: Outliers por encima del rango normal")
            print(f"🟡 Amarillo: Outliers por debajo del rango normal")
            print(f"💬 Comentarios: Pasa el mouse sobre las celdas marcadas para ver detalles")
            
        except ImportError:
            print("❌ Error: Necesitas instalar openpyxl. Ejecuta: pip install openpyxl")
        except Exception as e:
            print(f"❌ Error marcando outliers en Excel: {str(e)}")
    
    def create_boxplots(self, save_plots=True):
        """Crea boxplots para todas las variables numéricas"""
        if self.data is None:
            print("❌ Error: Dataset no cargado")
            return
        
        print(f"\n📈 Creando boxplots para {len(self.numeric_cols)} variables...")
        
        if save_plots:
            plots_dir = Path("boxplots")
            plots_dir.mkdir(exist_ok=True)
        
        for i, col in enumerate(self.numeric_cols, 1):
            plt.figure(figsize=(8, 6))
            
            # Crear boxplot sin colores personalizados (regla para artículos científicos)
            data_clean = self.data[col].dropna()
            plt.boxplot(data_clean, patch_artist=True, 
                       boxprops=dict(facecolor='white', color='black'),
                       whiskerprops=dict(color='black'),
                       capprops=dict(color='black'),
                       medianprops=dict(color='black'))
            
            plt.title(f"Boxplot - {col}", fontsize=14, fontweight='bold')
            plt.ylabel(col, fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # Añadir estadísticas
            stats_text = f"n: {len(data_clean)}\n"
            stats_text += f"Media: {data_clean.mean():.2f}\n"
            stats_text += f"Mediana: {data_clean.median():.2f}"
            
            plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            
            if save_plots:
                plt.savefig(plots_dir / f"boxplot_{col.replace('/', '_')}.png", 
                           dpi=300, bbox_inches='tight')
                print(f"  ✅ Guardado: boxplot_{col.replace('/', '_')}.png")
            else:
                plt.show()
            
            plt.close()  # Cerrar figura para liberar memoria
        
        if save_plots:
            print(f"\n📁 Todos los boxplots guardados en: {plots_dir}/")
    
    def save_outliers_report(self):
        """Guarda reporte completo de outliers"""
        if not self.outliers_dict:
            print("❌ No hay outliers que reportar")
            return
        
        report_file = Path("outliers_report.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("REPORTE DE OUTLIERS - VARIABLES NUMÉRICAS\n")
            f.write("=" * 60 + "\n")
            f.write(f"Dataset: {self.dataset_path.name}\n")
            f.write(f"Fecha: {pd.Timestamp.now()}\n")
            f.write(f"Variables analizadas: {len(self.numeric_cols)}\n")
            f.write(f"Variables con outliers: {len(self.outliers_dict)}\n\n")
            
            for col, outliers_df in self.outliers_dict.items():
                f.write(f"\nVARIABLE: {col}\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total outliers: {len(outliers_df)}\n")
                f.write(f"Porcentaje: {(len(outliers_df) / len(self.data)) * 100:.2f}%\n\n")
                f.write("Registros outliers:\n")
                f.write(outliers_df.to_string(index=False))
                f.write("\n\n")
        
        print(f"\n📄 Reporte guardado en: {report_file}")
    
    def interactive_menu(self):
        """Menú interactivo para explorar outliers"""
        while True:
            print("\n" + "=" * 50)
            print("MENÚ DE OUTLIERS")
            print("=" * 50)
            print("1. Ver lista de variables con outliers")
            print("2. Ver outliers de una variable específica")
            print("3. Crear boxplots")
            print("4. Marcar outliers en Excel (colorear)")
            print("5. Guardar reporte completo")
            print("6. Salir")
            
            choice = input("\nSelecciona una opción (1-6): ").strip()
            
            if choice == "1":
                print(f"\n📊 Variables con outliers ({len(self.outliers_dict)}):")
                for i, col in enumerate(self.outliers_dict.keys(), 1):
                    count = len(self.outliers_dict[col])
                    print(f"  {i}. {col} ({count} outliers)")
            
            elif choice == "2":
                if not self.outliers_dict:
                    print("❌ No hay outliers detectados")
                    continue
                
                print("\nVariables disponibles:")
                for i, col in enumerate(self.outliers_dict.keys(), 1):
                    print(f"  {i}. {col}")
                
                var_input = input("\nNombre de la variable (o número): ").strip()
                
                try:
                    # Si es un número, obtener la variable correspondiente
                    if var_input.isdigit():
                        var_list = list(self.outliers_dict.keys())
                        idx = int(var_input) - 1
                        if 0 <= idx < len(var_list):
                            variable = var_list[idx]
                        else:
                            print("❌ Número fuera de rango")
                            continue
                    else:
                        variable = var_input
                    
                    self.show_outliers_by_variable(variable)
                    
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
            
            elif choice == "3":
                save = input("¿Guardar boxplots en archivos? (s/n): ").strip().lower()
                self.create_boxplots(save == 's')
            
            elif choice == "4":
                self.highlight_outliers_in_excel()
            
            elif choice == "5":
                self.save_outliers_report()
            
            elif choice == "6":
                print("👋 ¡Hasta luego!")
                break
            
            else:
                print("❌ Opción no válida")

def main():
    # Ruta directa al archivo específico
    dataset_path = Path("/Users/natali/api-data-science/centenarios/CENTENARIOS_COMPLETO_PREP.xlsx")
    
    # Verificar archivo
    if not dataset_path.exists():
        print(f"❌ Error: No existe el archivo {dataset_path}")
        return
    
    # Crear detector y analizar
    detector = OutlierDetector(dataset_path)
    
    if not detector.load_data():
        return
    
    # Detectar outliers
    outliers_dict, outliers_summary = detector.detect_outliers()
    
    if outliers_dict:
        # Menú interactivo
        detector.interactive_menu()
    else:
        print("\n✅ No se detectaron outliers en las variables numéricas")

if __name__ == "__main__":
    main()
