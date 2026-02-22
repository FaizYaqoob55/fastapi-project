from app.database import engine
from sqlalchemy import inspect
insp = inspect(engine)
cols = insp.get_columns('action_items')
for c in cols:
    print(f"{c['name']} - {c['type']}")
