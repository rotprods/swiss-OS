import importlib.util, json, tempfile, unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('d',str(Path(__file__).parents[1]/'scripts/semantic_delta_v3.py')); M=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
def sem(): return [1.0]+[0.0]*1023
def cos(): return [1.0]+[0.0]*19
class DeltaV3Tests(unittest.TestCase):
  def cur(self,i,text):
    h=M.sha(text.encode()); return {'id':i,'embedding_input':text,'payload':{'input_sha256':h,'cos20':cos(),'git_sha':'new'}}
  def old(self,r):
    p=dict(r['payload']); p['git_sha']='old'; return {'id':r['id'],'vector':{'semantic':sem(),'cos20':cos()},'payload':p,'input_sha256':r['payload']['input_sha256'],'model_digest':M.MODEL_DIGEST}
  def test_incremental_and_deterministic(self):
    with tempfile.TemporaryDirectory() as td:
      p=Path(td); a=self.cur('00000000-0000-0000-0000-000000000001','same'); b=self.cur('00000000-0000-0000-0000-000000000002','new'); c=self.cur('00000000-0000-0000-0000-000000000003','gone')
      M.write(p/'chunks.jsonl',[a,b]); M.write(p/'base.jsonl.gz',[self.old(a),self.old(c)])
      M.plan(p/'chunks.jsonl',p/'base.jsonl.gz',p/'x'); M.plan(p/'chunks.jsonl',p/'base.jsonl.gz',p/'y')
      r=json.loads((p/'x/delta-receipt.json').read_text()); self.assertEqual((r['reused'],r['todo'],r['removed']),(1,1,1)); self.assertEqual((p/'x/reuse-vectors.jsonl.gz').read_bytes(),(p/'y/reuse-vectors.jsonl.gz').read_bytes())
  def test_duplicate_baseline_fails(self):
    with tempfile.TemporaryDirectory() as td:
      p=Path(td); a=self.cur('00000000-0000-0000-0000-000000000001','same'); M.write(p/'chunks.jsonl',[a]); M.write(p/'base.jsonl.gz',[self.old(a),self.old(a)])
      with self.assertRaisesRegex(ValueError,'BASELINE_DUPLICATE'): M.plan(p/'chunks.jsonl',p/'base.jsonl.gz',p/'x')
if __name__=='__main__': unittest.main()
