from enum import Enum


class UserRole(str,Enum):
    admin="admin",
    lead="lead",
    developer="developer",
    viewer="viewer"

    