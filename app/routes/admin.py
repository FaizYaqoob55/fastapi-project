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

# @router.get('/me')
# def my_profile(current_user = Depends(get_current_user)):
#     return {
#         'id': current_user.id,
#         'email': current_user.email,
#         'name': current_user.name,
#         'role': current_user.role
#     }
