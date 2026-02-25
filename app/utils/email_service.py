from pathlib import Path
from datetime import datetime

LOG_FILE = Path('log/email.log')


def send_email_simulation(to_email:str,subject:str,body:str):
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE,'a',encoding='utf-8') as f:
        f.write(f"\n--- EMAIL ---\n")
        f.write(f"TIME:{datetime.utcnow()}\n")
        f.write(f"TO:{to_email}\n")
        f.write(f"subject:{subject}\n")
        f.write(f"body:\n")
        f.write(body+"\n")



