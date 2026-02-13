from app.parsers.base_parser import BaseParser

class ActionParser(BaseParser):
    def parse(self) -> dict:
        actions = []
        # Standard Filter/URL Actions
        for node in self.root.findall(".//actions/action"):
            actions.append({
                "name": node.attrib.get("caption", node.attrib.get("name")),
                "type": node.find("activation").attrib.get("type", "unknown") if node.find("activation") is not None else "action"
            })

        highlights = []
        # Extract Highlights from Window view states
        for window in self.root.findall(".//windows/window"):
            sheet_name = window.attrib.get("name")
            highlight_node = window.find(".//highlight")
            
            if highlight_node is not None:
                for color_way in highlight_node.findall("color-one-way"):
                    for field in color_way.findall("field"):
                        field_name = field.text.strip("[]")
                        highlights.append({
                            "name": field_name,
                            "type": "Viewpoint Highlight",
                            "field": field_name,
                            "source": sheet_name,
                            "target_sheets": [sheet_name],
                            "expression": f"Static Highlight on [{field_name}]",
                            "values": [],
                            "color": "Default"
                        })
        return {"actions": actions, "highlights": highlights}