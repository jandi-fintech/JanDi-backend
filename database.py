from sqlalchemy                 import create_engine, MetaData
from sqlalchemy.ext.asyncio     import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm             import sessionmaker
from starlette.config           import Config

config = Config('.env')

# 동기 설정
SQLALCHEMY_DATABASE_URL = config(
    'SQLALCHEMY_DATABASE_URL',
    default="sqlite:///./test.db"
)
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    sync_engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    sync_engine = create_engine(SQLALCHEMY_DATABASE_URL)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# 메타데이터 네이밍 컨벤션
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)

def get_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 비동기 설정
SQLALCHEMY_DATABASE_URL_ASYNC = config(
    "SQLALCHEMY_DATABASE_URL_ASYNC",
    default="sqlite+aiosqlite:///./test.db"
)
async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL_ASYNC,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
