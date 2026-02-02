from app.parsers.base_parser import BaseParser

class ActionParser(BaseParser):
    def parse(self) -> dict:
        self.log_start()
        action_list = []
        caption_map = self._get_caption_map()

        try:
            for action in self.root.findall(".//actions/action"):
                raw_name = action.attrib.get("name", "")
                # Prioritize caption from the action tag, then from the global column map
                true_name = action.attrib.get("caption") or caption_map.get(raw_name, raw_name)

                # Safely find child nodes
                activation = action.find("activation")
                source = action.find("source")
                command = action.find("command")

                action_entry = {
                    "@attributes": {
                        "caption": true_name,
                        "name": raw_name
                    },
                    "activation": {
                        "@attributes": {
                            "auto-clear": activation.attrib.get("auto-clear", "true") if activation is not None else "true",
                            "type": activation.attrib.get("type", "on-select") if activation is not None else "on-select"
                        }
                    },
                    "source": {
                        "@attributes": {
                            "datasource": source.attrib.get("datasource") if source is not None else None,
                            "dashboard": source.attrib.get("dashboard") if source is not None else None,
                            "type": source.attrib.get("type", "sheet") if source is not None else "sheet"
                        },
                        "exclude-sheet": [
                            {"@attributes": {"name": s.attrib.get("name")}} 
                            for s in (source.findall(".//exclude-sheet") if source is not None else [])
                        ]
                    },
                    "command": {
                        "@attributes": {
                            "command": command.attrib.get("command", "") if command is not None else ""
                        },
                        "param": [
                            {"@attributes": {"name": p.attrib.get("name"), "value": p.attrib.get("value")}} 
                            for p in (command.findall(".//param") if command is not None else [])
                        ]
                    }
                }
                action_list.append(action_entry)

            result = {
                "@attributes": {},
                "action": action_list
            }

            self.log_complete({"action_count": len(action_list)})
            return result
        except Exception as e:
            self.log_error(e)
            raise

    def _get_caption_map(self) -> dict:
        mapping = {}
        for col in self.root.findall(".//column"):
            name = col.attrib.get("name")
            caption = col.attrib.get("caption")
            if name and caption:
                mapping[name] = caption
        return mapping