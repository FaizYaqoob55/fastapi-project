from sqlalchemy import Column, Integer, String, ForeignKey, Enum,Date,Boolean
from app.database import Base
from app.model.role import UserRole
from sqlalchemy.orm import relationship
from app.model.role import SessionStatus, Action_Status, ProjectStatus


class User(Base):
    __tablename__ = 'userr'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
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
    status=Column(Enum(SessionStatus, native_enum=False),default=SessionStatus.planned)
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



