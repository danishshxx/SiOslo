from app.core.database import Base, engine
from app.models import *  # noqa: F401,F403

print("Membuat tabel database dari model SQLAlchemy...")
Base.metadata.create_all(bind=engine)
print("✅ Semua tabel berhasil dibuat.")