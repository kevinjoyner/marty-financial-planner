from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import database

router = APIRouter(prefix="/api/tax_limits", tags=["tax_limits"])
# Placeholder as specific crud functions for tax limits might not be strict requirement for now
