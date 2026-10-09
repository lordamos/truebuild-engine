from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class CompanyDossier(Base):
    __tablename__ = "company_dossier"
    
    id = Column(Integer, primary_key=True, index=True)
    legal_name = Column(String, nullable=False)
    dba = Column(String)
    entity_type = Column(String, default='LLC')
    state_of_inc = Column(String, nullable=False)
    date_established = Column(String, nullable=False)
    ein = Column(String, unique=True, index=True, nullable=False)
    duns_number = Column(String)
    industry_naics = Column(String)
    primary_phone = Column(String, nullable=False)
    primary_email = Column(String, nullable=False)
    website = Column(String)
    physical_address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    officer_name = Column(String, nullable=False)
    officer_title = Column(String, default="Managing Member")
    officer_ssn_last4 = Column(String)
    officer_ownership_pct = Column(Float, default=100.0)
    bank_name = Column(String)
    bank_account_type = Column(String)
    compliance_score = Column(Integer, default=0)
    current_unlocked_tier = Column(Integer, default=1)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    tradelines = relationship("Tradeline", back_populates="company", cascade="all, delete-orphan")

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    tier = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    terms = Column(String, nullable=False)
    min_invoice = Column(Float, nullable=False)
    reports_to = Column(String, nullable=False)
    pg_required = Column(Integer, default=0)
    application_url = Column(String, nullable=False)
    application_type = Column(String, default='Online Form')
    underwriting_tips = Column(String)

    tradelines = relationship("Tradeline", back_populates="vendor")

class Tradeline(Base):
    __tablename__ = "tradelines"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company_dossier.id", ondelete="CASCADE"))
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    account_number = Column(String)
    status = Column(String, default="pending")
    credit_limit = Column(Float, default=0.0)
    opened_date = Column(String)

    company = relationship("CompanyDossier", back_populates="tradelines")
    vendor = relationship("Vendor", back_populates="tradelines")
    payments = relationship("PaymentRecord", back_populates="tradeline", cascade="all, delete-orphan")

class PaymentRecord(Base):
    __tablename__ = "payment_records"
    
    id = Column(Integer, primary_key=True, index=True)
    tradeline_id = Column(Integer, ForeignKey("tradelines.id", ondelete="CASCADE"))
    invoice_number = Column(String, nullable=False)
    invoice_amount = Column(Float, nullable=False)
    invoice_date = Column(String, nullable=False)
    due_date = Column(String, nullable=False)
    paid_date = Column(String, nullable=False)
    days_relative_to_due = Column(Integer, nullable=False)

    tradeline = relationship("Tradeline", back_populates="payments")
