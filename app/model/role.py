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
    PLANNED='PLANNED'
    COMPLETED='COMPLETED'
    CANCLLED='CANCELLED'

class Action_Status(str,Enum):
    PENDING ='PENDING'
    DONE = 'DONE'

    
