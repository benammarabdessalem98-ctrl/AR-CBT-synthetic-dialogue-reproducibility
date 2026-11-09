"""Numerical and input-validation tests; no LLM executions or fabricated data."""
import csv
import tempfile
import unittest
from pathlib import Path
import numpy as np
from reanalyse_scores import load_scores, summarize, categorical_audit

DATA=Path(__file__).resolve().parents[1]/'data'/'scores_80_original_columns.csv'
class Tests(unittest.TestCase):
    def test_source_means_and_correlations(self):
        ids,x=load_scores(DATA)
        r=summarize(ids,x,n_boot=100,seed=42)
        self.assertEqual(r['n_records'],80)
        self.assertAlmostEqual(r['series'][0]['mean'],4.04875,12)
        self.assertAlmostEqual(r['series'][1]['mean'],3.9775,12)
        self.assertAlmostEqual(r['reference_comparison']['pearson_r'],0.9204034464648122,12)
        self.assertAlmostEqual(r['reference_comparison']['spearman_rho'],0.926159,6)
        self.assertAlmostEqual(r['reference_comparison']['mean_difference'],0.008,12)
        self.assertAlmostEqual(r['reference_comparison']['mae'],0.3035,12)
    def test_categorical_reproduction(self):
        _,x=load_scores(DATA)
        r=categorical_audit(x[:,0],x[:,1])
        self.assertAlmostEqual(r['nearest_even']['kappa'],0.479505530253741,12)
        self.assertAlmostEqual(r['nearest_even']['observed_agreement'],0.625,12)
        self.assertAlmostEqual(r['cutoff_4']['observed_agreement'],0.8375,12)
    def test_duplicate_id_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.csv'; p.write_text('Session,Rater1,Rater2,ModelScore\nS1,1,2,3\nS1,2,3,4\n')
            with self.assertRaises(ValueError): load_scores(p)
    def test_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.csv'; p.write_text('Session,Rater1,Rater2,ModelScore\nS1,1,nan,3\n')
            with self.assertRaises(ValueError): load_scores(p)
    def test_constant_series_rejected(self):
        with self.assertRaises(ValueError): summarize(['A','B','C'],np.ones((3,3)),100,42)
    def test_bootstrap_reproducible(self):
        ids,x=load_scores(DATA)
        a=summarize(ids,x,n_boot=100,seed=42)
        b=summarize(ids,x,n_boot=100,seed=42)
        self.assertEqual(a['reference_comparison']['row_bootstrap_ci'],b['reference_comparison']['row_bootstrap_ci'])
if __name__=='__main__': unittest.main()
