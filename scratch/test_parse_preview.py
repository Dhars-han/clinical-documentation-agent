import openpyxl
import re

wb = openpyxl.load_workbook(r'data/clinical_docs/sheet data/synthetic_clinical_patients_P027_P056.xlsx')
ws = wb['Patient Data']

MONTHS = 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec'

def parse_med_clause(clause):
    c = clause.strip()
    status = 'active'
    if 'discontinued' in c.lower():
        status = 'discontinued'
    elif 'completed' in c.lower():
        status = 'historical'

    date_match = re.search(rf'(\d{{1,2}})\s+({MONTHS})', c, re.IGNORECASE)
    updated_at = '2026-09-10'
    if date_match:
        day = int(date_match.group(1))
        updated_at = f'2026-09-{day:02d}'

    dose_match = re.search(r'(\d+(?:\.\d+)?\s*(?:mg|mcg|g|units|unit|mEq))', c, re.IGNORECASE)
    dose = dose_match.group(1) if dose_match else None

    freq_match = re.search(r'\b(once daily|twice daily|three times daily|nightly|daily|weekly|as needed|prn)\b', c, re.IGNORECASE)
    freq = freq_match.group(1) if freq_match else None

    if dose_match:
        name = c[:dose_match.start()].strip()
    else:
        temp = re.sub(rf'\b(active|discontinued|since|\d{{1,2}}\s+({MONTHS})|refill updated)\b', '', c, flags=re.IGNORECASE)
        if freq_match:
            temp = re.sub(rf'\b{re.escape(freq)}\b', '', temp, flags=re.IGNORECASE)
        name = temp.strip()

    name = name.strip(' ,;')
    return {
        'name': name,
        'dose': dose or '',
        'frequency': freq or '',
        'status': status,
        'updated_at': updated_at
    }

def parse_lab_clause(clause):
    # E.g. 'Creatinine 1.2 mg/dL', 'Potassium 4.4 mmol/L', 'HbA1c 7.6%', 'ALT 28 U/L', 'LDL 102 mg/dL', 'No new labs'
    c = clause.strip()
    if not c or c.lower() in ['no new labs', 'no labs', 'none']:
        return None
    # match test name, value, unit
    # e.g. HbA1c 7.6% -> test=HbA1c, value=7.6, unit=%
    # Creatinine 1.2 mg/dL -> test=Creatinine, value=1.2, unit=mg/dL
    # TSH 3.1 mIU/L -> test=TSH, value=3.1, unit=mIU/L
    m = re.search(r'^([A-Za-z0-9\s\(\)\-\/]+?)\s+([0-9]+(?:\.[0-9]+)?)\s*(%|[A-Za-z0-9\/\^]+)?$', c)
    if m:
        test = m.group(1).strip()
        val = m.group(2).strip()
        unit = (m.group(3) or '').strip()
        return {'test_name': test, 'value': val, 'unit': unit, 'date': '2026-09-10'}
    return {'test_name': c, 'value': '', 'unit': '', 'date': '2026-09-10'}

print('--- Parsing Preview for all 50 patients ---')
total_meds = 0
total_allg = 0
total_labs = 0

for r in range(2, ws.max_row + 1):
    pid = ws.cell(row=r, column=1).value
    if not pid: continue

    # Meds
    med_val = ws.cell(row=r, column=5).value or ''
    for part in med_val.split(';'):
        part = part.strip()
        if not part or part.lower() == 'no active replacement documented': continue
        p = parse_med_clause(part)
        total_meds += 1

    # Allergies
    allg_val = ws.cell(row=r, column=6).value or ''
    if allg_val and allg_val.strip().lower() != 'no known medication allergies':
        # E.g. 'Ibuprofen — hives', 'Penicillin — rash'
        clean_allg = allg_val.replace('\u2014', '-').replace('—', '-')
        parts = clean_allg.split('-')
        allergen = parts[0].strip()
        reaction = parts[1].strip() if len(parts) > 1 else 'Unknown'
        total_allg += 1
    elif allg_val:
        # No known medication allergies
        total_allg += 1

    # Labs
    lab_val = ws.cell(row=r, column=7).value or ''
    for part in lab_val.split(';'):
        part = part.strip()
        l = parse_lab_clause(part)
        if l:
            total_labs += 1

print(f'Total Patients: 50 (P007 to P056)')
print(f'Total Medications to import: {total_meds}')
print(f'Total Allergy records to import: {total_allg}')
print(f'Total Lab records to import: {total_labs}')
