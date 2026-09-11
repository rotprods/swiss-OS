import importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('q',str(Path(__file__).parents[1]/'scripts/semantic_qdrant_v3.py')); M=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
class QdrantV3Tests(unittest.TestCase):
  def test_collection_is_generation_scoped(self):
    self.assertEqual(M.collection_for('a'*40),'swiss_os_repo_semantic_aaaaaaaa')
    with self.assertRaises(ValueError): M.collection_for('notsha')
  def test_alias_switch_is_single_transaction(self):
    calls=[]
    def fake(method,path,data=None): calls.append((method,path,data)); return {'result':{}}
    targets=iter(['old','new'])
    with patch.object(M,'qdrant',side_effect=fake), patch.object(M,'get_alias_target',side_effect=lambda alias=M.ALIAS: next(targets)):
      M.switch_alias('new')
    self.assertEqual(calls[0][0:2],('POST','/collections/aliases')); self.assertEqual(len(calls[0][2]['actions']),2)
  def test_scope_mismatch_fails_before_activation(self):
    with tempfile.TemporaryDirectory() as td:
      import gzip
      p=Path(td); row={'id':'00000000-0000-0000-0000-000000000001','model_digest':M.MODEL_DIGEST,'vector':{'semantic':[1.0]+[0.0]*1023,'cos20':[1.0]+[0.0]*19},'payload':{'repo':'other/repo','project':M.PROJECT,'git_sha':'a'*40}}
      with gzip.open(p/'v.gz','wt') as f: f.write(json.dumps(row)+'\n')
      (p/'r.json').write_text(json.dumps({'status':'COMPLETE','authority':'NON_AUTHORITATIVE','model_digest':M.MODEL_DIGEST,'source_commit':'a'*40,'count':1,'expected':1}))
      with patch.object(M,'get_alias_target',return_value='old'), patch.object(M,'ensure_collection'), patch.object(M,'qdrant'):
        with self.assertRaisesRegex(ValueError,'POINT_SCOPE'): M.import_generation(p/'v.gz',p/'r.json',replace=False,batch=1,activate=False,prefix='test')
if __name__=='__main__': unittest.main()
