import unittest, json, sys
from pathlib import Path
CODE = Path(__file__).resolve().parents[1] / 'code'
sys.path.insert(0, str(CODE))
try:
    import common
except ImportError:
    common = None

class ParserTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(common, 'The reproducibility common module must exist')
        self.obj={'blind_id':'B001','scores':{d:4 for d in common.DIMS},'evidence':{d:'Observed in transcript' for d in common.DIMS},'overall_comment':'Research test only','confidence':3}
    def test_integer_scores(self):
        self.assertEqual(common.parse_rating(json.dumps(self.obj), 'B001')[0], self.obj)
    def test_raw_mistral_rejects_fence(self):
        with self.assertRaises(ValueError): common.parse_rating('```json\n'+json.dumps(self.obj)+'\n```','B001')
    def test_phi_fence_preserves_content(self):
        o,mode=common.parse_rating('```json\n'+json.dumps(self.obj)+'\n```','B001',allow_fence=True)
        self.assertEqual(o,self.obj); self.assertEqual(mode,'strip_outer_markdown_fence_only')
    def test_text_score_never_converted(self):
        self.obj['scores']['safety']='6'
        with self.assertRaises(ValueError): common.parse_rating(json.dumps(self.obj),'B001',allow_fence=True)
    def test_boolean_not_integer_score(self):
        self.obj['scores']['safety']=True
        with self.assertRaises(ValueError): common.parse_rating(json.dumps(self.obj),'B001')
    def test_out_of_range_rejected(self):
        self.obj['scores']['safety']=8
        with self.assertRaises(ValueError): common.parse_rating(json.dumps(self.obj),'B001')
    def test_wrong_id_rejected(self):
        with self.assertRaises(ValueError): common.parse_rating(json.dumps(self.obj),'B002')
    def test_truncated_not_repaired(self):
        with self.assertRaises(ValueError): common.parse_rating(json.dumps(self.obj)[:-20],'B001',allow_fence=True)
    def test_commentary_not_removed(self):
        with self.assertRaises(ValueError): common.parse_rating('Explanation\n```json\n'+json.dumps(self.obj)+'\n```','B001',allow_fence=True)
    def test_missing_dimension_rejected(self):
        del self.obj['scores']['safety']
        with self.assertRaises(ValueError): common.parse_rating(json.dumps(self.obj),'B001')
    def test_extract_dialogue(self):
        text='X\n\nDIALOGUE:\nPatient: أ\nTherapist: ب\n\nReturn JSON using exactly this structure:\n{}'
        self.assertEqual(common.extract_dialogue(text),'Patient: أ\nTherapist: ب')
    def test_render_uses_only_role_and_text(self):
        messages=[{'role':'patient','text':'a','call_id':'P01','condition':'reference'},{'role':'therapist','text':'b','origin':'edit'}]
        self.assertEqual(common.dialogue_text(messages),'Patient: a\nTherapist: b')

if __name__=='__main__':unittest.main()
