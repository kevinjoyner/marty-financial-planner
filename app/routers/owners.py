from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, database

router = APIRouter(prefix="/api/owners", tags=["owners"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.Owner])
def read_owners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_owners(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.Owner)
def create_owner(owner: schemas.OwnerCreate, db: Session = Depends(get_db)):
    return crud.create_owner(db=db, owner=owner)

@router.get("/{owner_id}", response_model=schemas.Owner)
def read_owner(owner_id: int, db: Session = Depends(get_db)):
    db_owner = crud.get_owner(db, owner_id=owner_id)
    if db_owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")
    return db_owner

@router.delete("/{owner_id}")
def delete_owner(owner_id: int, db: Session = Depends(get_db)):
    db_owner = crud.delete_owner(db, owner_id=owner_id)
    if db_owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")
    return {"status": "success"}
