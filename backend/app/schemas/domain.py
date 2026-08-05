"""Domain CRUD schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import (
    AccountKind,
    CardNetwork,
    CardStatus,
    DueRuleType,
    LineReviewStatus,
    PostingStatus,
    SettlementMethod,
    StatementStatus,
    TransactionType,
)
from app.models.category import CategoryKind
from app.schemas.common import ORMModel

# ---- Contacts ----


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    archived: bool | None = None


class ContactResponse(ORMModel):
    id: UUID
    organization_id: UUID
    name: str
    phone: str | None
    email: str | None
    notes: str | None
    tags: list[str] | None
    archived_at: datetime | None
    outstanding_paise: int | None = None
    created_at: datetime
    updated_at: datetime


# ---- Cards ----


class CreditCardCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=120)
    issuer: str = Field(min_length=1, max_length=120)
    network: CardNetwork = CardNetwork.OTHER
    last_four: str = Field(min_length=4, max_length=4)
    credit_limit_paise: int = Field(gt=0)
    currency: str = "INR"
    statement_day: int = Field(ge=1, le=31)
    due_rule_type: DueRuleType
    due_rule_value: int = Field(ge=1, le=31)
    held_by_contact_id: UUID | None = None
    notes: str | None = None
    opening_balance_paise: int | None = Field(default=None, ge=0)

    @field_validator("last_four")
    @classmethod
    def digits_only(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("last_four must be 4 digits")
        return value


class CreditCardUpdate(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=120)
    issuer: str | None = None
    network: CardNetwork | None = None
    credit_limit_paise: int | None = Field(default=None, gt=0)
    statement_day: int | None = Field(default=None, ge=1, le=31)
    due_rule_type: DueRuleType | None = None
    due_rule_value: int | None = Field(default=None, ge=1, le=31)
    status: CardStatus | None = None
    held_by_contact_id: UUID | None = None
    notes: str | None = None


class CreditCardResponse(ORMModel):
    id: UUID
    organization_id: UUID
    nickname: str
    issuer: str
    network: CardNetwork
    last_four: str
    credit_limit_paise: int
    currency: str
    statement_day: int
    due_rule_type: DueRuleType
    due_rule_value: int
    status: CardStatus
    held_by_contact_id: UUID | None
    notes: str | None
    outstanding_paise: int | None = None
    available_credit_paise: int | None = None
    utilization_percent: float | None = None
    next_statement_date: date | None = None
    next_due_date: date | None = None
    created_at: datetime
    updated_at: datetime


# ---- Transactions ----


class TransactionCreate(BaseModel):
    account_id: UUID | None = None
    credit_card_id: UUID | None = None
    type: TransactionType
    amount_paise: int = Field(gt=0)
    occurred_at: datetime
    merchant: str = Field(min_length=1, max_length=255)
    contact_id: UUID | None = None
    category_id: UUID | None = None
    category: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    currency: str = "INR"
    posting_status: PostingStatus = PostingStatus.POSTED
    transfer_group_id: UUID | None = None


class TransactionUpdate(BaseModel):
    type: TransactionType | None = None
    amount_paise: int | None = Field(default=None, gt=0)
    occurred_at: datetime | None = None
    merchant: str | None = None
    contact_id: UUID | None = None
    category_id: UUID | None = None
    category: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class TransactionReverseRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)
    occurred_at: datetime | None = None


class TransactionAdjustRequest(BaseModel):
    account_id: UUID | None = None
    credit_card_id: UUID | None = None
    delta_paise: int  # signed; must be non-zero (enforced in service)
    reason: str = Field(min_length=1, max_length=2000)
    contact_id: UUID | None = None
    occurred_at: datetime | None = None
    merchant: str | None = Field(default=None, min_length=1, max_length=255)


class TransactionSplitBase(BaseModel):
    category_id: UUID | None = None
    amount_paise: int = Field(gt=0)
    notes: str | None = None
    tags: list[str] | None = None

class TransactionSplitResponse(TransactionSplitBase, ORMModel):
    id: UUID
    transaction_id: UUID

class TransactionResponse(ORMModel):
    id: UUID
    organization_id: UUID
    account_id: UUID
    credit_card_id: UUID | None
    contact_id: UUID | None
    statement_id: UUID | None
    type: TransactionType
    posting_status: PostingStatus
    amount_paise: int
    currency: str
    occurred_at: datetime
    merchant: str
    category: str | None
    category_id: UUID | None
    transfer_group_id: UUID | None
    tags: list[str] | None
    notes: str | None
    correction_reason: str | None
    delta_sign: int | None
    reverses_id: UUID | None
    reversed_by_id: UUID | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    splits: list[TransactionSplitResponse] = Field(default_factory=list)


# ---- Transfers ----

class TransferCreate(BaseModel):
    from_account_id: UUID
    to_account_id: UUID
    amount_paise: int = Field(gt=0)
    occurred_at: datetime
    notes: str | None = None
    tags: list[str] | None = None

class TransferResponse(BaseModel):
    transfer_group_id: UUID
    out_transaction: TransactionResponse
    in_transaction: TransactionResponse

# ---- Categories ----

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: CategoryKind
    color: str | None = Field(default=None, max_length=30)
    icon: str | None = Field(default=None, max_length=50)

class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    kind: CategoryKind | None = None
    color: str | None = Field(default=None, max_length=30)
    icon: str | None = Field(default=None, max_length=50)
    archived: bool | None = None

class CategoryResponse(ORMModel):
    id: UUID
    org_id: UUID
    name: str
    kind: CategoryKind
    color: str | None
    icon: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

# ---- Settlements ----


class SettlementCreate(BaseModel):
    contact_id: UUID
    amount_paise: int = Field(gt=0)
    settled_at: datetime
    method: SettlementMethod
    notes: str | None = None
    currency: str = "INR"


class SettlementResponse(ORMModel):
    id: UUID
    organization_id: UUID
    contact_id: UUID
    amount_paise: int
    currency: str
    settled_at: datetime
    method: SettlementMethod
    notes: str | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


# ---- Statements ----


class StatementCreate(BaseModel):
    credit_card_id: UUID
    period_start: date | None = None
    period_end: date | None = None
    statement_date: date | None = None
    due_date: date | None = None
    pdf_storage_path: str | None = None


class StatementResponse(ORMModel):
    id: UUID
    organization_id: UUID
    credit_card_id: UUID
    period_start: date | None
    period_end: date | None
    statement_date: date | None
    due_date: date | None
    pdf_storage_path: str | None
    status: StatementStatus
    parse_error: str | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    lines_count: int | None = None
    pending_count: int | None = None
    accepted_count: int | None = None
    imported_count: int | None = None


class StatementLineResponse(ORMModel):
    id: UUID
    statement_id: UUID
    organization_id: UUID
    raw_payload: dict[str, object] | None
    occurred_at: datetime | None
    merchant: str | None
    amount_paise: int | None
    proposed_type: TransactionType | None
    proposed_contact_id: UUID | None
    review_status: LineReviewStatus
    committed_transaction_id: UUID | None
    created_at: datetime
    updated_at: datetime


class StatementDetailResponse(StatementResponse):
    lines: list[StatementLineResponse] = Field(default_factory=list)


class StatementLineUpdate(BaseModel):
    review_status: LineReviewStatus | None = None
    merchant: str | None = Field(default=None, min_length=1, max_length=255)
    amount_paise: int | None = Field(default=None, gt=0)
    occurred_at: datetime | None = None
    proposed_type: TransactionType | None = None
    proposed_contact_id: UUID | None = None
    clear_contact: bool = False


class StatementBulkReview(BaseModel):
    review_status: LineReviewStatus
    only_pending: bool = True


class StatementImportResult(BaseModel):
    created: int
    skipped: int
    status: StatementStatus
    statement: StatementResponse


# ---- Notifications ----


class NotificationResponse(ORMModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    type: str
    title: str
    body: str
    href: str | None
    read_at: datetime | None
    created_at: datetime


class NotificationUnreadCount(BaseModel):
    unread: int


class NotificationMarkReadResult(BaseModel):
    updated: int


# ---- Dashboard ----


class AttentionItem(BaseModel):
    id: str
    severity: str  # critical | warning | info
    title: str
    detail: str
    href: str | None = None


class DashboardCardSummary(BaseModel):
    id: UUID
    nickname: str
    issuer: str
    last_four: str
    network: CardNetwork
    credit_limit_paise: int
    outstanding_paise: int
    available_credit_paise: int
    utilization_percent: float
    next_due_date: date | None
    next_statement_date: date | None
    status: CardStatus


class DashboardContactSummary(BaseModel):
    id: UUID
    name: str
    outstanding_paise: int
    updated_at: datetime


class DashboardResponse(BaseModel):
    total_credit_limit_paise: int
    total_outstanding_paise: int
    total_available_credit_paise: int
    total_friend_dues_paise: int
    cards_count: int
    contacts_count: int
    transactions_count: int
    attention: list[AttentionItem] = Field(default_factory=list)
    cards: list[DashboardCardSummary] = Field(default_factory=list)
    top_contacts: list[DashboardContactSummary] = Field(default_factory=list)


# ---- Accounts ----


class AccountCreate(BaseModel):
    kind: AccountKind
    name: str = Field(min_length=1, max_length=120)
    institution: str | None = Field(default=None, max_length=120)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    opening_balance_paise: int | None = Field(default=None, ge=0)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    institution: str | None = Field(default=None, max_length=120)


class CorrectBalanceRequest(BaseModel):
    target_balance_paise: int
    reason: str = Field(min_length=1, max_length=2000)
    occurred_at: datetime | None = None


class AccountResponse(ORMModel):
    id: UUID
    organization_id: UUID
    kind: AccountKind
    name: str
    institution: str | None
    currency: str
