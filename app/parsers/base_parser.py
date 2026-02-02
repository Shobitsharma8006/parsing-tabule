import asyncio
import itertools
from app.services.agent_logger import send_log_to_api


class BaseParser:
    """
    Base class for ALL Parsing Agent parsers.

    Guarantees:
    - Deterministic log ordering
    - Fire-and-forget logging
    - Logging NEVER breaks parsing
    """

    # 🔐 One sequence per parsing run (shared across all parsers)
    _sequence_counter = None

    @classmethod
    def init_sequence(cls):
        cls._sequence_counter = itertools.count(1)

    def __init__(self, root, context=None):
        self.root = root
        self.context = context or {}

    # --------------------------------------------------
    # Internal log emitter
    # --------------------------------------------------
    def _log(self, level: str, message: str, details=None):
        try:
            project_id = self.context.get("project_id")
            workbook_id = self.context.get("workbook_id")
            run_id = self.context.get("run_id")

            if not all([project_id, workbook_id, run_id]):
                return

            if BaseParser._sequence_counter is None:
                BaseParser.init_sequence()

            sequence = next(BaseParser._sequence_counter)

            payload_details = {
                "sequence": sequence,
                "parser": self.__class__.__name__,
                **(details or {})
            }

            asyncio.create_task(
                send_log_to_api(
                    project_id=project_id,
                    workbook_id=workbook_id,
                    run_id=run_id,
                    log_level=level,
                    message=message,
                    details=payload_details,
                )
            )
        except Exception:
            # 🔒 ABSOLUTE SAFETY
            pass

    # --------------------------------------------------
    # Public helpers used by parsers
    # --------------------------------------------------
    def log_start(self):
        self._log("INFO", f"{self.__class__.__name__} started")

    def log_complete(self, details=None):
        self._log("INFO", f"{self.__class__.__name__} completed", details)

    def log_error(self, error: Exception):
        self._log("ERROR", f"{self.__class__.__name__} failed", {
            "error": str(error)
        })
