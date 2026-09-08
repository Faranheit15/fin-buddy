"""Shared statement upload and parser budgets with no application imports."""

DEFAULT_STATEMENT_MAX_UPLOAD_BYTES = 15 * 1024 * 1024
DEFAULT_STATEMENT_UPLOAD_TTL_SECONDS = 15 * 60
DEFAULT_STATEMENT_ABANDON_AFTER_SECONDS = 60 * 60

PARSER_MAX_ROWS = 10_000
PARSER_MAX_COLUMNS = 100
PARSER_MAX_SHEETS = 10
PARSER_MAX_PDF_PAGES = 50
PARSER_MAX_DECOMPRESSED_BYTES = 64 * 1024 * 1024
PARSER_MAX_LINES = 10_000
PARSER_MAX_TEXT_CHARS = 1_000_000

SUPPORTED_STATEMENT_MIME_TYPES = (
    "application/pdf",
    "text/plain",
    "text/csv",
    "text/tab-separated-values",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
