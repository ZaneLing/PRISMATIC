"""Model-envelope handling, separate from unchanged order membership/scoring."""
import re
from rx_agent import compile_selection

def compile_model_selection(raw,catalogue):
    strict=compile_selection(raw,catalogue)
    text=raw.strip()
    # Qwen's supervised chat template emits an empty reasoning envelope.
    # Remove only that exact empty envelope, never nonempty reasoning or prose.
    cleaned=re.sub(r'^<think>\s*</think>\s*','',text,count=1)
    result=compile_selection(cleaned,catalogue)
    return {**result,'raw_strict_status':strict['status'],'empty_reasoning_envelope_removed':cleaned!=text}

def bind_cached_output(row,case):
    # Equal prompts legitimately share model output. Case identity and expanded
    # catalogue fields belong to the current evaluation case, never the cache writer.
    return {**row,**compile_model_selection(row['raw'],case['catalogue']),'case_id':case['case_id']}
