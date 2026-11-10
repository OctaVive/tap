import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('m09_report',Path(__file__).with_name('report.py'))
report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)


class AcceptanceGateTests(unittest.TestCase):
 def test_missing_failed_skipped_changed_and_duplicate_evidence_refuse_pass(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   (root/'source.go').write_text('fixture source')
   (root/'runtime.json').write_text(json.dumps({'fixture':'not real acceptance'}))
   sha=lambda name:hashlib.sha256((root/name).read_bytes()).hexdigest()
   ledger={'milestone':'P1-M09','cases':[dict(id=f'R{i:02}',status='PASS',evidence=['runtime.json']) for i in range(1,11)]}
   catalog={'schema':2,'milestone':'P1-M09','cases':[dict(id=case['id']+'.fixture',gate=case['id'],required=True) for case in ledger['cases']]}
   (root/'catalog.json').write_text(json.dumps(catalog))
   results={'milestone':'P1-M09','scope':'real-runtime-acceptance','catalog_sha256':sha('catalog.json'),'cases':[dict(id=case['id'],gate=case['gate'],status='PASS',evidence=['runtime.json']) for case in catalog['cases']]}
   (root/'results.json').write_text(json.dumps(results))
   manifest={'source':{'source.go':sha('source.go')},'evidence':{name:sha(name) for name in ['runtime.json','catalog.json','results.json']},'isolated_runtime_acceptance':True}
   def evaluate(gates=ledger,definitions=catalog,executions=results):
    return report.evaluate(root,gates,manifest,definitions,'catalog.json',executions,'results.json')['status']
   # Synthetic fixtures test reporter logic only, never runtime acceptance.
   self.assertEqual(evaluate(),'PASS')
   for status in ['FAIL','SKIP','NOT_RUN','INCOMPLETE','DEVELOPMENT_PASS']:
    bad=copy.deepcopy(ledger);bad['cases'][0]['status']=status
    self.assertEqual(evaluate(gates=bad),'INCOMPLETE')
    bad=copy.deepcopy(results);bad['cases'][0]['status']=status
    self.assertEqual(evaluate(executions=bad),'INCOMPLETE')
   for mutate in [lambda value:value['cases'].pop(),lambda value:value['cases'].append(value['cases'][0]),lambda value:value.update(catalog_sha256='changed'),lambda value:value.update(scope='development only'),lambda value:value['cases'][0].update(evidence=['missing.json']),lambda value:value['cases'][0].update(gate='R10')]:
    bad=copy.deepcopy(results);mutate(bad)
    self.assertEqual(evaluate(executions=bad),'INCOMPLETE')
   bad=copy.deepcopy(catalog);bad['cases'][0]['required']=False
   self.assertEqual(evaluate(definitions=bad),'INCOMPLETE')
   self.assertEqual(evaluate(executions=None),'INCOMPLETE')
   self.assertEqual(evaluate(definitions=None),'INCOMPLETE')
   (root/'source.go').write_text('changed source')
   self.assertEqual(evaluate(),'INCOMPLETE')


if __name__=='__main__':unittest.main()
