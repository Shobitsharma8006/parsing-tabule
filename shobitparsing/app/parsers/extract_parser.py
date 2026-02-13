from app.parsers.base_parser import BaseParser


class CustomSQLParser(BaseParser):

    def parse(self) -> dict:
        sql_blocks = []

        for rel in self.root.findall(".//relation[@type='text']"):
            sql = rel.text.strip() if rel.text else ""

            sql_blocks.append({
                "sql": sql,
                "line_count": len(sql.splitlines())
            })

        return {
            "custom_sql_present": len(sql_blocks) > 0,
            "custom_sql_blocks": sql_blocks
        }


class ExtractParser(BaseParser):

    def parse(self) -> dict:
        extracts = self.root.findall(".//extract")

        return {
            "extract_count": len(extracts),
            "uses_extract": len(extracts) > 0
        }
