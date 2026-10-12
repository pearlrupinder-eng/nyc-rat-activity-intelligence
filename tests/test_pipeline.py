import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pipeline import normalize, upsert, build_mart

def test_upsert_and_mart():
    with TemporaryDirectory() as d:
        p=Path(d)
        c=normalize("complaints",{"unique_key":"A1","created_date":"2026-01-12T10:00:00","descriptor":"Rat Sighting","borough":"BROOKLYN","incident_zip":"11201"})
        assert upsert("complaints",[c],p)==(1,1)
        assert upsert("complaints",[c],p)==(1,0)
        i=normalize("inspections",{"job_id":"B1","inspection_date":"2026-01-12T11:00:00","inspection_type":"Initial","result":"Rat Activity","zip_code":"11201"})
        assert upsert("inspections",[i],p)==(1,1)
        summary=build_mart(p)
        assert summary["complaints"]==1 and summary["inspections"]==1
        with (p/"daily_metrics.csv").open() as f:
            rows=list(csv.DictReader(f))
        assert sum(int(r["complaints"]) for r in rows)==1
        assert sum(int(r["rat_activity_inspections"]) for r in rows)==1
