"""Tests check consequential guardrails and metric denominators, not API quality."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from risklens import validate, split_paragraphs, baseline
from evaluate import score

TEXT = "A single supplier could stop production. This could materially adversely affect sales."


def valid_obj():
    return {"category":"Operational","needs_review":False,"review_reason":"", "severity":"High",
            "summary":["Production may be interrupted.","Sales could be affected."],"evidence":"A single supplier could stop production."}


class Controls(unittest.TestCase):
    def test_genuine_evidence_accepted(self):
        self.assertEqual(validate(valid_obj(),TEXT),[])

    def test_paraphrase_rejected(self):
        x=valid_obj(); x['evidence']='A supplier may halt production.'
        self.assertTrue(any('Evidence' in e for e in validate(x,TEXT)))

    def test_invented_number_rejected(self):
        x=valid_obj(); x['summary'][0]='Production may drop by 30%.'
        self.assertTrue(any('number' in e for e in validate(x,TEXT)))

    def test_materiality_not_invented(self):
        x=valid_obj(); x['evidence']='A single supplier could stop production.'
        self.assertTrue(any('High' in e for e in validate(x,'A single supplier could stop production. Sales could fall.')))

    def test_boolean_not_string(self):
        x=valid_obj(); x['needs_review']='false'
        self.assertTrue(any('boolean' in e for e in validate(x,TEXT)))

    def test_reason_required(self):
        x=valid_obj();x['needs_review']=True
        self.assertTrue(any('reason' in e for e in validate(x,TEXT)))

    def test_request_bounds(self):
        with self.assertRaises(ValueError):split_paragraphs('x'*6001)
        with self.assertRaises(ValueError):split_paragraphs('\n\n'.join([TEXT]*7))
        self.assertEqual(len(split_paragraphs(TEXT+'\n\n'+TEXT)),2)

    def test_keyword_tie_abstains(self):
        x=baseline('Cybersecurity incidents and supplier failures are equally significant threats.')
        self.assertTrue(x['needs_review']);self.assertIsNone(x['accepted_category'])

    def test_metrics_do_not_reward_accepting_review_case(self):
        r=[{'gold_review':False,'gold_category':'Operational','prediction':{'category':'Operational','needs_review':False}},
           {'gold_review':True,'gold_category':None,'prediction':{'category':'Market','needs_review':False}}]
        m=score(r)
        self.assertEqual(m['raw_accuracy_pct'],100)
        self.assertEqual(m['selective_accuracy_pct'],50)
        self.assertEqual(m['review_recall_pct'],0)

    def test_empty_denominator_is_na(self):
        r=[{'gold_review':False,'gold_category':'Operational','prediction':{'category':'Operational','needs_review':True}}]
        m=score(r)
        self.assertIsNone(m['selective_accuracy_pct']);self.assertIsNone(m['review_recall_pct'])
        self.assertEqual(m['correct_accepted_recall_pct'],0)

if __name__=='__main__':unittest.main()
