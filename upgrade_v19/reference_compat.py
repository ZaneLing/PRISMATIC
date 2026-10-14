"""Lossless views for legacy reference shapes; never alter submitted resources."""
import copy,json,types

def reference_view(trace):
    out=copy.deepcopy(trace);changes=[]
    for i,m in enumerate(out):
        if m.get('role')!='agent' or not m.get('content','').startswith('POST '):continue
        try:
            line,body=m['content'].split('\n',1);payload=json.loads(body)
        except (ValueError,TypeError):continue
        if not isinstance(payload,dict):continue
        changed=[]
        note=payload.get('note')
        if payload.get('resourceType')=='ServiceRequest' and isinstance(note,list) and len(note)==1 and isinstance(note[0],dict) and isinstance(note[0].get('text'),str):
            payload['note']=note[0];changed.append('note:singleton Annotation array -> legacy object view')
        if payload.get('resourceType')=='MedicationRequest':
            for j,d in enumerate(payload.get('dosageInstruction') or []):
                if not isinstance(d,dict):continue
                route=d.get('route')
                if isinstance(route,dict) and set(route)=={'text'} and isinstance(route['text'],str):
                    d['route']=route['text'];changed.append(f'dosageInstruction[{j}].route:text-only CodeableConcept -> legacy text view')
        if changed:
            m['content']=line+'\n'+json.dumps(payload);changes.append({'trace_index':i,'conversions':changed})
    return out,changes

def regrade_cached(row,case,grader,base):
    """Regrade unchanged physical evidence under the registered revised endpoint."""
    out=copy.deepcopy(row);semantic,changes=reference_view(out['live_trace'])
    def grade(trace):
        if out['status']!='completed' or out['answer'] is None:return False
        obj=types.SimpleNamespace(history=[types.SimpleNamespace(**m) for m in trace],result=out['answer'])
        return bool(getattr(grader,case['id'].split('_')[0])(case,obj,base))
    out['original_trace_correct']=grade(out['original_trace']);out['legacy_live_reference_correct']=grade(out['live_trace'])
    out['semantic_reference_correct']=grade(semantic);out['semantic_trace']=semantic;out['reference_projection_audits']=changes
    out['live_execution_correct']=out['semantic_reference_correct'] and all(out['active_post_checks'])
    out['grading_revision']='lossless_reference_views_v2';return out
