from app.parsers.base_parser import BaseParser

class FilterParser(BaseParser):
    def parse(self) -> list:
        filters_map = {}
        # Iterate all worksheets to find active filters
        for ws in self.root.findall(".//worksheets/worksheet"):
            ws_name = ws.attrib.get("name")
            for f in ws.findall(".//table/view/filter"):
                raw_col = f.attrib.get("column", "")
                # Format is usually [datasource].[Field Name]
                clean_name = raw_col.split(".")[-1].strip("[]")
                f_type = f.attrib.get("class", "categorical")

                if clean_name not in filters_map:
                    filters_map[clean_name] = {
                        "filter_name": clean_name,
                        "type": f_type,
                        "used_in_sheets": []
                    }
                if ws_name not in filters_map[clean_name]["used_in_sheets"]:
                    filters_map[clean_name]["used_in_sheets"].append(ws_name)
                    
        return list(filters_map.values())