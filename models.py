# File: models.py
from sqlalchemy.orm import relationship, declared_attr
from database       import Base
from sqlalchemy     import (
    Column, Integer, String, ForeignKey,
    DateTime, func, Text, Numeric, UniqueConstraint
)


# ────────────────────────────────────────────────────────────────────────────
# 공통 믹스인 클래스 정의
class TimestampMixin:
    """생성 시각(created_at) 공통 정의"""

    created_at = Column(
        DateTime, nullable=False,
        server_default=func.now() # 값이 자동으로 설정되는 생성 시각
    )


class UserMixin:
    """user_id 공통 정의 (index 포함)"""

    @declared_attr
    def user_id(cls):
        return Column(
            Integer, ForeignKey("user.id"),
            nullable=False, index=True
        )


# ────────────────────────────────────────────────────────────────────────────
class Institution(Base, TimestampMixin):
    """은행 기관 정보 모델"""

    __tablename__ = "institution"

    code = Column(String(4), primary_key=True)
    name = Column(String(100), nullable=False)

    internet_bankings = relationship("InternetBanking", back_populates="institution")
    accounts          = relationship("Account", back_populates="institution")


class User(Base, TimestampMixin):
    """사용자 정보 모델"""

    __tablename__ = "user"

    id            = Column(Integer, primary_key=True)
    username      = Column(String, unique=True, nullable=False)
    password      = Column(String, nullable=False)
    email         = Column(String, unique=True, nullable=False)
    round_up_unit = Column(Integer, nullable=False, default=100)


    internet_bankings = relationship("InternetBanking", back_populates="user")
    accounts          = relationship("Account", back_populates="user")
    spare_changes     = relationship("SpareChange", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base, UserMixin, TimestampMixin):
    """
    개별 계좌의 거래 내역을 기록합니다.
    - tx_type: 'withdraw', 'deposit', 'fee' 등
    - 잔돈 라운드-업 대상은 보통 'withdraw' 계열만 필터링합니다.
    """
    __tablename__ = "transaction"

    id          = Column(String(64), primary_key=True) # 외부 시스템 연동 고려
    account_id  = Column(Integer, ForeignKey("account.id"), nullable=False, index=True)
    amount      = Column(Numeric(18, 2), nullable=False)
    tx_type     = Column(String(20), nullable=False)
    memo        = Column(Text, nullable=True)

    account      = relationship("Account", back_populates="transactions")
    spare_change = relationship("SpareChange", uselist=False, back_populates="transaction")


class InternetBanking(Base, UserMixin, TimestampMixin):
    """인터넷 뱅킹 정보 모델"""

    __tablename__        = "internet_banking"

    id                   = Column(Integer, primary_key=True, index=True)
    institution_code     = Column(String(4), ForeignKey("institution.code"), nullable=False, index=True)
    banking_id           = Column(String(32), unique=True, nullable=False)
    banking_password_enc = Column(Text, nullable=False)

    user                 = relationship("User", back_populates="internet_bankings")
    institution          = relationship("Institution", back_populates="internet_bankings")


class Account(Base, UserMixin, TimestampMixin):
    """사용자 계좌 정보 모델"""

    __tablename__        = "account"

    id                   = Column(Integer, primary_key=True, index=True)
    institution_code     = Column(String(4), ForeignKey("institution.code"), nullable=False, index=True)
    account_number       = Column(String(20), unique=True, nullable=False)
    account_password_enc = Column(Text, nullable=False)

    user                 = relationship("User", back_populates="accounts")
    institution          = relationship("Institution", back_populates="accounts")
    transactions         = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class SpareChange(Base, TimestampMixin):
    """
    거래 금액(amount) 기준으로 계산된 라운드-업 잔돈을 저장.
    PK = (user_id, tx_id) 중복 방지.
    """
    __tablename__       = "spare_change"

    user_id              = Column(Integer, ForeignKey("user.id"), primary_key=True)
    tx_id                = Column(Integer, ForeignKey("transaction.id"), primary_key=True)
    round_up             = Column(Numeric(14, 2), nullable=False, doc="라운드-업 금액")

    user                 = relationship("User", back_populates="spare_changes")
    transaction          = relationship("Transaction", back_populates="spare_change")

    # 중복 방지: 동일 사용자와 거래 ID에 대해 하나의 잔돈만 저장
    __table_args__ = (
        UniqueConstraint(
            "user_id", "tx_id",
            name="uix_spare_change_user_tx"
        ),
    )
