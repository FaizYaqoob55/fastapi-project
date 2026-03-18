from icalendar import Calendar, Event
from datetime import timedelta
import uuid


# def create_calendar_event(session):
#     event_id=f'calendar_{uuid.uuid4()}'
#     event=Event()
#     event.end_time=session.end_time or (session.start_time + timedelta(hours=1))

#     print('External Calendar Event Created')
#     print('Title:',session.title)
#     print('Date:',session.date)
#     print('Meeting:',session.meeting_link)
#     print('Location:',session.location)
#     return event_id


def create_calendar_event(session):
    cal=Calendar()
    event=Event()
    event.add('dtstart',session.date)
    event.add('dtend',session.date+timedelta(hours=1))
    event.add('summary',session.title)
    cal.add_component(event)
    ics_file=f"calendar-{session.id}.ics"
    with open(ics_file, 'wb') as f:
        f.write(cal.to_ical())
    return ics_file

    # if session.start_time is None:
    #     raise ValueError("start_time is required to create a calendar event")

    # event_id = f'calendar_{uuid.uuid4()}'
    # end_time = session.end_time or (session.start_time + timedelta(hours=1))

    # print('External Calendar Event Created')
    # print('Title:', session.title)
    # print('Date:', session.date)
    # print('Start:', session.start_time)
    # print('End:', end_time)
    # print('Meeting:', session.meeting_link)
    # print('Location:', session.location)
    # return event_id