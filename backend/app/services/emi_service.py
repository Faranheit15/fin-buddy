"""Service for managing EMIs."""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta  # type: ignore

from app.models.emi import EmiInstallment
from app.models.enums import EmiInstallmentStatus


def generate_emi_schedule(
    principal_paise: int,
    interest_rate_bps: int,
    tenure_months: int,
    start_date: date,
) -> list[EmiInstallment]:
    """
    Generate an EMI schedule.
    
    Args:
        principal_paise: Total principal amount in paise.
        interest_rate_bps: Annual interest rate in basis points (e.g. 1500 for 15%).
        tenure_months: Number of months for the EMI.
        start_date: The date of the first installment.
        
    Returns:
        List of EmiInstallment objects (without plan_id/id bound).
    """
    if tenure_months <= 0:
        raise ValueError("Tenure must be at least 1 month")
        
    # Standard reducing balance EMI formula:
    # EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    # where P = principal, r = monthly interest rate, n = tenure
    
    monthly_rate = Decimal(interest_rate_bps) / Decimal(10000) / Decimal(12)
    principal = Decimal(principal_paise)
    n = tenure_months
    
    if monthly_rate > 0:
        factor = (1 + monthly_rate) ** n
        emi_amount = principal * monthly_rate * factor / (factor - 1)
    else:
        emi_amount = principal / n
        
    # We round the EMI amount to the nearest paise
    emi_amount_paise = int(emi_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    
    installments = []
    remaining_principal = principal
    
    for month in range(1, tenure_months + 1):
        due_date = start_date + relativedelta(months=month - 1)
        
        interest_for_month = remaining_principal * monthly_rate
        interest_paise = int(interest_for_month.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        
        # GST is 18% on interest
        gst_for_month = Decimal(interest_paise) * Decimal("0.18")
        gst_paise = int(gst_for_month.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        
        if month == tenure_months:
            # Last month absorbs remainder
            principal_for_month = int(remaining_principal)
        else:
            principal_for_month = emi_amount_paise - interest_paise
            
        remaining_principal -= Decimal(principal_for_month)
        total_installment = principal_for_month + interest_paise + gst_paise
        
        installment = EmiInstallment(
            sequence_number=month,
            due_date=due_date,
            principal_paise=principal_for_month,
            interest_paise=interest_paise,
            fees_paise=0,
            gst_paise=gst_paise,
            total_paise=total_installment,
            status=EmiInstallmentStatus.PENDING,
        )
        installments.append(installment)
        
    return installments
