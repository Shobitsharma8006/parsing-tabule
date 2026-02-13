from app.parsers.base_parser import BaseParser
import re


class SheetVisualParser(BaseParser):

    BOOLEAN_DATATYPES = {"boolean"}
    PARAMETER_PREFIX = "Parameter"

    def parse(self) -> dict:
        self.log_start()
        sheets = []

        try:
            # -------------------------------
            # Build Calculation ID → Caption map
            # -------------------------------
            calc_caption_map = {}
            calc_boolean_map = {}

            for col in self.root.findall(".//column"):
                name = col.attrib.get("name")
                caption = col.attrib.get("caption")
                datatype = col.attrib.get("datatype")

                if name and caption and name.startswith("[Calculation_"):
                    clean = self._clean_field(name)
                    calc_caption_map[clean] = caption
                    if datatype in self.BOOLEAN_DATATYPES:
                        calc_boolean_map[clean] = True

            # -------------------------------
            # Parse Worksheets
            # -------------------------------
            for ws in self.root.findall(".//worksheet"):
                sheet_name = ws.attrib.get("name")

                mark_node = ws.find(".//mark")
                mark_type = mark_node.attrib.get("class") if mark_node is not None else None

                dimensions = set()
                measures = set()
                filters = set()

                # -------------------------------
                # Dependencies (core signal)
                # -------------------------------
                for dep in ws.findall(".//datasource-dependencies/column"):
                    role = dep.attrib.get("role")
                    name = dep.attrib.get("name")
                    datatype = dep.attrib.get("datatype")

                    if not name:
                        continue

                    clean = self._clean_field(name)
                    resolved = self._resolve_calc(clean, calc_caption_map)

                    # 🚫 Skip parameters
                    if clean.startswith(self.PARAMETER_PREFIX):
                        continue

                    # 🚫 Skip EMAIL_ADDRESS as visual dimension (RLS)
                    if resolved == "EMAIL_ADDRESS":
                        filters.add(resolved)
                        continue

                    # BOOLEAN → FILTER
                    if clean in calc_boolean_map or datatype in self.BOOLEAN_DATATYPES:
                        filters.add(resolved)
                        continue

                    if role == "dimension":
                        dimensions.add(resolved)

                    elif role == "measure":
                        measures.add(resolved)

                # -------------------------------
                # ROWS / COLUMNS (visual intent)
                # -------------------------------
                rows = self._parse_shelf(ws, ".//table/rows", calc_caption_map)
                columns = self._parse_shelf(ws, ".//table/cols", calc_caption_map)

                sheets.append({
                    "name": sheet_name,
                    "type": "worksheet",
                    "mark_type": mark_type,
                    "dimensions": sorted(dimensions),
                    "measures": sorted(measures),
                    "rows": rows,
                    "columns": columns,
                    # "marks": {},
                    "filters": sorted(filters)
                })

            self.log_complete({"sheet_count": len(sheets)})
            return {"sheets": sheets}

        except Exception as e:
            self.log_error(e)
            raise

    # -------------------------------
    # Helpers
    # -------------------------------
    def _parse_shelf(self, ws, xpath, calc_caption_map):
        node = ws.find(xpath)
        if node is None or not node.text:
            return []

        fields = []
        for part in node.text.split(","):
            part = part.strip()
            if "." in part:
                part = part.split(".")[-1]

            clean = self._clean_field(part)
            fields.append(self._resolve_calc(clean, calc_caption_map))

        return list(dict.fromkeys(fields))

    def _clean_field(self, field: str) -> str:
        if not field:
            return field

        field = field.strip("[]")

        if "(" in field:
            field = field.split("(")[0].strip()

        if ":" in field:
            parts = field.split(":")
            if len(parts) > 1:
                field = parts[1]

        return field

    def _resolve_calc(self, field: str, calc_caption_map: dict) -> str:
        return calc_caption_map.get(field, field)
