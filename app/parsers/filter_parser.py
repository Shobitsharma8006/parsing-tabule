from app.parsers.base_parser import BaseParser

class FilterParser(BaseParser):
    def parse(self) -> list:
        self.log_start()
        filters_map = {}
        
        # Build ID -> Caption mapping
        caption_map = self._get_caption_map()

        try:
            for worksheet in self.root.findall(".//worksheet"):
                sheet_name = worksheet.attrib.get("name")
                for filter_node in worksheet.findall(".//filter"):
                    raw_id = filter_node.attrib.get("column")
                    if not raw_id:
                        continue
                    
                    # Resolve to caption if it exists, otherwise clean the ID
                    clean_name = caption_map.get(raw_id, self._clean_id(raw_id))
                    
                    if clean_name not in filters_map:
                        filters_map[clean_name] = {
                            "filter_name": clean_name,
                            "type": "categorical",
                            "used_in_sheets": set()
                        }
                    filters_map[clean_name]["used_in_sheets"].add(sheet_name)

            result = [{**v, "used_in_sheets": list(v["used_in_sheets"])} for v in filters_map.values()]
            self.log_complete({"filter_count": len(result)})
            return result
        except Exception as e:
            self.log_error(e)
            raise

    def _get_caption_map(self) -> dict:
        """Parses <column> tags to map technical names to captions."""
        mapping = {}
        for col in self.root.findall(".//column"):
            tech_name = col.attrib.get("name")
            caption = col.attrib.get("caption")
            if tech_name and caption:
                mapping[tech_name] = caption
        return mapping

    def _clean_id(self, tech_id: str) -> str:
        """Fallback to clean IDs like '[none:NAME:nk]' into 'NAME'."""
        if ":" in tech_id:
            return tech_id.split(":")[1].strip("[]")
        return tech_id.strip("[]")