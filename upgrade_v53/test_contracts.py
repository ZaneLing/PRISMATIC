import unittest,copy
from clinical_checks import check
from programs import execute,applies,joint_field_mismatch
from runtime import run_decoded
O={'drug_code':'synthetic:x','route':'oral','dosage':'1 mg','frequency':'daily'}
C={'context':{'diagnoses':['cardiovascular|hypertension|hypertension'],'prior_orders':[]}}
class Contracts(unittest.TestCase):
 def test_reference_not_visible(self):
  card=dict(op='remove',drug_code='synthetic:x',template=None,when=['dx:cardiovascular|hypertension'],unless=[])
  self.assertEqual(execute(C,[O],[card]),[])
  c=copy.deepcopy(C);c['gold']=[O];self.assertEqual(execute(c,[O],[card]),[])
 def test_exception_protects(self):
  card=dict(op='remove',drug_code='synthetic:x',template=None,when=['dx:cardiovascular|hypertension'],unless=['prior_record:present'])
  c=copy.deepcopy(C);c['context']['prior_orders']=[O];self.assertFalse(applies(c,card))
  self.assertEqual(execute(c,[O],[card]),[O])
 def test_scope_boundary(self):
  card=dict(op='remove',drug_code='synthetic:x',template=None,when=['dx:cardiovascular|hypertension'],unless=[])
  c=copy.deepcopy(C);c['context']['diagnoses']=['cardiovascular|hypotension'];self.assertEqual(execute(c,[O],[card]),[O])
 def test_all_actions_target_identity_only(self):
  other=dict(O,drug_code='synthetic:y');new=dict(O,dosage='2 mg')
  card=dict(op='replace',drug_code='synthetic:x',template=new,when=['dx:cardiovascular|hypertension'],unless=[])
  self.assertEqual(execute(C,[O,other],[card]),[other,new])
  card['op']='add';self.assertEqual(execute(C,[other],[card]),[other,new])
 def test_missing_wrong_unit_and_future_not_normal(self):
  for facts in [{},{'egfr':{'value':90,'unit':'mg/dL','measured_at':359,'available_at':359}},{'egfr':{'value':90,'unit':'mL/min/1.73m2','measured_at':350,'available_at':361}}]:
   self.assertEqual(check('metformin',facts)['checks'][0]['status'],'unknown')
 def test_renal_boundaries(self):
  for value,status in [(29.9,'contraindication'),(30,'initiation_not_recommended'),(44.9,'initiation_not_recommended'),(45,'no_trigger')]:
   facts={'egfr':{'value':value,'unit':'mL/min/1.73m2','measured_at':350,'available_at':350},'intent':{'value':'initiate','available_at':350,'provenance':'synthetic explicit order intent'}}
   self.assertEqual(check('metformin',facts)['checks'][0]['status'],status)
 def test_intent_not_inferred_from_missing_prior(self):
  facts={'potassium':{'value':5.6,'unit':'mEq/L','measured_at':350,'available_at':350}}
  self.assertEqual(check('eplerenone',facts)['checks'][1]['status'],'review_required')
  facts['intent']={'value':'initiate','available_at':350,'provenance':'synthetic explicit order intent'};self.assertEqual(check('eplerenone',facts)['checks'][1]['status'],'contraindication')
 def test_crcl_not_egfr(self):
  facts={'egfr':{'value':20,'unit':'mL/min/1.73m2','measured_at':350,'available_at':350}}
  self.assertEqual(check('enoxaparin',facts)['checks'][0]['status'],'unknown')
 def test_counterexample_changes_check(self):
  f={'crcl':{'value':29,'unit':'mL/min','measured_at':350,'available_at':350}}
  self.assertEqual(check('enoxaparin',f)['checks'][0]['status'],'dose_review_required')
  f['crcl']['value']=30;self.assertEqual(check('enoxaparin',f)['checks'][0]['status'],'no_trigger')
  self.assertEqual(check('enoxaparin',f)['clinical_appropriateness'],'not_assessed')
 def test_shared_fields_denominator(self):
  self.assertEqual(joint_field_mismatch([dict(O,dosage='2 mg')],[O]),(1,1))
  self.assertEqual(joint_field_mismatch([],[O]),(0,0))
 def test_categorical_facts_also_need_time_and_source(self):
  for acidosis in [True,{'value':True,'available_at':361,'provenance':'synthetic'},{'value':True,'available_at':350}]:
   self.assertEqual(check('metformin',{'active_metabolic_acidosis':acidosis})['checks'][1]['status'],'unknown')
  f={'active_metabolic_acidosis':{'value':True,'available_at':350,'provenance':'synthetic assessment'}}
  self.assertEqual(check('metformin',f)['checks'][1]['status'],'contraindication')
 def test_stale_or_negative_measurement_unknown(self):
  for value,time in [(90,-1),(-10,350),(float('nan'),350)]:
   f={'egfr':{'value':value,'unit':'mL/min/1.73m2','measured_at':time,'available_at':time}}
   self.assertEqual(check('metformin',f)['checks'][0]['status'],'unknown')
 def fallback_case(self):
  c=copy.deepcopy(C);c['context']['available_labs']=[];c.update(catalogue={'O1':O},frozen_draft=['O1'],drug_names={})
  return c
 def test_valid_empty_is_not_overridden(self):
  r=run_decoded(self.fallback_case(),dict(orders=[],syntax_failure=False,invalid_ids=0))
  self.assertEqual(r['orders'],[]);self.assertFalse(r['fallback_used'])
 def test_malformed_output_falls_back_with_provenance(self):
  r=run_decoded(self.fallback_case(),dict(orders=[],syntax_failure=True,invalid_ids=0),enable_fallback=True)
  self.assertEqual(r['orders'],[O]);self.assertEqual(r['order_source'],'frozen_supervised_draft')
 def test_known_subset_preserved(self):
  r=run_decoded(self.fallback_case(),dict(orders=[O],syntax_failure=False,invalid_ids=1))
  self.assertEqual(r['orders'],[O]);self.assertFalse(r['fallback_used'])
 def test_revision_does_not_refresh_old_measurement(self):
  f={'egfr':{'value':90,'unit':'mL/min/1.73m2','measured_at':-500,'available_at':350}}
  self.assertEqual(check('metformin',f)['checks'][0]['status'],'unknown')
if __name__=='__main__':unittest.main()
