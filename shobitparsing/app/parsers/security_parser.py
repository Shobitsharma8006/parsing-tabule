from app.parsers.base_parser import BaseParser


class SecurityParser(BaseParser):

    def parse(self) -> dict:
        self.log_start()

        try:
            has_rls = self.root.find(".//userfilter") is not None

            self.log_complete({
                "row_level_security": has_rls
            })

            return {
                "row_level_security": has_rls
            }

        except Exception as e:
            self.log_error(e)
            raise
