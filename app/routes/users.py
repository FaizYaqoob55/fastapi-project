from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.schemas.dependencies import UserPrefrencesUpdate
from app.schemas.dependencies import get_current_user
from app.models import User
from app.database import get_db


router=APIRouter(prefix="/user",
                 tags=["users"])

@router.put("/prefrences")
def update_prefrences(
    data:UserPrefrencesUpdate,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    for key ,value in data.dict(exclude_unset=True).items():
        setattr(current_user,key,value)
    db.commit()
    return {"message":"Prefrences updated"}

