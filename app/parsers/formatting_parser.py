from app.parsers.base_parser import BaseParser
import xml.etree.ElementTree as ET

class FormattingParser(BaseParser):
    def parse(self) -> dict:
        self.log_start()
        
        formatting_data = {
            "global_fonts": self._extract_fonts(self.root),
            "custom_color_palettes": self._extract_custom_palettes(),
            "worksheet_styles": {},
            "dashboard_borders": self._extract_dashboard_styles()
        }

        try:
            # Extract Styles per Worksheet
            for worksheet in self.root.findall(".//worksheet"):
                sheet_name = worksheet.attrib.get("name")
                formatting_data["worksheet_styles"][sheet_name] = {
                    "fonts": self._extract_fonts(worksheet),
                    "tooltips": self._extract_tooltips(worksheet),
                    "borders": self._extract_borders(worksheet)
                }

            self.log_complete({"sheets_formatted": len(formatting_data["worksheet_styles"])})
            return formatting_data
        except Exception as e:
            self.log_error(e)
            raise

    def _extract_fonts(self, element) -> list:
        fonts = []
        # Find font definitions in style rules or formatted text runs
        for run in element.findall(".//run"):
            font = run.attrib.get("fontname") or run.attrib.get("family")
            if font and font not in fonts:
                fonts.append(font)
        return fonts

    def _extract_custom_palettes(self) -> list:
        palettes = []
        # Custom colors are often in <encoding attr='color'> within <style>
        for encoding in self.root.findall(".//encoding[@attr='color']"):
            palette_name = encoding.attrib.get("palette")
            if palette_name:
                mappings = []
                for map_node in encoding.findall("map"):
                    mappings.append({
                        "hex": map_node.attrib.get("to"),
                        "value": map_node.find("bucket").text if map_node.find("bucket") is not None else None
                    })
                palettes.append({"palette_name": palette_name, "mappings": mappings})
        return palettes

    def _extract_tooltips(self, worksheet) -> dict:
        tooltip = worksheet.find(".//tooltip")
        if tooltip is not None:
            return {
                "enabled": tooltip.attrib.get("enabled", "true"),
                "text_preview": "".join([t.text for t in tooltip.findall(".//run") if t.text])
            }
        return {"enabled": "false"}

    def _extract_borders(self, element) -> list:
        borders = []
        for format_attr in element.findall(".//format[@attr='border-style']"):
            borders.append({
                "style": format_attr.attrib.get("value"),
                "width": element.find(".//format[@attr='border-width']").attrib.get("value") if element.find(".//format[@attr='border-width']") is not None else "0"
            })
        return borders

    def _extract_dashboard_styles(self) -> list:
        dashboard_styles = []
        for zone in self.root.findall(".//zone-style"):
            border_color = zone.find("./format[@attr='border-color']")
            if border_color is not None:
                dashboard_styles.append({
                    "color": border_color.attrib.get("value"),
                    "margin": zone.find("./format[@attr='margin']").attrib.get("value") if zone.find("./format[@attr='margin']") is not None else "0"
                })
        return dashboard_styles