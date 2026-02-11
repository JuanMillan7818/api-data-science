import pandas as pd
from pathlib import Path
import math


class CentenariosService:
    PATH_FILE = Path(__file__).resolve(
    ).parents[2] / "centenarios/centenarios_diccionario.xlsx"
    PATH_DATA_FILE = Path(__file__).resolve(
    ).parents[2] / "centenarios/centenarios_metabolomica.xlsx"

    def __init__(self):
        print("CentenariosService initialized " + str(self.PATH_FILE))
        self.completeness_map = self._calculate_completeness()

    def _calculate_completeness(self):
        """
        Loads the data file and calculates completeness statistics for each variable.
        """
        try:
            if not self.PATH_DATA_FILE.exists():
                print(f"Data file not found: {self.PATH_DATA_FILE}")
                return {}

            df = pd.read_excel(self.PATH_DATA_FILE)
            total_rows = len(df)
            stats = {}

            # Calculate stats for each column
            for col in df.columns:
                non_null = int(df[col].count())
                null_count = total_rows - non_null
                pct = (non_null / total_rows) * 100 if total_rows > 0 else 0.0

                # Normalize key to match dictionary variable names (usually lowercase/stripped in our service)
                # The dictionary service lowercases the 'Variable' column from the dictionary file.
                # We should try to match that.
                key = str(col).strip()

                stats[key] = {
                    "valid_percentage": pct,
                    "null_count": null_count,
                    "non_null_count": non_null,
                    "total_rows": total_rows
                }

            print(f"Loaded completeness stats for {len(stats)} variables.")
            return stats

        except Exception as e:
            print(f"Error calculating completeness: {str(e)}")
            return {}

    def get_variables_from_dictionary(self):
        """
        Reads the Excel file and returns a list of dictionaries containing 
        detailed variable information including dtype, categories, and keywords.
        """
        try:
            # Read the Excel file
            df = pd.read_excel(self.PATH_FILE)

            # Clean column names
            df.columns = df.columns.str.strip().str.lower()

            # Ensure required columns exist (mapping to expected lower case names)
            # Expected: variable, variable label, code, value, categoria, palabras clave

            # Rename for consistency
            column_mapping = {
                'variable': 'variable',
                'variable label': 'variable_label',
                'variablelabel': 'variable_label',
                'code': 'code',
                'value': 'value',
                'categoria': 'category_group',  # Renamed to avoid confusion with dtype category
                'palabras clave': 'keywords',
                'palabrasclave': 'keywords'
            }
            df = df.rename(columns=column_mapping)

            # Fill forward variable and label for merged cells interpretation
            # (though normally pandas reads repeated vars as separate rows if not merged,
            # if they are just empty for the same var in subsequent rows, forward fill is needed)
            # Assuming 'variable' is present for all valid rows or at least the start of a block
            df['variable'] = df['variable'].ffill()
            df['variable_label'] = df['variable_label'].ffill()
            # Do NOT ffill category/keywords globally, as it bleeds into next variable if empty within its own block start
            # We will handle extraction per group

            # Clean data
            df['variable'] = df['variable'].astype(str).str.strip()
            df = df[df['variable'] != 'nan']

            # Group by variable
            grouped = df.groupby('variable')

            results = []

            for name, group in grouped:
                first_row = group.iloc[0]
                variable_label = first_row.get('variable_label')
                if pd.isna(variable_label) or variable_label == 'nan':
                    variable_label = None
                else:
                    variable_label = str(variable_label).strip()

                # Determine dtype
                # 1. Check if 'category_group' (Excel: CATEGORIA) corresponds to the dictionary category logic
                # The user said: "si en el archivo tiene la columna 'CATEGORIA' y valor valido entonces colocar el dtype como 'categorical'"
                # But wait, looking at the screenshot, 'CATEGORIA' seems to be 'DATOS SOCIODEMOGRÁFICOS', which is a grouping, not the dtype itself.
                # However, the user explicitly said: "si en el archivo tiene la columna 'CATEGORIA' y valor valido entonces colocar el dtype como 'categorical'"
                # I will follow this instruction.

                category_val = first_row.get('category_group')
                is_categorical_group = pd.notna(category_val) and str(
                    category_val).strip() != '' and str(category_val).lower() != 'nan'

                # Default dtype
                dtype = 'unknown'

                # Check categories/codes to refine dtype
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
                    # User instruction: valid CATEGORIA => categorical
                    dtype = 'categorical'
                elif codes_present:
                    # Heuristic for boolean or generic categorical/ordinal
                    # Check if codes look like boolean (0/1 and Yes/No values)
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
                        # If it has codes but not strictly boolean-like, it's widely categorical/nominal
                        dtype = 'categorical'
                else:
                    # No codes, check label or name for hints
                    # If assume numeric unless specified
                    dtype = 'numeric'
                    # Check for datetime hints
                    if 'fecha' in name.lower() or (variable_label and 'fecha' in variable_label.lower()):
                        dtype = 'datetime'

                # Keywords
                keywords = []
                # Assuming keywords are in one row or repeated
                kw_val = first_row.get('keywords')
                if pd.notna(kw_val) and str(kw_val).strip() != '' and str(kw_val).lower() != 'nan':
                    # Split by comma or newline if multiple
                    keywords = [k.strip() for k in str(kw_val).replace(
                        '\n', ',').split(',') if k.strip()]

                # Merge completeness data
                # We try to find the variable name in the completeness map
                # The dictionary variable name is 'name' here.
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
                    **comp_data  # Spread the completeness stats into the variable object
                })

            return results

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Excel file not found at {self.PATH_FILE}")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

    def get_variable_completeness(self, page: int = 1, size: int = 20, dtype: str = None):
        """
        Returns completeness statistics with pagination.
        """
        variables = self.get_variables_from_dictionary()

        # Filter by dtype if provided
        if dtype and dtype != "all":
            variables = [v for v in variables if v.get('dtype') == dtype]

        total = len(variables)

        # Map to completeness items using the data already merged in get_variables_from_dictionary
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

        # Pagination
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
        Returns statistics about the variables.
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

        # Calculate global completeness (average valid percentage of all variables)
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
