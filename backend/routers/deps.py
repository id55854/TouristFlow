"""Shared route dependencies."""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.property import Property


def get_property_or_404(property_id: int, db: Session = Depends(get_db)) -> Property:
    prop = db.get(Property, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop
