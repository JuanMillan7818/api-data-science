import pandas as pd
from pathlib import Path
import math


class CentenariosService:
    PATH_FILE = Path(__file__).resolve(
    ).parents[2] / "centenarios/centenarios_diccionario.xlsx"

    def __init__(self):
        print("CentenariosService initialized" + str(self.PATH_FILE))

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

                results.append({
                    'variable': name,
                    'variable_label': variable_label,
                    'dtype': dtype,
                    'categories': categories,
                    'keywords': keywords
                })

            return results

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Excel file not found at {self.PATH_FILE}")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

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

        # Mocking completeness for now as we don't have real data values yet, just the dictionary
        # In a real scenario, this would calculate non-nulls / total cells
        completeness = 0.0  # Default to 0 or 100? User has dictionary, maybe 100% defined?
        # But looking at the component, it expects a percentage.
        # Since we only have metadata, let's return 0 or calculate based on fields filled in excel?
        # A dictionary is always "complete" in terms of definition, but maybe not data.
        # Let's mock it to 100 for definitions or 0 for data.
        # The prompt implies "stats de total de Numericas y demas", so variable counts are key.

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
            "completeness": 0.0
        }


centenarios_service = CentenariosService()
