from datetime import datetime, date


def generate_ics_file(session):
        try:
                from ics import Calendar, Event
        except ModuleNotFoundError:
                raise RuntimeError("Missing dependency 'ics'. Install with: pip install ics")

        cal = Calendar()
        event = Event()
        event.name = session.title
        # Use start_time and end_time if available
        if hasattr(session, 'start_time') and session.start_time:
                # Combine session.date with session.start_time to ensure correct day and time
                event.begin = datetime.combine(session.date, session.start_time.time())
        elif isinstance(session.date, datetime):
                event.begin = session.date
        elif isinstance(session.date, date):
                event.begin = datetime.combine(session.date, datetime.min.time())
        else:
                event.begin = session.date

        if hasattr(session, 'end_time') and session.end_time:
                event.end = datetime.combine(session.date, session.end_time.time())

        event.description = "Growth session"
        if getattr(session, 'meeting_link', None):
                event.url = session.meeting_link
        if getattr(session, 'location', None):
                event.location = session.location

        cal.events.add(event)
        return cal.serialize()