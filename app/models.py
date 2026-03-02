import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, ForeignKey, Enum,Date,Boolean,DateTime,Text
from datetime import datetime
from app.database import Base
from app.model.role import UserRole,DebtPriority,DebtStatus
from sqlalchemy.orm import relationship
from app.model.role import SessionStatus, Action_Status, ProjectStatus
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = 'userr'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    email_notification_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=sa.true(),
    )
    email_session_reminder = Column(
        Boolean,
        default=True,)
    email_action_item_due = Column(
        Boolean,
        default=True,)
    email_mention = Column(
        Boolean,
        default=True,)
    role = Column(Enum(UserRole, native_enum=False), default=UserRole.viewer, nullable=False)
    team = relationship('Team', secondary='team_member', back_populates='members')


class Team(Base):
    __tablename__ = 'team'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    lead_id = Column(Integer, ForeignKey('userr.id'), nullable=False)
    lead = relationship('User', foreign_keys=[lead_id])

    members = relationship('User', secondary='team_member', back_populates='team')



class TeamMember(Base):
    __tablename__ = 'team_member'

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey('team.id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('userr.id', ondelete='CASCADE'))

 
class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, index=True)
    name=Column(String,unique=True,index=True)
    description=Column(String)
    status = Column(Enum(ProjectStatus, native_enum=False), default=ProjectStatus.active)
    team_id=Column(Integer,ForeignKey('team.id', ondelete='CASCADE'))
    team=relationship('Team',backref='projects')
    
    


class GrowthSession(Base):
    __tablename__ = 'growth_session'

    id = Column(Integer,primary_key=True,index=True)
    title= Column(String,nullable=False)
    date=Column(Date,nullable=False)
    start_time=Column(DateTime,nullable=False)
    end_time=Column(DateTime,nullable=False)
    status=Column(Enum(SessionStatus, native_enum=False),default=SessionStatus.planned)
    calendar_event_id=Column(String,nullable=True)
    meeting_link=Column(String,nullable=True)
    location=Column(String,nullable=True)
    team_id=Column(Integer,ForeignKey('team.id', ondelete='CASCADE'))
    notes=relationship('SessionNote',back_populates='session',cascade='all,delete')
    action_items=relationship('ActionItem',back_populates='session',cascade='all,delete')


class SessionNote(Base):
    __tablename__='session_note'
    id=Column(Integer,primary_key=True,index=True)
    content=Column(String,nullable=False)
    session_id=Column(Integer,ForeignKey('growth_session.id', ondelete='CASCADE'))
    session=relationship('GrowthSession',back_populates='notes')


class ActionItem(Base):
    __tablename__='action_items'
    id=Column(Integer,primary_key=True,index=True)
    title=Column(String,nullable=False)
    completed=Column(Boolean,default=False)
    status=Column(Enum(Action_Status, native_enum=False),default=Action_Status.pending)
    session_id=Column(Integer,ForeignKey('growth_session.id', ondelete='CASCADE'))
    session=relationship('GrowthSession',back_populates='action_items')



class Notification(Base):
    __tablename__ = 'notifications'
    id =Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey('userr.id'),nullable=False)
    type =Column(String,nullable=False)
    message=Column(String,nullable=False)
    is_read = Column(Boolean,default=False)
    created_at=Column(DateTime(timezone=True),server_default=func.now())




class TechnicalDebt(Base):
    __tablename__="technical_debts"

    id=Column(Integer,primary_key=True,index=True)
    project_id=Column(Integer,ForeignKey("projects.id"),nullable=False)
    owner_id=Column(Integer,ForeignKey("userr.id"),nullable=False)
    title=Column(String(255),nullable=False)
    description=Column(Text,nullable=True)
    priority=Column(Enum(DebtPriority),default=DebtPriority.medium)
    status=Column(Enum(DebtStatus),default=DebtStatus.open)
    severity=Column(Integer,nullable=True)
    estimated_effort=Column(Integer,nullable=True)
    actual_effort=Column(Integer,nullable=True)
    due_date=Column(Date,nullable=True)
    created_at=Column(DateTime,default=datetime.utcnow)
    comments=relationship("DebtComment",backref="technical_debt",cascade="all,delete-orphan")

class DebtComment(Base):
    __tablename__="debt_comments"
    id=Column(Integer,primary_key=True,index=True)
    debt_id=Column(Integer,ForeignKey("technical_debts.id"),nullable=False)
    user_id=Column(Integer,ForeignKey("userr.id"),nullable=False)
    comment=Column(Text,nullable=False)
    created_at=Column(DateTime,default=datetime.utcnow)

class DebtStatusHistory(Base):
    __tablename__="debt_status_history"
    id=Column(Integer,primary_key=True,index=True)
    technical_debt_id=Column(Integer,ForeignKey("technical_debts.id"),nullable=False)
    old_status=Column(String)
    new_status=Column(String)
    changed_by=Column(Integer,ForeignKey("userr.id"),nullable=False)
    changed_at=Column(DateTime,default=datetime.utcnow)


