try:
    from backend.database import engine, SessionLocal, Base
    from backend.models import Patient, Note, Medication, Allergy, Lab, Consultation
except ImportError:
    from .database import engine, SessionLocal, Base
    from .models import Patient, Note, Medication, Allergy, Lab, Consultation

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()


patient = Patient(
    id="P001",
    name="Synthetic Patient 001",
    age=45
)

db.add(patient)


db.add(Note(
    patient_id="P001",
    content="Previous follow-up: Patient was taking Metformin 500mg daily and Drug B 10mg daily.",
    source="previous_note",
    created_at="2026-08-20"
))


db.add(Medication(
    patient_id="P001",
    name="Metformin",
    dose="500 mg",
    frequency="once daily",
    status="active",
    source="medication_database",
    updated_at="2026-09-10"
))

db.add(Medication(
    patient_id="P001",
    name="Drug B",
    dose="10 mg",
    frequency="once daily",
    status="discontinued",
    source="medication_database",
    updated_at="2026-09-10"
))


db.add(Allergy(
    patient_id="P001",
    allergen="Penicillin",
    reaction="Unknown",
    source="allergy_database",
    updated_at="2026-09-08"
))


db.add(Lab(
    patient_id="P001",
    test_name="HbA1c",
    value="7.1",
    unit="%",
    source="laboratory_database",
    date="2026-09-10"
))

db.add(Lab(
    patient_id="P001",
    test_name="Creatinine",
    value="1.0",
    unit="mg/dL",
    source="laboratory_database",
    date="2026-09-10"
))

db.add(Consultation(
    patient_id="P001",
    transcript=(
        "Patient reports that they are still taking Metformin 500 mg once daily.\n"
        "Patient says they stopped Drug B approximately one week ago.\n"
        "Patient reports no known drug allergies.\n"
        "Recent blood work was discussed during the consultation."
    ),
    source="consultation",
    created_at="2026-09-13"
))


db.commit()
db.close()

print("Database seeded successfully!")