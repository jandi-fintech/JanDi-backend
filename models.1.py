# File: models.py
from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    DateTime, func, Text, Numeric, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


# ────────────────────────────────────────────────────────────────────────────
class Institution(Base):
    """은행 기관 정보 모델"""
    
    __tablename__        = "institution"
    
    code                 = Column(String(4), primary_key=True)
    name                 = Column(String(100), nullable=False)
    created_at           = Column(
        DateTime, nullable=False, 
        server_default=func.now() # 값이 자동으로 설정되는 생성 시각
        ) 
    
    internet_bankings    = relationship("InternetBanking", back_populates="institution")
    accounts             = relationship("Account", back_populates="institution")


# ────────────────────────────────────────────────────────────────────────────
class User(Base):
    """사용자 정보 모델"""
    
    __tablename__        = "user"
    
    id                   = Column(Integer, primary_key=True)
    username             = Column(String, unique=True, nullable=False)
    password             = Column(String, nullable=False)
    email                = Column(String, unique=True, nullable=False)
    created_at           = Column(DateTime, nullable=False, server_default=func.now())
    
    internet_bankings    = relationship("InternetBanking", back_populates="user")
    accounts             = relationship("Account", back_populates="user")
    
    # 라운드-업 단위 설정 (유저별 또는 시스템 전체)
    round_up_configs  = relationship(
        "RoundUpConfig",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # 잔돈(라운드-업) 내역
    spare_changes     = relationship(
        "SpareChange",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# ────────────────────────────────────────────────────────────────────────────
class InternetBanking(Base):
    """인터넷 뱅킹 정보 모델"""
    
    __tablename__        = "internet_banking"
    
    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    institution_code     = Column(String(4), ForeignKey("institution.code"), nullable=False, index=True)
    
    banking_id           = Column(String(32), unique=True, nullable=False)
    banking_password_enc = Column(Text, nullable=False)
    created_at           = Column(DateTime, nullable=False, server_default=func.now())
    
    user                 = relationship("User", back_populates="internet_bankings")
    institution          = relationship("Institution", back_populates="internet_bankings")


# ────────────────────────────────────────────────────────────────────────────
class Account(Base):
    """ 사용자 계좌 정보 모델 """
    
    __tablename__        = "account"
    
    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    institution_code     = Column(String(4), ForeignKey("institution.code"), nullable=False, index=True)
    
    account_number       = Column(String(20), unique=True, nullable=False)
    account_password_enc = Column(Text, nullable=False)
    created_at           = Column(DateTime, nullable=False, server_default=func.now())
    
    user                 = relationship("User", back_populates="accounts")
    institution          = relationship("Institution", back_populates="accounts")


# ────────────────────────────────────────────────────────────────────────────
class RoundUpConfig(Base):
    """
    라운드-업 단위를 동적으로 관리.
    시스템 전체 또는 유저별 단위 설정 가능.
    """

    __tablename__ = "round_up_config"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("user.id"), nullable=True)
    unit       = Column(Integer, nullable=False)  # ex) 10, 100, 1000
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="round_up_configs")


# ────────────────────────────────────────────────────────────────────────────
class SpareChange(Base):
    """
    거래 금액(amount) 기준으로 계산된 라운드-업 잔돈을 저장.
    PK = (user_id, tx_id) 중복 방지.
    """

    __tablename__ = "spare_change"

    user_id    = Column(Integer, ForeignKey("user.id"), primary_key=True)
    tx_id      = Column(String(64), ForeignKey("transaction.id"), primary_key=True)
    round_up   = Column(Numeric(14, 2), nullable=False, doc="라운드-업 금액")
    created_at = Column(
        DateTime, nullable=False,
        server_default=func.now()
    )

    user        = relationship("User", back_populates="spare_changes")
    transaction = relationship("Transaction", back_populates="spare_change")

    # 중복 방지: 동일 사용자와 거래 ID에 대해 하나의 잔돈만 저장
    __table_args__ = (
        UniqueConstraint(
            "user_id", "tx_id",
            name="uix_spare_change_user_tx"
        ),
    )