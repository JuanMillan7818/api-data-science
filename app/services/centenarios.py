import pandas as pd
from pathlib import Path
import math


class CentenariosService:
    PATH_FILE = Path(__file__).resolve(
    ).parents[2] / "centenarios/centenarios_diccionario.xlsx"
    PATH_DATA_FILE = Path(__file__).resolve(
    ).parents[2] / "centenarios/centenarios_metabolomica_clean.xlsx"  # ← Usar archivo limpio

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

            #df = pd.read_excel(self.PATH_DATA_FILE)
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

            print(f"Variables con ≥90% completitud: {len(high_completeness_vars)}")
            print(f"Lista: {high_completeness_vars[:10]}...")  # Mostrar primeras 10
            
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
            output_file = Path(__file__).resolve().parents[2] / "variables_90plus_completitud.txt"
            
            # Obtener variables del diccionario para tener descripciones
            dict_vars = self.get_variables_from_dictionary()
            dict_var_info = {v['variable']: v for v in dict_vars}
            
            # Escribir lista al archivo
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Variables con ≥90% de completitud: {len(variables_list)}\n")
                f.write(f"Generado: {pd.Timestamp.now()}\n")
                f.write("=" * 50 + "\n")
                
                for var in variables_list:
                    # Buscar descripción en el diccionario
                    var_info = dict_var_info.get(var, {})
                    description = var_info.get('variable_label', 'Sin descripción (no en diccionario)')
                    dtype = var_info.get('dtype', 'unknown')
                    
                    # Obtener completitud del mapa (si existe)
                    completeness_pct = 0.0
                    if hasattr(self, 'completeness_map') and var in self.completeness_map:
                        completeness_pct = self.completeness_map[var].get('valid_percentage', 0.0)
                    
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
                    
                    inferred_dtype, inferred_categories = self._infer_from_dataset(name)
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
                inferred_dtype, inferred_categories = self._infer_from_dataset(var)
                
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
            print(f"ERROR en _infer_from_dataset para variable {var_name}: {str(e)}")
            return "unknown", []

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
            raise Exception(f"Error al obtener información del dataset: {str(e)}")
            



centenarios_service = CentenariosService()
