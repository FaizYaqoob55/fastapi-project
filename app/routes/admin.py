from fastapi import APIRouter,Depends
from app.schemas.dependencies import get_current_user, requires_role
from app.model.role import UserRole

router=APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.get("/dashboard")
def admin_dashboard(
    current_user=Depends(requires_role(UserRole.admin))
):
    
    return{
        'message':'Welcome Admin',
        'email':current_user.email,
        'role':current_user.role
     }

