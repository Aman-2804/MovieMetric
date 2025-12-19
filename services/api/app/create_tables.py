from .db import Base, engine
from . import models  

Base.metadata.create_all(bind=engine)
print("Tables created!!")