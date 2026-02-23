from datetime import datetime, date


def generate_ics_file(session):
        try:
                from ics import Calendar, Event
        except ModuleNotFoundError:
                raise RuntimeError("Missing dependency 'ics'. Install with: pip install ics")

        cal = Calendar()
        event = Event()
        event.name = session.title
        # normalize date to datetime for the ics Event
        if isinstance(session.date, datetime):
                event.begin = session.date
        elif isinstance(session.date, date):
                event.begin = datetime.combine(session.date, datetime.min.time())
        else:
                event.begin = session.date

        event.description = "Growth session"
        if getattr(session, 'meeting_link', None):
                event.url = session.meeting_link
        if getattr(session, 'location', None):
                event.location = session.location

        cal.events.add(event)
        return cal.serialize()