from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    lead = "lead"
    developer = "developer"
    viewer = "viewer"

class ProjectStatus(str,Enum):
    active='active'
    inactive='inactive'
    completed='completed'
    
class SessionStatus(str,Enum):
    planned='planned'
    completed='completed'
    cancelled='cancelled'

class Action_Status(str,Enum):
    in_progress='in_progress'
    pending ='pending'
    completed='completed'
    

class NotificationType(str,Enum):
    session_reminder = 'session-reminder'
    action_item_due = 'action_item-due'
    mention = 'mention'


class DebtPriority(str,Enum):
    low="low"
    medium="medium"
    high="high"

class DebtStatus(str,Enum):
    open="open"
    in_progress="in_progress"
    resolved="resolved"

