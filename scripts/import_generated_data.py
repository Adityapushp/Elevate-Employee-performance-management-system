#!/usr/bin/env python3
"""Import generated CSV tables into PostgreSQL. Ground truth is intentionally excluded."""
import argparse, csv, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'generator'))
import schema as S

def convert(value, field):
    if value == '': return None
    if field['type'] == 'bool': return value.lower() in ('1','true','t','yes')
    if field['type'] == 'int': return int(value)
    if field['type'] == 'float': return float(value)
    return value

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True,help='Folder containing generator CSV files')
    parser.add_argument('--dsn',default='postgresql://epms:epms_dev_password@localhost:5432/epms')
    parser.add_argument('--replace',action='store_true',help='Truncate existing domain tables before import')
    args=parser.parse_args()
    try:
        import psycopg
    except ImportError:
        raise SystemExit('Install importer dependency: pip install "psycopg[binary]>=3.2,<4"')
    folder=Path(args.input)
    if not folder.is_dir(): raise SystemExit(f'CSV folder not found: {folder}')
    with psycopg.connect(args.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute('SET CONSTRAINTS ALL DEFERRED')
            if args.replace:
                names=[f'"{t}"' for t in reversed(S.TABLES) if t!='ground_truth']
                cur.execute('TRUNCATE '+', '.join(names)+' RESTART IDENTITY CASCADE')
            for table in S.TABLES:
                if table=='ground_truth': continue
                path=folder/f'{table}.csv'
                if not path.exists(): raise SystemExit(f'Missing required CSV: {path}')
                fields=S.RAW[table]
                columns=[f['name'] for f in fields]
                count=0
                with path.open(newline='',encoding='utf-8') as f:
                    reader=csv.DictReader(f)
                    if reader.fieldnames != columns: raise SystemExit(f'Unexpected columns in {path.name}')
                    with cur.copy(f'COPY "{table}" ({", ".join(chr(34)+c+chr(34) for c in columns)}) FROM STDIN') as copy:
                        for row in reader:
                            copy.write_row([convert(row[col], fields[i]) for i,col in enumerate(columns)])
                            count+=1
                print(f'{table}: {count:,} rows')
            cur.execute('SET CONSTRAINTS ALL IMMEDIATE')
            # Rebind local demo identities to suitable synthetic employees after replacing the dataset.
            cur.execute("UPDATE app_users SET employee_id=(SELECT employee_id FROM employees WHERE system_role='sysadmin' ORDER BY employee_id LIMIT 1) WHERE email='hr.admin@example.test'")
            cur.execute("UPDATE app_users SET employee_id=(SELECT employee_id FROM employees WHERE system_role='manager' ORDER BY employee_id LIMIT 1) WHERE email='manager@example.test'")
            cur.execute("UPDATE app_users SET employee_id=(SELECT employee_id FROM employees WHERE system_role='employee' ORDER BY employee_id LIMIT 1) WHERE email='employee@example.test'")
            cur.execute("UPDATE app_users SET employee_id=(SELECT employee_id FROM employees WHERE system_role='employee' AND employee_id<>(SELECT employee_id FROM app_users WHERE email='employee@example.test') ORDER BY employee_id LIMIT 1) WHERE email='peer@example.test'")
        conn.commit()
    print('Import complete. ground_truth.csv was not loaded into application tables.')
if __name__=='__main__': main()
