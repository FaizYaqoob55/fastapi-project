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
    


    
