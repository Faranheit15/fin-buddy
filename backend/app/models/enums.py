"""PostgreSQL-backed enums used across the domain."""

import enum


class PlatformRole(enum.StrEnum):
    """Application-wide role (admin panel access)."""

    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class OrgRole(enum.StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class CardStatus(enum.StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"


class CardNetwork(enum.StrEnum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    RUPAY = "rupay"
    AMEX = "amex"
    OTHER = "other"


class DueRuleType(enum.StrEnum):
    FIXED_DAY = "fixed_day"
    DAYS_AFTER_STATEMENT = "days_after_statement"


class TransactionType(enum.StrEnum):
    PURCHASE = "purchase"
    REFUND = "refund"
    FEE = "fee"
    INTEREST = "interest"
    PAYMENT_TO_ISSUER = "payment_to_issuer"
    OPENING_BALANCE = "opening_balance"
    ADJUSTMENT = "adjustment"
    REVERSAL = "reversal"
    TRANSFER_OUT = "transfer_out"
    TRANSFER_IN = "transfer_in"


class PostingStatus(enum.StrEnum):
    DRAFT = "draft"
    POSTED = "posted"


class AccountKind(enum.StrEnum):
    BANK = "bank"
    CASH = "cash"
    WALLET = "wallet"
    CREDIT_CARD = "credit_card"


class SettlementMethod(enum.StrEnum):
    UPI = "upi"
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    OTHER = "other"


class StatementStatus(enum.StrEnum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    NEEDS_REVIEW = "needs_review"
    IMPORTED = "imported"
    FAILED = "failed"


class LineReviewStatus(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EDITED = "edited"


class ActivityAction(enum.StrEnum):
    """High-level user/admin actions for the activity log."""

    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"
    TOKEN_REFRESH = "token_refresh"
    PROFILE_UPDATE = "profile_update"
    ORG_CREATE = "org_create"
    ORG_UPDATE = "org_update"
    MEMBER_INVITE = "member_invite"
    MEMBER_UPDATE = "member_update"
    MEMBER_REMOVE = "member_remove"
    CARD_CREATE = "card_create"
    CARD_UPDATE = "card_update"
    CARD_ARCHIVE = "card_archive"
    CONTACT_CREATE = "contact_create"
    CONTACT_UPDATE = "contact_update"
    CONTACT_ARCHIVE = "contact_archive"
    TRANSACTION_CREATE = "transaction_create"
    TRANSACTION_UPDATE = "transaction_update"
    TRANSACTION_DELETE = "transaction_delete"
    TRANSACTION_POST = "transaction_post"
    TRANSACTION_REVERSE = "transaction_reverse"
    TRANSACTION_ADJUST = "transaction_adjust"
    SETTLEMENT_CREATE = "settlement_create"
    SETTLEMENT_UPDATE = "settlement_update"
    SETTLEMENT_DELETE = "settlement_delete"
    STATEMENT_UPLOAD = "statement_upload"
    STATEMENT_REVIEW = "statement_review"
    STATEMENT_IMPORT = "statement_import"
    NOTIFICATION_READ = "notification_read"
    ADMIN_VIEW = "admin_view"
    ADMIN_ACTION = "admin_action"
    API_REQUEST = "api_request"
    OTHER = "other"


class ErrorSeverity(enum.StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
