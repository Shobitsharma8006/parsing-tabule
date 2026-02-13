from app.parsers.base_parser import BaseParser
import re


class MeasureParser(BaseParser):
    """
    Parses TRUE Tableau measures.
    """

    AGG_FUNCTIONS = {"SUM", "AVG", "COUNT", "COUNTD", "MIN", "MAX"}
    NUMERIC_TYPES = {"integer", "real", "float", "double", "number"}
    LOD_PATTERN = re.compile(r"\{\s*(FIXED|INCLUDE|EXCLUDE)", re.IGNORECASE)
    BOOLEAN_PATTERN = re.compile(r"(>=|<=|=|<|>)")

    def parse(self) -> dict:
        self.log_start()
        measures = {}

        try:
            for col in self.root.findall(".//column"):
                if col.attrib.get("role") != "measure":
                    continue

                calc = col.find("calculation")
                if calc is None:
                    continue

                formula = calc.attrib.get("formula")
                if not formula:
                    continue

                formula = formula.replace("&#10;", " ").strip()

                # Exclusions
                if self.LOD_PATTERN.search(formula):
                    continue
                if self.BOOLEAN_PATTERN.search(formula) and "AND" in formula.upper():
                    continue

                match = re.match(r"^\s*(\w+)\s*\(", formula)
                if not match:
                    continue

                agg = match.group(1).upper()
                if agg not in self.AGG_FUNCTIONS:
                    continue

                datatype = col.attrib.get("datatype")
                if datatype and datatype.lower() not in self.NUMERIC_TYPES:
                    continue

                name = col.attrib.get("caption") or col.attrib.get("name")
                name = name.strip("[]")

                usage_count = self._count_usage(col.attrib.get("name"))

                key = f"{agg.lower()}|{name}"

                measures[key] = {
                    "name": name,
                    "datatype": datatype,
                    "default_aggregation": agg.lower(),
                    "formula": formula,
                    "usage_count": usage_count
                }

            self.log_complete({"measure_count": len(measures)})
            return measures

        except Exception as e:
            self.log_error(e)
            raise

    def _count_usage(self, column_name: str) -> int:
        if not column_name:
            return 0
        return len(self.root.findall(
            f".//column-instance[@column='{column_name}']"
        ))
