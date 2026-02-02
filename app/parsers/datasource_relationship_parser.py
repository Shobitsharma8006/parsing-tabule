from app.parsers.base_parser import BaseParser


class DatasourceRelationshipParser(BaseParser):

    def parse(self) -> list:
        self.log_start()

        relationships = []

        try:
            # --------------------------------------------------
            # Build object-id → table caption map
            # --------------------------------------------------
            object_map = {}
            for obj in self.root.findall(".//object-graph/objects/object"):
                object_id = obj.attrib.get("id")
                caption = obj.attrib.get("caption")
                if object_id and caption:
                    object_map[object_id] = caption

            # --------------------------------------------------
            # Parse logical relationships
            # --------------------------------------------------
            for rel in self.root.findall(".//object-graph/relationships/relationship"):
                left_id = rel.find("first-end-point").attrib.get("object-id")
                right_id = rel.find("second-end-point").attrib.get("object-id")

                left_table = object_map.get(left_id)
                right_table = object_map.get(right_id)

                if not left_table or not right_table:
                    continue

                conditions = self._parse_expression(rel.find("expression"))

                cardinality, source = self._infer_cardinality(
                    left_table, right_table, conditions
                )

                relationships.append({
                    "relationship_type": "logical",
                    "from_table": left_table,
                    "to_table": right_table,
                    "cardinality": cardinality,
                    "cardinality_source": source,
                    "join_conditions": [
                        {
                            "left": f"{left_table}.{l}",
                            "operator": "=",
                            "right": f"{right_table}.{r}"
                        }
                        for l, r in conditions
                    ]
                })

            self.log_complete({"relationship_count": len(relationships)})
            return relationships

        except Exception as e:
            self.log_error(e)
            raise

    # --------------------------------------------------
    # Expression parsing
    # --------------------------------------------------
    def _parse_expression(self, expr):
        conditions = []

        if expr is None:
            return conditions

        op = expr.attrib.get("op")

        if op == "=":
            left_expr, right_expr = expr.findall("expression")
            conditions.append([
                self._clean_field(left_expr.attrib.get("op")),
                self._clean_field(right_expr.attrib.get("op"))
            ])

        elif op == "AND":
            for child in expr.findall("expression"):
                conditions.extend(self._parse_expression(child))

        return conditions

    # --------------------------------------------------
    # Field cleanup
    # --------------------------------------------------
    def _clean_field(self, field: str) -> str:
        if not field:
            return field

        field = field.strip("[]")

        if "(" in field:
            field = field.split("(")[0].strip()

        return field

    # --------------------------------------------------
    # Cardinality inference (Tableau-correct)
    # --------------------------------------------------
    def _infer_cardinality(self, left_table, right_table, conditions):
        """
        Tableau rules:
        - Missing cardinality in XML = implicit MANY-TO-MANY
        - Only explicit overrides appear in XML
        """

        aggregate_keywords = [
            "snapshot", "aggregated", "monthly", "latest", "summary"
        ]

        # Heuristic: aggregate tables
        if any(k in left_table.lower() for k in aggregate_keywords) or \
           any(k in right_table.lower() for k in aggregate_keywords):
            return "one-to-many", "heuristic"

        # Composite join keys → many-to-many
        if len(conditions) > 1:
            return "many-to-many", "heuristic"

        # Common dimensional joins
        key_terms = ["state", "date", "fips"]
        for l, r in conditions:
            if any(k in l.lower() for k in key_terms) and \
               any(k in r.lower() for k in key_terms):
                return "many-to-many", "heuristic"

        # ✅ DEFAULT TABLEAU BEHAVIOR
        return "many-to-many", "implicit_default"
