import pandas as pd
from pathlib import Path
import math


class CentenariosService:
    PATH_FILE = Path(__file__).resolve(
    ).parents[2] / "centenarios/centenarios_diccionario.xlsx"
    PATH_DATA_FILE = Path(__file__).resolve(
        # ← Usar archivo limpio
    ).parents[2] / "centenarios/centenarios_metabolomica_clean.xlsx"

    """
    def __init__(self):
        print("CentenariosService inicializado " + str(self.PATH_FILE))
        self.completeness_map = self._calculate_completeness()"""

    def __init__(self):
        print("CentenariosService inicializado " + str(self.PATH_FILE))

        # Cargar dataset UNA sola vez
        if self.PATH_DATA_FILE.exists():
            self.df_data = pd.read_excel(self.PATH_DATA_FILE)
        else:
            self.df_data = pd.DataFrame()
        self.completeness_map = self._calculate_completeness()

    def get_high_completeness_variables(self):
        """
        Retorna la lista de variables con ≥90% de completitud.
        Esta lista se calcula durante _calculate_completeness().
        """
        return getattr(self, 'high_completeness_vars', [])

    def _calculate_completeness(self):
        """
        Carga centenarios_metabolomica y calcula estadísticas de completitud para cada variable.
        Retorna un diccionario con métricas de valores nulos y válidos.
        """
        try:
            if not self.PATH_DATA_FILE.exists():
                print(f"Archivo de datos no encontrado: {self.PATH_DATA_FILE}")
                return {}

            # df = pd.read_excel(self.PATH_DATA_FILE)
            df = self.df_data
            total_rows = len(df)
            stats = {}

            # Lista para guardar variables con ≥90% completitud
            high_completeness_vars = []

            # Calcular estadísticas para cada columna
            for col in df.columns:
                non_null = int(df[col].count())
                null_count = total_rows - non_null
                pct = (non_null / total_rows) * 100 if total_rows > 0 else 0.0

                # Normalizar clave para coincidir con nombres de variables del diccionario
                # (generalmente minúsculas/sin espacios en nuestro servicio)
                key = str(col).strip()

                stats[key] = {
                    "valid_percentage": pct,
                    "null_count": null_count,
                    "non_null_count": non_null,
                    "total_rows": total_rows
                }

                # Guardar variables con ≥90% completitud
                if pct >= 90.0:
                    high_completeness_vars.append(key)

            print(
                f"Variables con ≥90% completitud: {len(high_completeness_vars)}")
            # Mostrar primeras 10
            print(f"Lista: {high_completeness_vars[:10]}...")

            # Guardar la lista como atributo para uso posterior
            self.high_completeness_vars = high_completeness_vars

            # Guardar en archivo .txt
            self._save_high_completeness_to_file(high_completeness_vars)

            print(
                f"Estadísticas de completitud cargadas para {len(stats)} variables.")
            return stats
        except Exception as e:
            print(f"Error calculating completeness: {str(e)}")
            return {}

    def _save_high_completeness_to_file(self, variables_list):
        """
        Guarda la lista de variables con ≥90% completitud en un archivo .txt
        Incluye descripción si está disponible en el diccionario.
        """
        try:
            # Ruta al archivo
            output_file = Path(__file__).resolve(
            ).parents[2] / "variables_90plus_completitud.txt"

            # Obtener variables del diccionario para tener descripciones
            dict_vars = self.get_variables_from_dictionary()
            dict_var_info = {v['variable']: v for v in dict_vars}

            # Escribir lista al archivo
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(
                    f"Variables con ≥90% de completitud: {len(variables_list)}\n")
                f.write(f"Generado: {pd.Timestamp.now()}\n")
                f.write("=" * 50 + "\n")

                for var in variables_list:
                    # Buscar descripción en el diccionario
                    var_info = dict_var_info.get(var, {})
                    description = var_info.get(
                        'variable_label', 'Sin descripción (no en diccionario)')
                    dtype = var_info.get('dtype', 'unknown')

                    # Obtener completitud del mapa (si existe)
                    completeness_pct = 0.0
                    if hasattr(self, 'completeness_map') and var in self.completeness_map:
                        completeness_pct = self.completeness_map[var].get(
                            'valid_percentage', 0.0)

                    f.write(f"{var}\n")
                    f.write(f"  └─ Descripción: {description}\n")
                    f.write(f"  └─ Tipo: {dtype}\n")
                    f.write(f"  └─ Completitud: {completeness_pct:.1f}%\n")
                    f.write("\n")

            print(f"Lista de variables con ≥90% guardada en: {output_file}")

        except Exception as e:
            print(f"Error guardando lista de variables: {str(e)}")

    def get_variables_from_dictionary(self):
        """
        Lee el archivo Excel centenarios_diccionario.xlsx y retorna una lista de diccionarios con
        información detallada de las variables, incluyendo tipo de dato (dtype), categorías y palabras clave.
        """
        try:
            # Leer el archivo Excel
            df = pd.read_excel(self.PATH_FILE)

            # Limpiar nombres de columnas
            df.columns = df.columns.str.strip().str.lower()

            # Asegurar que existan las columnas requeridas
            # Esperado: variable, variable label, code, value, categoria, palabras clave

            # Renombrar para consistencia
            column_mapping = {
                'variable': 'variable',
                'variable label': 'variable_label',
                'variablelabel': 'variable_label',
                'code': 'code',
                'value': 'value',
                # Renombrado para evitar confusion con dtype categoria
                'categoria': 'category_group',
                'palabras clave': 'keywords',
                'palabrasclave': 'keywords'
            }
            df = df.rename(columns=column_mapping)

            # Rellenar hacia adelante (fill) variable y etiqueta para interpretación de celdas combinadas
            # (pandas lee celdas combinadas como NaN en filas subsiguientes, necesitamos propagar el valor)
            df['variable'] = df['variable'].ffill()
            df['variable_label'] = df['variable_label'].ffill()
            # NO hacer ffill global de categoria/keywords, ya que contaminaría la siguiente variable
            # Manejaremos la extracción por grupo

            # Limpiar datos
            df['variable'] = df['variable'].astype(str).str.strip()
            df = df[df['variable'] != 'nan']

            # Agrupar por variable
            grouped = df.groupby('variable')

            results = []

            for name, group in grouped:
                # SOLO procesar variables que existen en el dataset
                if name not in self.df_data.columns:
                    continue

                first_row = group.iloc[0]
                variable_label = first_row.get('variable_label')
                if pd.isna(variable_label) or variable_label == 'nan':
                    variable_label = None
                else:
                    variable_label = str(variable_label).strip()

                # Determinar tipo de dato (dtype)
                # 1. Verificar si 'category_group' (Excel: CATEGORIA) tiene valor válido
                category_val = first_row.get('category_group')
                is_categorical_group = pd.notna(category_val) and str(
                    category_val).strip() != '' and str(category_val).lower() != 'nan'

                # Dtype por defecto
                dtype = 'unknown'

                # Verificar categorías/códigos para refinar dtype
                categories = []
                codes_present = False

                for _, row in group.iterrows():
                    code = row.get('code')
                    val = row.get('value')

                    if pd.notna(code) and str(code).strip() != '' and str(code).lower() != 'nan':
                        codes_present = True
                        cat_val = str(val).strip() if pd.notna(
                            val) else str(code)
                        categories.append({
                            'code': str(code).strip(),
                            'value': cat_val
                        })

                if len(categories) > 0:
                    # Si el diccionario tiene valores definidos en la columna "value"

                    if len(categories) == 2:
                        dtype = "boolean"
                    else:
                        dtype = "categorical"

                else:
                    # Si NO hay valores en el diccionario,
                    # entonces inferimos desde el dataset real

                    inferred_dtype, inferred_categories = self._infer_from_dataset(
                        name)
                    dtype = inferred_dtype
                    categories = inferred_categories

                # Palabras clave (Keywords)
                keywords = []
                # Asumiendo que las keywords están en una fila o repetidas
                kw_val = first_row.get('keywords')
                if pd.notna(kw_val) and str(kw_val).strip() != '' and str(kw_val).lower() != 'nan':
                    # Separar por coma o salto de línea si hay múltiples
                    keywords = [k.strip() for k in str(kw_val).replace(
                        '\n', ',').split(',') if k.strip()]

                # Fusionar datos de completitud
                comp_data = self.completeness_map.get(name, {
                    "valid_percentage": 0.0,
                    "null_count": 0,
                    "non_null_count": 0,
                    "total_rows": 0
                })

                results.append({
                    'variable': name,
                    'variable_label': variable_label,
                    'dtype': dtype,
                    'categories': categories,
                    'keywords': keywords,
                    "valid_percentage": float(comp_data.get("valid_percentage", 0.0)),
                    "null_count": int(comp_data.get("null_count", 0)),
                    "non_null_count": int(comp_data.get("non_null_count", 0)),
                    "total_rows": int(comp_data.get("total_rows", 0))
                })

            return results

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Archivo Excel no encontrado en {self.PATH_FILE}")
        except Exception as e:
            raise Exception(f"Error al leer archivo Excel: {str(e)}")

    def get_variables_from_dataset(self):
        # Obtener variables del dataset desde completeness_map
        # Cache del diccionario para no llamarlo 648 veces
        dict_vars_cache = self.get_variables_from_dictionary()
        dict_var_names = {d['variable'] for d in dict_vars_cache}

        dataset_vars = []
        for var_name, stats in self.completeness_map.items():
            # Verificar si esta variable ya está en el diccionario (usando cache)
            if var_name not in dict_var_names:
                dataset_vars.append({
                    'variable': var_name,
                    'variable_label': None,  # Sin documentación
                    'dtype': 'unknown',      # Sin tipo definido
                    'categories': [],         # Sin categorías
                    'keywords': [],          # Sin keywords
                    **stats                 # Estadísticas de completitud
                })
        return dataset_vars

    def get_all_variables(self):
        """
        Retorna TODAS las variables: diccionario + dataset.
        Combina variables documentadas con variables solo del dataset.
        """
        # Variables del diccionario
        dict_vars = self.get_variables_from_dictionary()

        # Variables del dataset que NO están en el diccionario
        dataset_vars = self.get_variables_not_in_dictionary()

        # Combinar: variables del diccionario + variables extra
        return dict_vars + dataset_vars

    def get_variable_completeness(self, page: int = 1, size: int = 20, dtype: str = None):
        """
        Retorna estadísticas de completitud paginadas.
        """
        # Usar el método que ya combina todo: 648 variables
        variables = self.get_all_variables()

        # Filtrar por tipo de dato (dtype) si se proporciona
        if dtype and dtype != "all":
            variables = [v for v in variables if v.get('dtype') == dtype]

        total = len(variables)

        # Mapear a ítems de completitud usando los datos ya fusionados
        completeness_items = []
        for v in variables:
            completeness_items.append({
                "variable": v['variable'],
                "valid_percentage": v.get('valid_percentage', 0.0),
                "null_count": v.get('null_count', 0),
                "non_null_count": v.get('non_null_count', 0),
                "total_rows": v.get('total_rows', 0),
                "dtype": v['dtype']
            })

        # Paginación
        start = (page - 1) * size
        end = start + size
        paginated_items = completeness_items[start:end]

        return {
            "items": paginated_items,
            "total": total,
            "page": page,
            "size": size,
            "has_more": end < total
        }

    def get_variable_stats(self):
        """
        Retorna estadísticas agregadas sobre las variables.
        """
        variables = self.get_all_variables()

        counts = {
            "numeric": 0,
            "categorical": 0,
            "boolean": 0,
            "datetime": 0,
            "unknown": 0
        }

        for v in variables:
            dtype = v.get('dtype', 'unknown')
            if dtype in counts:
                counts[dtype] += 1
            else:
                counts['unknown'] += 1

        # Calcular completitud global (promedio del porcentaje válido de todas las variables)
        total_valid_pct = sum(v.get('valid_percentage', 0.0)
                              for v in variables)
        avg_completeness = total_valid_pct / \
            len(variables) if len(variables) > 0 else 0.0

        return {
            "stats": [
                {"label": "Numericas",
                    "value": counts["numeric"], "type": "numeric"},
                {"label": "Categoricas",
                    "value": counts["categorical"], "type": "categorical"},
                {"label": "Booleanas",
                    "value": counts["boolean"], "type": "boolean"},
                {"label": "Datetime",
                    "value": counts["datetime"], "type": "datetime"},
            ],
            "total_variables": len(variables),
            "completeness": avg_completeness
        }

    def get_variables_not_in_dictionary(self):
        """
        Retorna variables que están en los datos crudos pero NO en el diccionario.
        """
        try:
            # Usar self.df_data que ya está cargado en __init__
            data_vars = set(self.df_data.columns)

            # Variables en diccionario
            variables_dict = self.get_variables_from_dictionary()
            dict_vars = {v['variable'] for v in variables_dict}

            # Variables que están en datos pero no en diccionario
            extra_vars = data_vars - dict_vars

            # Calcular estadísticas para estas variables
            extra_vars_info = []
            total_rows = len(self.df_data)

            for var in sorted(extra_vars):
                non_null = int(self.df_data[var].count())
                null_count = total_rows - non_null
                pct = (non_null / total_rows) * 100 if total_rows > 0 else 0.0

                # Inferir tipo desde los datos reales
                inferred_dtype, inferred_categories = self._infer_from_dataset(
                    var)

                extra_vars_info.append({
                    'variable': var,
                    'valid_percentage': float(pct),
                    'null_count': int(null_count),
                    'non_null_count': int(non_null),
                    'total_rows': int(total_rows),
                    'dtype': inferred_dtype,
                    'variable_label': None,
                    'categories': inferred_categories,
                    'keywords': []
                })

            return extra_vars_info

        except Exception as e:
            raise Exception(f"Error al obtener variables extra: {str(e)}")

    def _infer_from_dataset(self, var_name):
        """
        Infiere el tipo de variable desde los datos del dataset.
        Versión segura que evita errores de scalar variables.
        """
        try:
            if var_name not in self.df_data.columns:
                return "unknown", []

            series = self.df_data[var_name].dropna()

            if len(series) == 0:
                return "unknown", []

            # Si es numérico
            if pd.api.types.is_numeric_dtype(series):
                unique_vals = sorted(series.unique())
                n_unique = len(unique_vals)

                # Booleano 0/1
                if n_unique == 2 and set(unique_vals).issubset({0, 1}):
                    # Convertir tipos numpy a tipos nativos
                    return "boolean", [int(val) for val in unique_vals]

                # Pocos valores enteros → categórica codificada
                if n_unique <= 10:
                    # Convertir tipos numpy a tipos nativos
                    return "categorical", [int(val) for val in unique_vals]

                # Para el resto, asumir numérica
                return "numeric", []

            else:
                # Texto → categórica
                unique_vals = sorted(series.unique())
                return "categorical", unique_vals

        except Exception as e:
            print(
                f"ERROR en _infer_from_dataset para variable {var_name}: {str(e)}")
            return "unknown", []

    def analyze_missing_by_patient(self):
        """
        Analiza la distribución de valores missing por paciente (fila).
        Evalúa si el missing está concentrado en ciertos pacientes o distribuido homogéneamente.
        """
        print("Analizando missing por paciente...")

        # Calcular valores nulos por fila (paciente)
        missing_by_patient = self.df_data.isnull().sum(axis=1)
        total_columns = len(self.df_data.columns)

        # Calcular porcentaje de missing por paciente
        missing_pct_by_patient = (missing_by_patient / total_columns) * 100

        # Estadísticas básicas
        max_missing_pct = missing_pct_by_patient.max()
        mean_missing_pct = missing_pct_by_patient.mean()
        min_missing_pct = missing_pct_by_patient.min()

        # Pacientes con más de 30% y 50% missing
        patients_above_30pct = (missing_pct_by_patient > 30).sum()
        patients_above_50pct = (missing_pct_by_patient > 50).sum()

        # IDs de pacientes con más de 50% missing
        high_missing_indices = missing_pct_by_patient[missing_pct_by_patient > 50].index.tolist(
        )
        high_missing_patient_ids = []

        # Obtener IDs de pacientes (columna 'Número' si existe)
        if 'Número' in self.df_data.columns:
            high_missing_patient_ids = self.df_data.loc[high_missing_indices, 'Número'].tolist(
            )
        else:
            high_missing_patient_ids = [
                f"Paciente_{i}" for i in high_missing_indices]

        # Análisis por Sexo
        sex_analysis = {}
        if 'Sexo' in self.df_data.columns:
            sex_missing = self.df_data.groupby('Sexo').apply(
                lambda x: x.isnull().sum().sum() / (len(x.columns) * len(x)) * 100
            )
            sex_analysis = sex_missing.to_dict()

        # Análisis por Edad
        age_analysis = {}
        if 'Edad' in self.df_data.columns:
            # Crear grupos de edad
            age_bins = [0, 30, 50, 70, 100]
            age_labels = ['0-30', '31-50', '51-70', '71-100']
            self.df_data['edad_grupo'] = pd.cut(
                self.df_data['Edad'], bins=age_bins, labels=age_labels, right=False)

            # Calcular missing por grupo de edad de forma más simple
            for grupo_label in age_labels:
                grupo_mask = self.df_data['edad_grupo'] == grupo_label
                grupo_data = self.df_data[grupo_mask]

                if len(grupo_data) > 0:
                    missing_pct = (grupo_data.isnull().sum().sum(
                    ) / (len(grupo_data.columns) * len(grupo_data))) * 100
                    age_analysis[grupo_label] = float(missing_pct)
                else:
                    age_analysis[grupo_label] = 0.0

            # Eliminar columna temporal
            self.df_data = self.df_data.drop('edad_grupo', axis=1)

        # Resultados estructurados
        results = {
            "max_missing_pct": float(max_missing_pct),
            "mean_missing_pct": float(mean_missing_pct),
            "min_missing_pct": float(min_missing_pct),
            "patients_above_30pct": int(patients_above_30pct),
            "patients_above_50pct": int(patients_above_50pct),
            "high_missing_patient_ids": high_missing_patient_ids,
            "sex_analysis": sex_analysis,
            "age_analysis": age_analysis
        }

        # Imprimir resultados
        print("\n" + "="*60)
        print("ANÁLISIS DE MISSING POR PACIENTE")
        print("="*60)
        print(f"Total pacientes analizados: {len(self.df_data)}")
        print(f"Total variables analizadas: {total_columns}")
        print(f"\nEstadísticas de missing por paciente:")
        print(f"  Máximo missing: {max_missing_pct:.2f}%")
        print(f"  Promedio missing: {mean_missing_pct:.2f}%")
        print(f"  Mínimo missing: {min_missing_pct:.2f}%")
        print(
            f"\nPacientes con >30% missing: {patients_above_30pct} ({patients_above_30pct/len(self.df_data)*100:.1f}%)")
        print(
            f"Pacientes con >50% missing: {patients_above_50pct} ({patients_above_50pct/len(self.df_data)*100:.1f}%)")

        # Interpretación automática
        print(f"\nINTERPRETACIÓN:")
        if patients_above_50pct > 0:
            print(
                f"  ⚠️  HAY CONCENTRACIÓN: {patients_above_50pct} pacientes con >50% missing")
            print(
                f"  IDs pacientes problemáticos: {high_missing_patient_ids[:5]}{'...' if len(high_missing_patient_ids) > 5 else ''}")
        else:
            print(f"  ✅ NO HAY CONCENTRACIÓN: Ningún paciente con >50% missing")

        # Evaluar homogeneidad
        cv = missing_pct_by_patient.std() / mean_missing_pct  # Coeficiente de variación
        if cv < 0.3:
            print(f"  ✅ DISTRIBUCIÓN HOMOGÉNEA: CV = {cv:.3f} < 0.3")
        else:
            print(f"  ⚠️  DISTRIBUCIÓN HETEROGÉNEA: CV = {cv:.3f} ≥ 0.3")

        # Análisis por Sexo
        if sex_analysis:
            print(f"\nANÁLISIS POR SEXO:")
            for sexo, pct in sex_analysis.items():
                print(f"  {sexo}: {pct:.2f}% missing")

        # Análisis por Edad
        if age_analysis:
            print(f"\nANÁLISIS POR EDAD:")
            for edad_grupo, pct in age_analysis.items():
                print(f"  {edad_grupo}: {float(pct):.2f}% missing")

        print("="*60)

        return results

    def plot_missing_by_patient(self):
        """
        Genera un histograma del porcentaje de missing por paciente.
        """
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            print("Generando histograma de missing por paciente...")

            # Calcular missing por paciente
            missing_by_patient = self.df_data.isnull().sum(axis=1)
            total_columns = len(self.df_data.columns)
            missing_pct_by_patient = (missing_by_patient / total_columns) * 100

            # Crear histograma
            plt.figure(figsize=(12, 6))
            plt.hist(missing_pct_by_patient, bins=20,
                     edgecolor='black', alpha=0.7, color='skyblue')
            plt.title('Distribución de Missing por Paciente',
                      fontsize=14, fontweight='bold')
            plt.xlabel('Porcentaje de Missing (%)', fontsize=12)
            plt.ylabel('Número de Pacientes', fontsize=12)
            plt.grid(True, alpha=0.3)

            # Agregar línea de referencia en 50%
            plt.axvline(x=50, color='red', linestyle='--',
                        linewidth=2, label='Umbral 50%')
            plt.legend()

            # Agregar estadísticas
            mean_pct = missing_pct_by_patient.mean()
            plt.text(0.02, 0.95, f'Media: {mean_pct:.1f}%',
                     transform=plt.gca().transAxes, fontsize=10,
                     verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            plt.tight_layout()
            plt.show()

            print("Histograma generado exitosamente")

        except ImportError:
            print(
                "❌ Error: matplotlib no está instalado. Instale con: pip install matplotlib")
        except Exception as e:
            print(f"❌ Error al generar histograma: {str(e)}")

    def get_dataset_info(self):
        """
        Obtiene información del dataset.
        """
        try:
            return {
                "total_variables": len(self.df_data.columns),
                "total_rows": len(self.df_data),
                "columns": self.df_data.columns.tolist()
            }
        except Exception as e:
            raise Exception(
                f"Error al obtener información del dataset: {str(e)}")

    def get_numeric_stats(self):
        """
        Calcula estadísticas descriptivas para variables numéricas.
        Útil para generar gráficos boxplot en el frontend.
        Usa las mismas variables que el endpoint /variables con dtype=numeric.
        """
        try:
            if self.df_data.empty:
                return {"variables": []}

            # Obtener todas las variables del servicio (como en el endpoint /variables)
            all_vars = self.get_all_variables()

            # Filtrar solo variables numéricas (como en el endpoint /variables con dtype=numeric)
            numeric_vars = [v for v in all_vars if v.get('dtype') == 'numeric']

            # Filtrar variables que existen en el dataset
            numeric_vars = [
                v for v in numeric_vars if v['variable'] in self.df_data.columns]

            stats = []
            total_rows = len(self.df_data)

            for var_info in numeric_vars:
                var_name = var_info['variable']
                col_data = self.df_data[var_name].dropna()

                if len(col_data) > 0:
                    stats.append({
                        "variable": var_name,
                        "variable_label": var_info.get('variable_label', var_name),
                        "dtype": "numeric",
                        "mean": float(col_data.mean()),
                        "std": float(col_data.std()),
                        "min": float(col_data.min()),
                        "q1": float(col_data.quantile(0.25)),
                        "median": float(col_data.median()),
                        "q3": float(col_data.quantile(0.75)),
                        "max": float(col_data.max()),
                        "valid_percentage": (len(col_data) / total_rows) * 100,
                        "null_count": int(self.df_data[var_name].isna().sum()),
                        "non_null_count": int(len(col_data)),
                        "total_rows": int(total_rows)
                    })

            return {"variables": stats}

        except Exception as e:
            raise Exception(
                f"Error al calcular estadísticas numéricas: {str(e)}")

    def _get_variable_label(self, variable_name):
        """
        Obtiene el label de una variable desde el diccionario.
        """
        try:
            # Obtener variables del diccionario
            dict_vars = self.get_variables_from_dictionary()

            # Buscar la variable
            for var in dict_vars:
                if var['variable'] == variable_name:
                    return var.get('variable_label', variable_name)

            # Si no se encuentra, retornar el nombre de la variable
            return variable_name

        except Exception:
            # Si hay error, retornar el nombre de la variable
            return variable_name

    def get_categorical_stats(self, page: int = 1, size: int = 20, search: str = None):
        """
        Calcula estadísticas detalladas para variables categóricas.
        Retorna top 20 valores más frecuentes para cada variable.
        """
        try:
            # 1. Obtener todas las variables
            all_vars = self.get_all_variables()

            # 2. Filtrar solo categóricas
            cat_vars = [v for v in all_vars if v.get('dtype') == 'categorical']

            # 3. Filtro de búsqueda (si aplica)
            if search:
                search_lower = search.lower()
                cat_vars = [
                    v for v in cat_vars
                    if search_lower in str(v.get("variable", "")).lower() or
                    search_lower in str(v.get("variable_label", "")).lower() or
                    any(search_lower in k.lower()
                        for k in v.get("keywords", []))
                ]

            total = len(cat_vars)

            # 4. Paginación
            start = (page - 1) * size
            end = start + size
            paginated_vars = cat_vars[start:end]

            items = []

            for var_info in paginated_vars:
                var_name = var_info['variable']

                # Verificar si existe en dataset
                if var_name not in self.df_data.columns:
                    continue

                # Calcular value counts
                # dropna=True por defecto en value_counts, pero queremos asegurarnos
                series = self.df_data[var_name]
                total_rows = len(series)
                valid_count = series.count()

                # Top 20 valores
                # normalize=False para conteos absolutos
                value_counts = series.value_counts().head(20)

                # Crear mapa de códigos a etiquetas para esta variable
                category_map = {}
                if var_info.get('categories'):
                    for cat in var_info['categories']:
                        if isinstance(cat, dict):
                            code = str(cat.get('code', '')).strip()
                            label = str(cat.get('value', '')).strip()
                            if code:
                                category_map[code] = label
                        # Si no es dict (es str/int), no hay mapeo código-etiqueta adicional
                        # que podamos usar, así que lo ignoramos para el mapa.

                top_values = []
                for val, count in value_counts.items():
                    # Calcular porcentaje relativo al total de filas (o validas? usu. validas para distribucion)
                    # Aquí usaremos relativas a validas para que sumen 100% (si mostramos todos)
                    # Pero el requerimiento dice "cantidad de valores que hay de cada opcion"

                    pct = (count / valid_count *
                           100) if valid_count > 0 else 0.0

                    val_str = str(val).strip()

                    # Normalizar: Si es float convertiod a string tipo "1.0", eliminar el ".0"
                    # para que coincida con el código del diccionario "1"
                    if val_str.endswith('.0'):
                        val_str = val_str[:-2]

                    display_value = val_str
                    label_text = None

                    # Intentar mapear a etiqueta del diccionario
                    if val_str in category_map:
                        mapped_label = category_map[val_str]
                        if mapped_label and mapped_label.lower() != val_str.lower():
                            label_text = mapped_label

                    # Manejo especial para booleanos si no hay categorías definidas pero es 0/1
                    elif var_info.get('dtype') == 'boolean':
                        if val_str == '0':
                            label_text = "Falso/No"
                        elif val_str == '1':
                            label_text = "Verdadero/Sí"

                    top_values.append({
                        "value": display_value,
                        "label": label_text,
                        "count": int(count),
                        "percentage": float(pct)
                    })

                # Normalizar lista de categorías para cumplir con el esquema Pydantic
                raw_categories = var_info.get('categories', [])
                formatted_categories = []
                if raw_categories:
                    for cat in raw_categories:
                        if isinstance(cat, dict):
                            formatted_categories.append(cat)
                        else:
                            # Si es un primitivo (int, str), convertir a estructura Category
                            val_str = str(cat).strip()
                            formatted_categories.append({
                                "code": val_str,
                                "value": val_str
                            })

                items.append({
                    "variable": var_name,
                    "variable_label": var_info.get('variable_label'),
                    "total_rows": int(total_rows),
                    "valid_percentage": var_info.get('valid_percentage', 0.0),
                    "top_values": top_values,
                    "categories": formatted_categories
                })

            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "has_more": end < total
            }

        except Exception as e:
            print(f"Error en get_categorical_stats: {str(e)}")
            raise Exception(
                f"Error al calcular estadísticas categóricas: {str(e)}")


centenarios_service = CentenariosService()
