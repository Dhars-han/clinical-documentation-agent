# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text, ForeignKey
try:
    from backend.database import Base
except ImportError:
    from .database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True)
    name = Column(String)
    age = Column(Integer)


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    content = Column(Text)
    source = Column(String)
    created_at = Column(String)


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    name = Column(String)
    dose = Column(String)
    frequency = Column(String)
    status = Column(String)
    source = Column(String)
    updated_at = Column(String)


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    allergen = Column(String)
    reaction = Column(String)
    source = Column(String)
    updated_at = Column(String)


class Lab(Base):
    __tablename__ = "labs"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    test_name = Column(String)
    value = Column(String)
    unit = Column(String)
    source = Column(String)
    date = Column(String)


class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    transcript = Column(Text)
    source = Column(String)
    created_at = Column(String)