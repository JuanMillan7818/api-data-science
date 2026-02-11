import pandas as pd
from pathlib import Path
import math


class CentenariosService:
    PATH_FILE = Path(__file__).resolve(
    ).parents[2] / "centenarios/centenarios_diccionario.xlsx"
    PATH_DATA_FILE = Path(__file__).resolve(
    ).parents[2] / "centenarios/centenarios_metabolomica.xlsx"

    def __init__(self):
        print("CentenariosService inicializado " + str(self.PATH_FILE))
        self.completeness_map = self._calculate_completeness()

    def _calculate_completeness(self):
        """
        Carga el archivo de datos y calcula estadísticas de completitud para cada variable.
        Retorna un diccionario con métricas de valores nulos y válidos.
        """
        try:
            if not self.PATH_DATA_FILE.exists():
                print(f"Archivo de datos no encontrado: {self.PATH_DATA_FILE}")
                return {}

            df = pd.read_excel(self.PATH_DATA_FILE)
            total_rows = len(df)
            stats = {}

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

            print(
                f"Estadísticas de completitud cargadas para {len(stats)} variables.")
            return stats

        except Exception as e:
            print(f"Error calculating completeness: {str(e)}")
            return {}

    def get_variables_from_dictionary(self):
        """
        Lee el archivo Excel y retorna una lista de diccionarios con
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

            # Rellenar hacia adelante (ffill) variable y etiqueta para interpretación de celdas combinadas
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

                if is_categorical_group:
                    # Instrucción de usuario: CATEGORIA válida => categorical
                    dtype = 'categorical'
                elif codes_present:
                    # Heurística para booleano o categórico general/ordinal
                    # Verificar si los códigos parecen booleanos (0/1 y valores Si/No)
                    is_bool = False
                    if len(categories) == 2:
                        vals_set = {c['value'].lower() for c in categories}
                        codes_set = {c['code'] for c in categories}
                        if ({'0', '1'} == codes_set or {'1', '2'} == codes_set) and \
                           (any(v in vals_set for v in ['si', 'no', 'yes', 'no', 'true', 'false', 'hombre', 'mujer', 'masculino', 'femenino', 'urbana', 'rural'])):
                            is_bool = True

                    if is_bool:
                        dtype = 'boolean'
                    else:
                        # Si tiene códigos pero no es estrictamente booleano, es categórico/nominal
                        dtype = 'categorical'
                else:
                    # Sin códigos, revisar etiqueta o nombre para pistas
                    # Asumir numérico a menos que se especifique lo contrario
                    dtype = 'numeric'
                    # Verificar pistas de fecha
                    if 'fecha' in name.lower() or (variable_label and 'fecha' in variable_label.lower()):
                        dtype = 'datetime'

                # Palabras clave (Keywords)
                keywords = []
                # Asumiendo que las keywords están en una fila o repetidas
                kw_val = first_row.get('keywords')
                if pd.notna(kw_val) and str(kw_val).strip() != '' and str(kw_val).lower() != 'nan':
                    # Separar por coma o salto de línea si hay múltiples
                    keywords = [k.strip() for k in str(kw_val).replace(
                        '\n', ',').split(',') if k.strip()]

                # Fusionar datos de completitud
                # Intentamos encontrar el nombre de la variable en el mapa de completitud
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
                    **comp_data  # Esparcir las estadísticas de completitud en el objeto variable
                })

            return results

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Archivo Excel no encontrado en {self.PATH_FILE}")
        except Exception as e:
            raise Exception(f"Error al leer archivo Excel: {str(e)}")

    def get_variable_completeness(self, page: int = 1, size: int = 20, dtype: str = None):
        """
        Retorna estadísticas de completitud paginadas.
        """
        variables = self.get_variables_from_dictionary()

        # Filtrar por tipo de dato (dtype) si se proporciona
        if dtype and dtype != "all":
            variables = [v for v in variables if v.get('dtype') == dtype]

        total = len(variables)

        # Mapear a ítems de completitud usando los datos ya fusionados en get_variables_from_dictionary
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
        variables = self.get_variables_from_dictionary()

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


centenarios_service = CentenariosService()
