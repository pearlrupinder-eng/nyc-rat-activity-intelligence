import csv
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import normalize, upsert, build_mart

class PipelineTests(unittest.TestCase):
    def test_upsert_and_mart(self):
        with TemporaryDirectory() as d:
            p=Path(d)
            c=normalize("complaints",{"unique_key":"A1","created_date":"2026-01-12T10:00:00","descriptor":"Rat Sighting","borough":"BROOKLYN","incident_zip":"11201"})
            self.assertEqual(upsert("complaints",[c],p),(1,1))
            self.assertEqual(upsert("complaints",[c],p),(1,0))
            i=normalize("inspections",{"job_id":"B1","inspection_date":"2026-01-12T11:00:00","inspection_type":"Initial","result":"Rat Activity","zip_code":"11201"})
            self.assertEqual(upsert("inspections",[i],p),(1,1))
            summary=build_mart(p)
            self.assertEqual(summary["complaints"],1)
            self.assertEqual(summary["inspections"],1)
            with (p/"daily_metrics.csv").open(newline="") as file:
                rows=list(csv.DictReader(file))
            self.assertEqual(sum(int(r["complaints"]) for r in rows),1)
            self.assertEqual(sum(int(r["rat_activity_inspections"]) for r in rows),1)

if __name__=="__main__":
    unittest.main()
