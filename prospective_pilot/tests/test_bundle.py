import unittest,sys,json,tempfile,subprocess,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'code'))
from common import *
class BundleTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.refs,cls.variants,cls.judges=load_verified_bundle(P)
 def test_source_counts(self):self.assertEqual((len(self.refs),len(self.variants)),(5,20))
 def test_primary_acceptance(self):
  self.assertEqual({j:sum(x['parsed'] is not None for x in r.values()) for j,r in self.judges.items()},{'mistral':14,'phi':20})
 def test_all_phi_outputs_fenced(self):self.assertTrue(all(x['response']['raw_text'].lstrip().startswith('```') for x in self.judges['phi'].values()))
 def test_no_homework_only_closure_changes(self):
  for v in self.variants.values():
   if v['condition']=='no_homework':
    orig=self.refs[v['base_case_id']]['messages'];self.assertEqual(orig[:7],v['messages'][:7]);self.assertNotEqual(orig[7]['text'],v['messages'][7]['text'])
 def test_supportive_only_turns_2_3(self):
  for v in self.variants.values():
   if v['condition']=='supportive_non_cbt':
    orig=self.refs[v['base_case_id']]['messages'];self.assertEqual([i for i,(a,b) in enumerate(zip(orig,v['messages'])) if a['text']!=b['text']],[3,5])
 def test_primary_scores_and_outputs_unchanged_during_recompute(self):
  from reproduce_pilot import run
  files=list((P/'automated_judging').rglob('*.json'))+list((P/'analysis').glob('*'))
  old={f:sha(f.read_bytes()) for f in files if f.is_file()}
  with tempfile.TemporaryDirectory() as t:
   result=run(P,Path(t)/'outputs');self.assertEqual(result['primary_valid'],{'mistral':14,'phi':20})
   self.assertAlmostEqual(result['overall_agreement']['pearson'],0.053163920378,places=10)
  self.assertTrue(all(sha(f.read_bytes())==s for f,s in old.items()))
 def test_dry_run_does_not_import_torch(self):
  r=subprocess.run([sys.executable,str(P/'code/replay_models.py'),'--role','phi','--dry-run'],capture_output=True,text=True,check=True)
  self.assertEqual(json.loads(r.stdout)['new_model_calls'],0)
 def test_refuse_replace(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'x.json';write_once(f,{'a':1});write_once(f,{'a':1})
   with self.assertRaises(ValueError):write_once(f,{'a':2})
if __name__=='__main__':unittest.main()
