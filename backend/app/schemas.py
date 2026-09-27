from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class RegisterIn(LoginIn):
    name: str
    role: str = "underwriter"

class CustomerIn(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    annual_income: float
    employment_type: str = "Salaried"

class ApplicationIn(BaseModel):
    customer_id: int
    product: str = "Personal Loan"
    amount: float
    tenure_months: int
    purpose: str = ""
    credit_score: int = 700
    monthly_debt: float = 0

class DocumentIn(BaseModel):
    application_id: int
    document_type: str
    file_name: str
    extracted_summary: str = ""

class StatusIn(BaseModel):
    status: str

class ReviewIn(BaseModel):
    decision: str
    note: str = ""

class NotifyIn(BaseModel):
    channel: str = "Email"
    message: Optional[str] = None
