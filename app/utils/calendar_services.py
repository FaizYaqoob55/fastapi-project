import uuid


def create_calendar_event(session):
    event_id=f'calendar_{uuid.uuid4()}'
    print('External Calendar Event Created')
    print('Title:',session.title)
    print('Date:',session.date)
    print('Meeting:',session.meeting_link)
    print('Location:',session.location)
    return event_id