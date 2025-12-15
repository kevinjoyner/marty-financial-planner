from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/owners",
    tags=["owners"],
)

@router.post("/", response_model=schemas.Owner)
def create_owner(owner: schemas.OwnerCreate, db: Session = Depends(get_db)):
    crud.create_scenario_snapshot(db, owner.scenario_id, f"Create Owner: {owner.name}")
    db_owner = crud.create_owner(db=db, owner=owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner

@router.get("/", response_model=list[schemas.Owner])
def read_owners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    owners = crud.get_owners(db, skip=skip, limit=limit)
    return owners

@router.get("/{owner_id}", response_model=schemas.Owner)
def read_owner(owner_id: int, db: Session = Depends(get_db)):
    db_owner = crud.get_owner(db, owner_id=owner_id)
    if db_owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")
    return db_owner

@router.put("/{owner_id}", response_model=schemas.Owner)
def update_owner(
    owner_id: int, owner: schemas.OwnerUpdate, db: Session = Depends(get_db)
):
    db_owner = crud.get_owner(db, owner_id=owner_id)
    if db_owner:
        crud.create_scenario_snapshot(db, db_owner.scenario_id, f"Update Owner: {db_owner.name}")

    db_owner = crud.update_owner(db, owner_id=owner_id, owner=owner)
    if db_owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")
    db.commit()
    db.refresh(db_owner)
    return db_owner

@router.delete("/{owner_id}")
def delete_owner(owner_id: int, db: Session = Depends(get_db)):
    db_owner = crud.get_owner(db, owner_id=owner_id)
    if db_owner:
        crud.create_scenario_snapshot(db, db_owner.scenario_id, f"Delete Owner: {db_owner.name}")
    
    if db_owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")
    db.delete(db_owner)
    db.commit()
    return {"ok": True, "detail": "Owner deleted"}
