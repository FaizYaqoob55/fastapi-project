from datetime import datetime, date, time

def generate_ics_file(session):
    try:
        from ics import Calendar, Event
        import pytz
    except ModuleNotFoundError:
        raise RuntimeError("Missing dependency 'ics' or 'pytz'. Please ensure they are installed.")

    # User's local timezone
    local_tz = pytz.timezone("Asia/Karachi")

    cal = Calendar()
    event = Event()
    event.name = session.title

    # Combine date and time and make it timezone-aware
    if session.date and session.start_time:
        s_time = session.start_time if isinstance(session.start_time, time) else session.start_time.time()
        start_dt = datetime.combine(session.date, s_time)
        event.begin = local_tz.localize(start_dt)
    
    if session.date and session.end_time:
        e_time = session.end_time if isinstance(session.end_time, time) else session.end_time.time()
        end_dt = datetime.combine(session.date, e_time)
        event.end = local_tz.localize(end_dt)

    event.description = f"Growth session for team"
    # Baqi metadata
    if hasattr(session, 'meeting_link') and session.meeting_link:
        event.url = session.meeting_link
        
    cal.events.add(event)
    return cal.serialize()