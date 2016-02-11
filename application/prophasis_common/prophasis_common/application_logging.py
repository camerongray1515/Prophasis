from .models import LogMessage, session

def log_message(category, message):
    session.add(LogMessage(category=category, message=message))
    session.commit()
