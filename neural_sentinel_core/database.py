# database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# --- POSTGRESQL CONNECTION STRING ---
# Format: postgresql://<username>:<password>@<host>:<port>/<database_name>
# Update 'postgres' and 'your_password' to match your local setup
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1810@localhost:5432/neural_sentinel_db"

# Notice we removed the check_same_thread argument (that is SQLite only)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 2. Define the Audit Log Table
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    file_name = Column(String, index=True)
    status = Column(String) # "safe" or "danger"
    threat_count = Column(Integer, default=0)
    highest_risk = Column(String, default="NONE")
    threat_details = Column(Text, default="[]") 

# 3. Create the tables
def init_db():
    Base.metadata.create_all(bind=engine)