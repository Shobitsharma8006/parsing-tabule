# import re
# from app.parsers.base_parser import BaseParser
# from app.parsers.measure_parser import MeasureParser

# class CalculationParser(BaseParser):
#     """
#     Tableau-semantic calculation parser.

#     Buckets:
#     - measures
#     - calculated_fields        ✅ real calculated logic only
#     - lod_expressions
#     - filters
#     """

#     LOD_PATTERNS = {
#         "fixed": re.compile(r"\{\s*FIXED", re.IGNORECASE),
#         "include": re.compile(r"\{\s*INCLUDE", re.IGNORECASE),
#         "exclude": re.compile(r"\{\s*EXCLUDE", re.IGNORECASE),
#     }

#     AGG_FUNCTIONS = ["SUM(", "AVG(", "COUNT(", "COUNTD("]
#     BOOLEAN_HINTS = [">", "<", ">=", "<=", "=", " AND ", " OR "]

#     # 🔴 literals only → parameter backing fields
#     LITERAL_ONLY_PATTERN = re.compile(r'^(".*?"|\d+(\.\d+)?)$')

#     def parse(self) -> dict:
#         self.log_start()

#         calculated_fields = {}
#         lod_expressions = {}
#         filters = {}

#         # 1️⃣ Build Caption Map (Technical ID -> Human Name)
#         caption_map = self._get_caption_map()

#         try:
#             measures = MeasureParser(self.root, self.context).parse()

#             for col in self.root.findall(".//column"):
#                 calc = col.find("calculation")
#                 if calc is None:
#                     continue

#                 formula = calc.attrib.get("formula")
#                 if not formula:
#                     continue

#                 formula = self._normalize_formula(formula)

#                 # -------------------------------
#                 # 🚫 EXCLUDE PARAMETERS
#                 # -------------------------------
#                 if self._is_parameter_column(col, formula):
#                     continue

#                 # 2️⃣ Resolve Display Name
#                 raw_name = col.attrib.get("name", "")
#                 display_name = col.attrib.get("caption") or caption_map.get(raw_name, raw_name.strip("[]"))
                
#                 # 3️⃣ Resolve Formula & Dependencies (Replace IDs with Names)
#                 true_formula = self._resolve_formula_expressions(formula, caption_map)
                
#                 raw_dependencies = self._extract_dependencies(formula)
#                 true_dependencies = [
#                     self._resolve_dependency_name(d, caption_map)
#                     for d in raw_dependencies
#                 ]

#                 usage_count = self._count_usage(col.attrib.get("name"))

#                 # -------------------------------
#                 # 1️⃣ LOD
#                 # -------------------------------
#                 lod_type = self._detect_lod_type(true_formula)
#                 if lod_type:
#                     lod_expressions[display_name] = {
#                         "formula": true_formula,
#                         "lod_type": lod_type,
#                         "dependencies": true_dependencies,
#                         "usage_count": usage_count
#                     }
#                     continue

#                 # -------------------------------
#                 # 2️⃣ Boolean filters / RLS
#                 # -------------------------------
#                 if self._is_boolean_filter(true_formula):
#                     calculated_fields[display_name] = {
#                         "formula": true_formula,
#                         "dependencies": true_dependencies,
#                         "usage_count": usage_count
#                     }
#                     continue

#                 # -------------------------------
#                 # 3️⃣ Measures (already handled)
#                 # -------------------------------
#                 if self._is_measure_formula(true_formula):
#                     continue

#                 # -------------------------------
#                 # 4️⃣ Real calculated fields
#                 # -------------------------------
#                 calculated_fields[display_name] = {
#                     "formula": true_formula,
#                     "dependencies": true_dependencies,
#                     "usage_count": usage_count
#                 }

#             self.log_complete({
#                 "calculated_field_count": len(calculated_fields),
#                 "lod_count": len(lod_expressions),
#                 "filter_count": len(filters)
#             })

#             return {
#                 "measures": measures,
#                 "calculated_fields": calculated_fields,
#                 "lod_expressions": lod_expressions,
#                 "filters": filters
#             }

#         except Exception as e:
#             self.log_error(e)
#             raise

#     # ==================================================
#     # Helpers
#     # ==================================================

#     def _get_caption_map(self) -> dict:
#         """
#         Scans all columns to build a mapping from Technical IDs 
#         to their human-readable [Caption] names.
#         """
#         mapping = {}
#         for col in self.root.findall(".//column"):
#             name = col.attrib.get("name")
#             caption = col.attrib.get("caption")
#             if name and caption:
#                 # Map BOTH the bracketed and unbracketed versions to the caption
#                 mapping[name] = f"[{caption}]"
#                 if not name.startswith("["):
#                     mapping[f"[{name}]"] = f"[{caption}]"
#         return mapping

#     def _resolve_formula_expressions(self, formula: str, caption_map: dict) -> str:
#         """
#         Replaces ALL instances of [Technical_ID] (e.g. [Calculation_...] OR [VISIT_STATUS]) 
#         in the formula string with the actual field captions.
#         """
#         resolved_formula = formula
        
#         # 🟢 UPDATED REGEX: Capture ANY content inside square brackets
#         # matches: [Calculation_123], [VISIT_STATUS], [Department]
#         tokens = re.findall(r"(\[[^\]]+\])", resolved_formula)
        
#         for token in set(tokens): # Use set to avoid redundant replacements
#             # 1. Try direct match with brackets (e.g. "[VISIT_STATUS]" -> "[Visit Status]")
#             if token in caption_map:
#                 resolved_formula = resolved_formula.replace(token, caption_map[token])
            
#             # 2. Try match without brackets (just in case map key is "VISIT_STATUS")
#             else:
#                 inner_text = token.strip("[]")
#                 if inner_text in caption_map:
#                      resolved_formula = resolved_formula.replace(token, caption_map[inner_text])
        
#         return resolved_formula

#     def _resolve_dependency_name(self, raw_dep: str, caption_map: dict) -> str:
#         """Helper to resolve a single dependency name cleanly"""
#         # Try finding the bracketed version first
#         bracketed = f"[{raw_dep}]"
#         if bracketed in caption_map:
#             return caption_map[bracketed].strip("[]")
        
#         if raw_dep in caption_map:
#              return caption_map[raw_dep].strip("[]")
             
#         return raw_dep

#     def _normalize_formula(self, formula: str) -> str:
#         return formula.replace("&#10;", "\n").strip()

#     def _detect_lod_type(self, formula: str):
#         for lod_type, pattern in self.LOD_PATTERNS.items():
#             if pattern.search(formula):
#                 return lod_type
#         return None

#     def _is_measure_formula(self, formula: str) -> bool:
#         f = formula.upper()
#         return any(fn in f for fn in self.AGG_FUNCTIONS)

#     def _is_boolean_filter(self, formula: str) -> bool:
#         f = formula.upper()
#         return (
#             "IF " in f
#             or "CASE " in f
#             or "USERNAME()" in f
#             or any(op in f for op in self.BOOLEAN_HINTS)
#         )

#     def _extract_dependencies(self, formula: str) -> list:
#         return sorted(set(re.findall(r"\[([^\]]+)\]", formula)))

#     def _count_usage(self, column_name: str) -> int:
#         if not column_name:
#             return 0
#         return len(self.root.findall(f".//column-instance[@column='{column_name}']"))

#     def _is_parameter_column(self, col, formula: str) -> bool:
#         """
#         Detect Tableau parameters masquerading as calculations.
#         """
#         # class="parameter"
#         if col.attrib.get("class") == "parameter":
#             return True

#         # literal-only formula → "completed", 0, 5
#         if self.LITERAL_ONLY_PATTERN.match(formula.strip()):
#             return True

#         # parameter datasource reference
#         if "[Parameters]." in formula:
#             return False  # real logic using parameter → KEEP

#         # param-domain-type attribute
#         if col.attrib.get("param-domain-type"):
#             return True

#         return False




import re
from app.parsers.base_parser import BaseParser
from app.parsers.measure_parser import MeasureParser


class CalculationParser(BaseParser):
    """
    Tableau-semantic calculation parser.

    Buckets:
    - measures
    - calculated_fields        ✅ real calculated logic only
    - lod_expressions
    - filters
    """

    LOD_PATTERNS = {
        "fixed": re.compile(r"\{\s*FIXED", re.IGNORECASE),
        "include": re.compile(r"\{\s*INCLUDE", re.IGNORECASE),
        "exclude": re.compile(r"\{\s*EXCLUDE", re.IGNORECASE),
    }

    AGG_FUNCTIONS = ["SUM(", "AVG(", "COUNT(", "COUNTD("]
    BOOLEAN_HINTS = [">", "<", ">=", "<=", "=", " AND ", " OR "]

    # literals only → parameter backing fields
    LITERAL_ONLY_PATTERN = re.compile(r'^(".*?"|\d+(\.\d+)?)$')

    # ==================================================
    # MAIN PARSER
    # ==================================================

    def parse(self) -> dict:
        self.log_start()

        calculated_fields = {}
        lod_expressions = {}
        filters = {}

        caption_map = self._get_caption_map()

        try:
            measures = MeasureParser(self.root, self.context).parse()

            for col in self.root.findall(".//column"):
                calc = col.find("calculation")
                if calc is None:
                    continue

                formula = calc.attrib.get("formula")
                if not formula:
                    continue

                formula = self._normalize_formula(formula)

                # 🚫 skip pure parameter definitions
                if self._is_parameter_column(col, formula):
                    continue

                # Resolve display name
                raw_name = col.attrib.get("name", "")
                display_name = (
                    col.attrib.get("caption")
                    or caption_map.get(raw_name, raw_name.strip("[]"))
                )

                # ✅ Resolve parameters + captions
                true_formula = self._resolve_formula_expressions(formula, caption_map)

                # ✅ Extract dependencies from CLEAN formula
                raw_dependencies = self._extract_dependencies(true_formula)
                true_dependencies = [
                    self._resolve_dependency_name(d, caption_map)
                    for d in raw_dependencies
                ]

                usage_count = self._count_usage(col.attrib.get("name"))

                # -------------------------------
                # LOD EXPRESSIONS
                # -------------------------------
                lod_type = self._detect_lod_type(true_formula)
                if lod_type:
                    lod_expressions[display_name] = {
                        "formula": true_formula,
                        "lod_type": lod_type,
                        "dependencies": true_dependencies,
                        "usage_count": usage_count,
                    }
                    continue

                # -------------------------------
                # BOOLEAN FILTERS / RLS
                # -------------------------------
                if self._is_boolean_filter(true_formula):
                    calculated_fields[display_name] = {
                        "formula": true_formula,
                        "dependencies": true_dependencies,
                        "usage_count": usage_count,
                    }
                    continue

                # -------------------------------
                # MEASURES (already parsed)
                # -------------------------------
                if self._is_measure_formula(true_formula):
                    continue

                # -------------------------------
                # REAL CALCULATED FIELDS
                # -------------------------------
                calculated_fields[display_name] = {
                    "formula": true_formula,
                    "dependencies": true_dependencies,
                    "usage_count": usage_count,
                }

            self.log_complete({
                "calculated_field_count": len(calculated_fields),
                "lod_count": len(lod_expressions),
                "filter_count": len(filters),
            })

            return {
                "measures": measures,
                "calculated_fields": calculated_fields,
                "lod_expressions": lod_expressions,
                "filters": filters,
            }

        except Exception as e:
            self.log_error(e)
            raise

    # ==================================================
    # HELPERS
    # ==================================================

    def _get_caption_map(self) -> dict:
        """
        Builds mapping:
        [TECH_NAME] -> [Caption]
        """
        mapping = {}

        for col in self.root.findall(".//column"):
            name = col.attrib.get("name")
            caption = col.attrib.get("caption")

            if name and caption:
                mapping[name] = f"[{caption}]"
                mapping[name.strip("[]")] = f"[{caption}]"

        return mapping

    def _strip_parameter_namespace(self, formula: str) -> str:
        """
        [Parameters].[Revenue Threshold] → [Revenue Threshold]
        """
        return re.sub(
            r"\[Parameters\]\.\[([^\]]+)\]",
            r"[\1]",
            formula,
        )

    def _resolve_formula_expressions(self, formula: str, caption_map: dict) -> str:
        """
        Resolves:
        - Parameter namespace
        - Technical IDs → captions
        """
        resolved_formula = self._strip_parameter_namespace(formula)

        tokens = re.findall(r"(\[[^\]]+\])", resolved_formula)

        for token in set(tokens):
            if token in caption_map:
                resolved_formula = resolved_formula.replace(token, caption_map[token])
            else:
                inner = token.strip("[]")
                if inner in caption_map:
                    resolved_formula = resolved_formula.replace(token, caption_map[inner])

        return resolved_formula

    def _resolve_dependency_name(self, raw_dep: str, caption_map: dict) -> str:
        bracketed = f"[{raw_dep}]"

        if bracketed in caption_map:
            return caption_map[bracketed].strip("[]")

        if raw_dep in caption_map:
            return caption_map[raw_dep].strip("[]")

        return raw_dep

    def _normalize_formula(self, formula: str) -> str:
        return formula.replace("&#10;", "\n").strip()

    def _detect_lod_type(self, formula: str):
        for lod_type, pattern in self.LOD_PATTERNS.items():
            if pattern.search(formula):
                return lod_type
        return None

    def _is_measure_formula(self, formula: str) -> bool:
        f = formula.upper()
        return any(fn in f for fn in self.AGG_FUNCTIONS)

    def _is_boolean_filter(self, formula: str) -> bool:
        f = formula.upper()
        return (
            "IF " in f
            or "CASE " in f
            or "USERNAME()" in f
            or any(op in f for op in self.BOOLEAN_HINTS)
        )

    def _extract_dependencies(self, formula: str) -> list:
        return sorted(set(re.findall(r"\[([^\]]+)\]", formula)))

    def _count_usage(self, column_name: str) -> int:
        if not column_name:
            return 0
        return len(
            self.root.findall(
                f".//column-instance[@column='{column_name}']"
            )
        )

    def _is_parameter_column(self, col, formula: str) -> bool:
        """
        Detect Tableau parameters masquerading as calculations.
        """
        if col.attrib.get("class") == "parameter":
            return True

        if self.LITERAL_ONLY_PATTERN.match(formula.strip()):
            return True

        if "[Parameters]." in formula:
            return False

        if col.attrib.get("param-domain-type"):
            return True

        return False
