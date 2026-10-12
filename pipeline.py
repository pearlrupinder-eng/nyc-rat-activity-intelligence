"""NYC rat complaints and rodent inspection data collection (Socrata)."""
import argparse
import csv
import json
import os
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://data.cityofnewyork.us/resource"
IDS = {"complaints": "erm2-nwe9", "inspections": "p937-wjvj"}
DATES = {"complaints": "created_date", "inspections": "inspection_date"}
FIELDS = {
    "complaints": ["unique_key","created_date","closed_date","complaint_type","descriptor","borough","incident_zip","latitude","longitude","status"],
    "inspections": ["job_id","inspection_date","inspection_type","result","bbl","zip_code","latitude","longitude","approved_date"],
}
OUTPUTS = {"complaints": "complaints.csv", "inspections": "inspections.csv"}

def fetch(dataset, start, end, page_size=1000, retries=4):
    field = DATES[dataset]
    where = f"{field} >= '{start}T00:00:00' AND {field} < '{end}T00:00:00'"
    if dataset == "complaints":
        where += " AND descriptor = 'Rat Sighting'"
    offset = 0
    while True:
        params = {"$where":where, "$limit":page_size,"$offset":offset,"$order":f"{field} ASC"}
        url = f"{BASE}/{IDS[dataset]}.json?" + urlencode(params)
        for attempt in range(retries):
            try:
                headers = {"User-Agent":"NYC-Rat-Intelligence/1.0"}
                if os.getenv("SOCRATA_APP_TOKEN"):
                    headers["X-App-Token"] = os.environ["SOCRATA_APP_TOKEN"]
                with urlopen(Request(url,headers=headers),timeout=45) as response:
                    rows=json.load(response)
                if not isinstance(rows,list):
                    raise ValueError("Unexpected response from Socrata")
                break
            except Exception:
                if attempt == retries-1:
                    raise
                time.sleep(2 ** attempt)
        yield from rows
        offset+=len(rows)
        if len(rows)<page_size:
            break

def normalize(dataset,item):
    row={field:str(item.get(field,"") or "") for field in FIELDS[dataset]}
    if dataset=="inspections":
        row["latitude"]=str(item.get("latitude",item.get("lat","")) or "")
        row["longitude"]=str(item.get("longitude",item.get("lon","")) or "")
    return row

def identity(dataset,row):
    if dataset=="complaints":
        return (row["unique_key"],)
    return tuple(row.get(c,"") for c in ("job_id","inspection_date","inspection_type","bbl","result"))

def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def upsert(dataset,fresh,directory):
    path=directory/OUTPUTS[dataset]
    existing=read_csv(path)
    merged={identity(dataset,row):row for row in existing}
    for row in fresh:
        key=identity(dataset,row)
        if key[0]:
            merged[key]=row
    rows=sorted(merged.values(),key=lambda r:(r.get(DATES[dataset],""),identity(dataset,r)))
    write_csv(path,rows,FIELDS[dataset])
    return len(rows),len(rows)-len(existing)

def parse_date(value):
    try:
        return datetime.fromisoformat(value[:10]).date()
    except (ValueError,TypeError):
        return None

def build_mart(directory):
    complaints=read_csv(directory/"complaints.csv")
    inspections=read_csv(directory/"inspections.csv")
    daily={}
    def bucket(date,borough,zip_code):
        key=(date,borough or "UNKNOWN",zip_code or "UNKNOWN")
        if key not in daily:
            daily[key]={"date":date,"borough":key[1],"zip_code":key[2],"complaints":0,"inspections":0,"rat_activity_inspections":0,"passed_inspections":0,"other_inspections":0}
        return daily[key]
    for row in complaints:
        dt=parse_date(row.get("created_date"))
        if dt:
            bucket(str(dt),row.get("borough",""),row.get("incident_zip",""))["complaints"]+=1
    for row in inspections:
        dt=parse_date(row.get("inspection_date"))
        if not dt:
            continue
        b=bucket(str(dt),"UNKNOWN",row.get("zip_code",""))
        b["inspections"]+=1
        result=row.get("result","").lower()
        if "rat activity" in result:
            b["rat_activity_inspections"]+=1
        elif "passed" in result:
            b["passed_inspections"]+=1
        else:
            b["other_inspections"]+=1
    fields=["date","borough","zip_code","complaints","inspections","rat_activity_inspections","passed_inspections","other_inspections"]
    write_csv(directory/"daily_metrics.csv",[daily[k] for k in sorted(daily)],fields)
    weeks=Counter()
    for row in daily.values():
        d=parse_date(row["date"])
        iso=d.isocalendar()
        weeks[(f"{iso.year}-W{iso.week:02d}",row["zip_code"])]+=row["complaints"]
    write_csv(directory/"weekly_complaints_by_zip.csv",[{"iso_week":k[0],"zip_code":k[1],"complaints":v} for k,v in sorted(weeks.items())],["iso_week","zip_code","complaints"])
    return {"complaints":len(complaints),"inspections":len(inspections),"daily_grains":len(daily)}

def run(args):
    directory=Path(args.output)
    directory.mkdir(parents=True,exist_ok=True)
    end=args.end or datetime.now(timezone.utc).date().isoformat()
    start=args.start or (datetime.fromisoformat(end).date()-timedelta(days=args.lookback)).isoformat()
    if start>=end:
        raise ValueError("Start must be before end")
    log={"run_utc":datetime.now(timezone.utc).isoformat(),"window":[start,end],"status":"success","sources":{}}
    try:
        for source in IDS:
            fresh=[normalize(source,r) for r in fetch(source,start,end)]
            count,added=upsert(source,fresh,directory)
            log["sources"][source]={"downloaded":len(fresh),"total":count,"net_new":added}
        log["mart"]=build_mart(directory)
    except Exception as exc:
        log["status"]="failed"
        log["error"]=str(exc)
        raise
    finally:
        (directory/"refresh_status.json").write_text(json.dumps(log,indent=2),encoding="utf-8")
    print(json.dumps(log,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--lookback",type=int,default=21)
    p.add_argument("--output",default="data")
    run(p.parse_args())
