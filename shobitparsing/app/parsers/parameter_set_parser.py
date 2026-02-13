 

from app.parsers.base_parser import BaseParser
import re


class ParameterSetParser(BaseParser):

    def parse(self) -> dict:
        self.log_start()

        try:
            result = {
                "parameters": self._parse_parameters(),
                "sets": self._parse_sets()
            }

            self.log_complete({
                "parameter_count": len(result["parameters"]),
                "set_count": len(result["sets"])
            })

            return result

        except Exception as e:
            self.log_error(e)
            raise

    # ==================================================
    # PARAMETERS
    # ==================================================
    def _parse_parameters(self) -> dict:
        parameters = {}

        for ds in self.root.findall(".//datasource-dependencies[@datasource='Parameters']"):
            for col in ds.findall(".//column"):
                name = col.attrib.get("caption") or col.attrib.get("name")
                if not name:
                    continue

                name = name.strip("[]")

                param_type = col.attrib.get("param-domain-type")
                current_value = col.attrib.get("value")

                param_info = {
                    "datatype": col.attrib.get("datatype"),
                    "current_value": current_value,
                    "allowable_values": None,
                    "range": None
                }

                range_node = col.find("range")
                if range_node is not None:
                    param_info["allowable_values"] = "range"
                    param_info["range"] = {
                        "min": range_node.attrib.get("min"),
                        "max": range_node.attrib.get("max"),
                        "step": range_node.attrib.get("granularity")
                    }
                elif param_type == "list":
                    param_info["allowable_values"] = "list"

                parameters[name] = param_info

        return parameters

    # ==================================================
    # SETS (FIXED vs DYNAMIC — CORRECT TABLEAU LOGIC)
    # ==================================================
    def _parse_sets(self) -> dict:
        sets = {}

        for group in self.root.findall(".//group"):
            group_class = group.attrib.get("class") or group.attrib.get("type")
            if group_class not in ("set", None):
                continue

            name = group.attrib.get("caption") or group.attrib.get("name")
            if not name:
                continue
            name = name.strip("[]")

            expr = group.find(".//expression")
            gf = group.find("groupfilter")
            members = group.findall(".//member")

            base_field = None

            # -------------------------------
            # EXPRESSION → DYNAMIC SET
            # -------------------------------
            if expr is not None:
                formula = expr.attrib.get("formula")
                refs = re.findall(r"\[([^\]]+)\]", formula or "")
                if refs:
                    base_field = refs[-1]

                entry = {
                    "type": "dynamic",
                    "base_field": base_field
                }

                if formula:
                    entry["formula"] = formula

                sets[name] = entry
                continue

            # -------------------------------
            # GROUPFILTER
            # -------------------------------
            if gf is not None:
                member_attr = gf.attrib.get("member")

                # member-based → FIXED
                if member_attr:
                    base_field = member_attr.strip("[]")
                    sets[name] = {
                        "type": "fixed",
                        "base_field": base_field
                    }
                else:
                    # no explicit member → dynamic condition
                    sets[name] = {
                        "type": "dynamic",
                        "base_field": None
                    }
                continue

            # -------------------------------
            # MEMBER LIST → FIXED
            # -------------------------------
            if members:
                field_attr = members[0].attrib.get("field")
                if field_attr:
                    base_field = field_attr.strip("[]")

                sets[name] = {
                    "type": "fixed",
                    "base_field": base_field
                }

        return sets


