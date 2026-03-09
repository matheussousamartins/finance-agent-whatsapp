from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from app.models.transaction import Base


class OnboardingStep:
    WAITING_NAME = "waiting_name"
    WAITING_BUDGET = "waiting_budget"
    DONE = "done"


class PlanStatus:
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    monthly_budget = Column(Float, nullable=True)
    onboarding_step = Column(String, default=OnboardingStep.WAITING_NAME)

    # Plano e trial
    plan = Column(String, default="free")              # "free", "mensal", "trimestral", "semestral"
    plan_status = Column(String, default=PlanStatus.TRIAL)  # "trial", "active", "expired"
    trial_start = Column(DateTime, default=datetime.utcnow)
    plan_expires_at = Column(DateTime, nullable=True)  # data de expiração do plano pago

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User phone={self.phone} name={self.name} plan={self.plan} status={self.plan_status}>"

    def is_onboarding_done(self) -> bool:
        return self.onboarding_step == OnboardingStep.DONE

    def is_trial_active(self) -> bool:
        if not self.trial_start:
            return False
        days = (datetime.utcnow() - self.trial_start).days
        return days < 7

    def is_plan_active(self) -> bool:
        if not self.plan_expires_at:
            return False
        return datetime.utcnow() < self.plan_expires_at

    def has_access(self) -> bool:
        """Verifica se o usuário tem acesso ao sistema."""
        return self.is_trial_active() or self.is_plan_active()