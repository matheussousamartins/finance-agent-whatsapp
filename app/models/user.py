from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.models.transaction import Base


class OnboardingStep:
    WAITING_NAME = "waiting_name"
    WAITING_BUDGET = "waiting_budget"
    DONE = "done"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    monthly_budget = Column(Float, nullable=True)
    onboarding_step = Column(String, default=OnboardingStep.WAITING_NAME)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User phone={self.phone} name={self.name} step={self.onboarding_step}>"

    def is_onboarding_done(self) -> bool:
        return self.onboarding_step == OnboardingStep.DONE