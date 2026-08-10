"""CSV and Excel statement parser."""

from __future__ import annotations

import io

import pandas as pd

from app.core.exceptions import AppError
from app.models.enums import TransactionType
from app.services.parsers.base import ParsedLine, ParseResult


class CsvExcelParser:
    name = "csv_excel_parser"

    def parse_bytes(self, data: bytes, filename: str, *, issuer: str | None = None) -> ParseResult:
        try:
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(io.BytesIO(data))
            else:
                df = pd.read_excel(io.BytesIO(data))
        except Exception as exc:
            raise AppError(
                f"Failed to read file as tabular data: {exc}", code="tabular_read_failed"
            ) from exc

        # Basic column normalization
        # We look for common headers: Date, Description, Amount, Type (or Debit/Credit)
        cols = {c.lower().strip(): c for c in df.columns}

        date_col = next((c for c in cols if "date" in c or "time" in c), None)
        desc_col = next(
            (
                c
                for c in cols
                if "desc" in c or "merchant" in c or "narrative" in c or "particulars" in c
            ),
            None,
        )
        amt_col = next((c for c in cols if "amount" in c or "value" in c), None)

        # Sometimes there's separate Debit and Credit columns
        debit_col = next((c for c in cols if "debit" in c or "withdrawal" in c), None)
        credit_col = next((c for c in cols if "credit" in c or "deposit" in c), None)
        type_col = next((c for c in cols if "type" in c or "cr/dr" in c), None)

        if not date_col or not desc_col:
            raise AppError("Missing required columns: Date, Description", code="missing_columns")

        if not amt_col and not (debit_col or credit_col):
            raise AppError("Missing Amount or Debit/Credit columns", code="missing_columns")

        lines = []
        for _, row in df.iterrows():
            # Parse Date
            raw_date = str(row[cols[date_col]]) if not pd.isna(row[cols[date_col]]) else ""
            if not raw_date.strip():
                continue

            try:
                # pandas to_datetime handles many formats
                dt = pd.to_datetime(raw_date)
                occurred_at = dt.to_pydatetime()
            except Exception:
                occurred_at = None

            # Parse Description
            merchant = str(row[cols[desc_col]]) if not pd.isna(row[cols[desc_col]]) else "Unknown"

            # Parse Amount and Type
            amount = 0.0
            tx_type = TransactionType.PURCHASE

            if amt_col and not pd.isna(row[cols[amt_col]]):
                amount_str = str(row[cols[amt_col]]).replace(",", "").strip()
                try:
                    amount = abs(float(amount_str))
                except ValueError:
                    amount = 0.0

                # Determine type from type_col or sign
                if type_col and not pd.isna(row[cols[type_col]]):
                    t_val = str(row[cols[type_col]]).lower().strip()
                    if t_val in ["cr", "credit", "deposit", "payment"]:
                        tx_type = TransactionType.PAYMENT_TO_ISSUER
                    else:
                        tx_type = TransactionType.PURCHASE
                else:
                    if amount_str.startswith("-"):
                        # Sometimes negative is spend, sometimes payment. Assume negative = payment for cards?
                        # Actually standard: positive spend, negative payment (or vice versa).
                        # Let's assume negative means credit (payment to card)
                        tx_type = TransactionType.PAYMENT_TO_ISSUER
                    else:
                        tx_type = TransactionType.PURCHASE

            elif debit_col and not pd.isna(row[cols[debit_col]]):
                try:
                    amount = float(str(row[cols[debit_col]]).replace(",", "").strip())
                    tx_type = TransactionType.PURCHASE
                except ValueError:
                    pass
            elif credit_col and not pd.isna(row[cols[credit_col]]):
                try:
                    amount = float(str(row[cols[credit_col]]).replace(",", "").strip())
                    tx_type = TransactionType.PAYMENT_TO_ISSUER
                except ValueError:
                    pass

            if amount == 0:
                continue

            amount_paise = int(round(amount * 100))

            lines.append(
                ParsedLine(
                    occurred_at=occurred_at,
                    merchant=merchant[:255],
                    amount_paise=amount_paise,
                    proposed_type=tx_type,
                    raw={str(k): v for k, v in row.to_dict().items()},
                )
            )

        return ParseResult(lines=lines, parser_name="csv_excel")
