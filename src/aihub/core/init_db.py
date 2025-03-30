from aihub.core.database import engine
from aihub.models import user

def init_db():
    user.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db() 