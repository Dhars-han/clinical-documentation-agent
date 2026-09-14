"""Comprehensive seeder for synthetic patient datasets (P001 and P007–P056).

Parses the canonical Excel spreadsheet:
    data/clinical_docs/sheet data/synthetic_clinical_patients_P027_P056.xlsx
into structured clinical entities and exports to:
    data/synthetic_patients.json
for sub-second serverless cold-start database population, and seeds the configured database.
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.database import engine, SessionLocal, Base
from backend.models import Patient, Note, Medication, Allergy, Lab, Consultation

EXCEL_REL_PATH = os.path.join("data", "clinical_docs", "sheet data", "synthetic_clinical_patients_P027_P056.xlsx")
EXCEL_PATH = os.path.join(PROJECT_ROOT, EXCEL_REL_PATH)
JSON_PATH = os.path.join(PROJECT_ROOT, "data", "synthetic_patients.json")

MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"


def parse_med_clause(clause: str) -> Optional[Dict[str, str]]:
    c = clause.strip()
    if not c or c.lower() == "no active replacement documented":
        return None

    status = "active"
    if "discontinued" in c.lower():
        status = "discontinued"
    elif "completed" in c.lower():
        status = "historical"

    date_match = re.search(rf"(\d{{1,2}})\s+({MONTHS})", c, re.IGNORECASE)
    updated_at = "2026-09-10"
    if date_match:
        day = int(date_match.group(1))
        updated_at = f"2026-09-{day:02d}"

    dose_match = re.search(r"(\d+(?:\.\d+)?\s*(?:mg|mcg|g|units|unit|mEq))", c, re.IGNORECASE)
    dose = dose_match.group(1) if dose_match else ""

    freq_match = re.search(r"\b(once daily|twice daily|three times daily|nightly|daily|weekly|as needed|prn)\b", c, re.IGNORECASE)
    freq = freq_match.group(1) if freq_match else ""

    if dose_match:
        name = c[:dose_match.start()].strip()
    else:
        temp = re.sub(rf"\b(active|discontinued|since|\d{{1,2}}\s+({MONTHS})|refill updated)\b", "", c, flags=re.IGNORECASE)
        if freq_match:
            temp = re.sub(rf"\b{re.escape(freq)}\b", "", temp, flags=re.IGNORECASE)
        name = temp.strip()

    name = name.strip(" ,;")
    return {
        "name": name,
        "dose": dose,
        "frequency": freq,
        "status": status,
        "source": "medication_database",
        "updated_at": updated_at
    }


def parse_lab_clause(clause: str) -> Optional[Dict[str, str]]:
    c = clause.strip()
    if not c or c.lower() in ["no new labs", "no labs", "none"]:
        return None

    # E.g. "Creatinine 1.2 mg/dL", "Potassium 4.4 mmol/L", "HbA1c 7.6%", "TSH 2.8 mIU/L"
    m = re.search(r"^([A-Za-z0-9\s\(\)\-\/]+?)\s+([0-9]+(?:\.[0-9]+)?)\s*(%|[A-Za-z0-9\/\^]+)?$", c)
    if m:
        test = m.group(1).strip()
        val = m.group(2).strip()
        unit = (m.group(3) or "").strip()
        return {
            "test_name": test,
            "value": val,
            "unit": unit,
            "source": "laboratory_database",
            "date": "2026-09-10"
        }
    return {
        "test_name": c,
        "value": "",
        "unit": "",
        "source": "laboratory_database",
        "date": "2026-09-10"
    }


def parse_allergy_clause(allg_val: str) -> List[Dict[str, str]]:
    results = []
    if not allg_val or not allg_val.strip():
        return results

    val = allg_val.strip()
    if val.lower() == "no known medication allergies":
        results.append({
            "allergen": "No known medication allergies",
            "reaction": "None documented",
            "source": "allergy_database",
            "updated_at": "2026-09-08"
        })
    else:
        # e.g. "Ibuprofen — hives", "Penicillin — rash"
        clean = val.replace("\u2014", "-").replace("—", "-")
        for item in clean.split(";"):
            item = item.strip()
            if not item:
                continue
            parts = item.split("-")
            allergen = parts[0].strip()
            reaction = parts[1].strip() if len(parts) > 1 else "Unknown"
            results.append({
                "allergen": allergen,
                "reaction": reaction,
                "source": "allergy_database",
                "updated_at": "2026-09-08"
            })
    return results


def get_base_p001_data() -> Dict[str, Any]:
    """Preserves baseline P001 from backend/seed.py for backwards compatibility."""
    return {
        "id": "P001",
        "name": "Synthetic Patient 001",
        "age": 45,
        "notes": [
            {
                "content": "Previous follow-up: Patient was taking Metformin 500mg daily and Drug B 10mg daily.",
                "source": "previous_note",
                "created_at": "2026-08-20"
            }
        ],
        "medications": [
            {
                "name": "Metformin",
                "dose": "500 mg",
                "frequency": "once daily",
                "status": "active",
                "source": "medication_database",
                "updated_at": "2026-09-10"
            },
            {
                "name": "Drug B",
                "dose": "10 mg",
                "frequency": "once daily",
                "status": "discontinued",
                "source": "medication_database",
                "updated_at": "2026-09-10"
            }
        ],
        "allergies": [
            {
                "allergen": "Penicillin",
                "reaction": "Unknown",
                "source": "allergy_database",
                "updated_at": "2026-09-08"
            }
        ],
        "labs": [
            {
                "test_name": "HbA1c",
                "value": "7.1",
                "unit": "%",
                "source": "laboratory_database",
                "date": "2026-09-10"
            },
            {
                "test_name": "Creatinine",
                "value": "1.0",
                "unit": "mg/dL",
                "source": "laboratory_database",
                "date": "2026-09-10"
            }
        ],
        "consultations": [
            {
                "transcript": (
                    "Patient reports that they are still taking Metformin 500 mg once daily.\n"
                    "Patient says they stopped Drug B approximately one week ago.\n"
                    "Patient reports no known drug allergies.\n"
                    "Recent blood work was discussed during the consultation."
                ),
                "source": "consultation",
                "created_at": "2026-09-13"
            }
        ]
    }


def parse_all_synthetic_patients() -> List[Dict[str, Any]]:
    """Parses all 50 patients from the Excel sheet into structured dictionary records."""
    patients: List[Dict[str, Any]] = [get_base_p001_data()]

    if not os.path.exists(EXCEL_PATH):
        print(f"Warning: Excel file not found at {EXCEL_PATH}")
        return patients

    import openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb["Patient Data"]

    for r in range(2, ws.max_row + 1):
        pid = ws.cell(row=r, column=1).value
        if not pid:
            continue
        pid = str(pid).strip()

        age_val = ws.cell(row=r, column=2).value
        try:
            age = int(age_val) if age_val is not None else 50
        except Exception:
            age = 50

        patient_record: Dict[str, Any] = {
            "id": pid,
            "name": f"Patient {pid}",
            "age": age,
            "notes": [],
            "medications": [],
            "allergies": [],
            "labs": [],
            "consultations": []
        }

        # Col 4: Previous Note
        prev_note = ws.cell(row=r, column=4).value
        if prev_note and str(prev_note).strip():
            patient_record["notes"].append({
                "content": str(prev_note).strip(),
                "source": "previous_note",
                "created_at": "2026-08-20"
            })

        # Col 5: Medication Database
        med_val = ws.cell(row=r, column=5).value or ""
        for part in str(med_val).split(";"):
            m = parse_med_clause(part)
            if m:
                patient_record["medications"].append(m)

        # Col 6: Allergy Database
        allg_val = ws.cell(row=r, column=6).value or ""
        patient_record["allergies"].extend(parse_allergy_clause(str(allg_val)))

        # Col 7: Laboratory Results
        lab_val = ws.cell(row=r, column=7).value or ""
        for part in str(lab_val).split(";"):
            l = parse_lab_clause(part)
            if l:
                patient_record["labs"].append(l)

        # Col 8: Consultation Transcript
        transcript = ws.cell(row=r, column=8).value
        if transcript and str(transcript).strip():
            patient_record["consultations"].append({
                "transcript": str(transcript).strip(),
                "source": "consultation",
                "created_at": "2026-09-14"
            })

        patients.append(patient_record)

    return patients


def export_json_dataset(patients: List[Dict[str, Any]], target_path: str = JSON_PATH):
    """Saves parsed dataset to JSON for fast serverless cold-start seeding."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(patients, f, indent=2)
    print(f"Exported {len(patients)} synthetic patients to {target_path}")


def seed_database_from_records(patients: List[Dict[str, Any]], drop_first: bool = False):
    """Populates the configured database (Postgres or SQLite) from patient records."""
    if drop_first:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_ids = {p.id for p in db.query(Patient.id).all()}
        added_count = 0

        for pt in patients:
            pid = pt["id"]
            if pid in existing_ids:
                continue

            patient = Patient(id=pid, name=pt["name"], age=pt["age"])
            db.add(patient)

            for n in pt.get("notes", []):
                db.add(Note(patient_id=pid, content=n["content"], source=n["source"], created_at=n["created_at"]))

            for m in pt.get("medications", []):
                db.add(Medication(
                    patient_id=pid,
                    name=m["name"],
                    dose=m["dose"],
                    frequency=m["frequency"],
                    status=m["status"],
                    source=m["source"],
                    updated_at=m["updated_at"]
                ))

            for a in pt.get("allergies", []):
                db.add(Allergy(
                    patient_id=pid,
                    allergen=a["allergen"],
                    reaction=a["reaction"],
                    source=a["source"],
                    updated_at=a["updated_at"]
                ))

            for l in pt.get("labs", []):
                db.add(Lab(
                    patient_id=pid,
                    test_name=l["test_name"],
                    value=l["value"],
                    unit=l["unit"],
                    source=l["source"],
                    date=l["date"]
                ))

            for c in pt.get("consultations", []):
                db.add(Consultation(
                    patient_id=pid,
                    transcript=c["transcript"],
                    source=c["source"],
                    created_at=c["created_at"]
                ))

            added_count += 1

        db.commit()
        total_patients = db.query(Patient).count()
        print(f"Database seeded: {added_count} patients added (Total in DB: {total_patients})")
    finally:
        db.close()


def auto_seed_if_needed():
    """Idempotent auto-seed hook called at backend startup."""
    try:
        db = SessionLocal()
        count = db.query(Patient).count()
        db.close()
        if count >= 50:
            return count
    except Exception:
        pass

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # Prefer loading from fast JSON cache if it exists
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                patients = json.load(f)
            seed_database_from_records(patients, drop_first=False)
            return len(patients)
        except Exception as e:
            print(f"Warning: Failed to load synthetic_patients.json: {e}")

    # Fallback to parsing Excel if JSON not found
    if os.path.exists(EXCEL_PATH):
        try:
            patients = parse_all_synthetic_patients()
            seed_database_from_records(patients, drop_first=False)
            return len(patients)
        except Exception as e:
            print(f"Warning: Failed to parse Excel: {e}")

    return 0


if __name__ == "__main__":
    print("Parsing Excel dataset and generating synthetic patient records...")
    patients_data = parse_all_synthetic_patients()
    export_json_dataset(patients_data)
    print("Seeding configured database...")
    seed_database_from_records(patients_data, drop_first=True)
    print(f"Successfully seeded {len(patients_data)} patients (P001, P007–P056)!")
