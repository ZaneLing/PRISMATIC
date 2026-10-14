"""Twenty binary drug decisions with explicit control of answer-prefix exposure."""
import mlx.core as mx
import mlx.nn as nn

def positions(lengths,offsets):return lengths[:,0:1]+mx.array(offsets,dtype=mx.int32)[None,:]
def inputs_and_labels(batch,lengths,offsets,zero_id,one_id,prefix):
    pos=positions(lengths,offsets);labels=(mx.take_along_axis(batch,pos,axis=1)==one_id).astype(mx.int32);inputs=batch[:,:-1]
    if prefix=='zero':
        # Mask only declared answer decisions, leaving every prompt token intact.
        decision=(mx.arange(inputs.shape[1])[None,:,None]==pos[:,None,:]).any(axis=-1)
        inputs=mx.where(decision,zero_id,inputs)
    elif prefix!='teacher':raise ValueError(prefix)
    return inputs,labels,pos
def logits_at_decisions(model,inputs,pos,zero_id,one_id):
    hidden=model.model(inputs);chosen=mx.take_along_axis(hidden,(pos-1)[:,:,None],axis=1)
    all_logits=model.model.embed_tokens.as_linear(chosen) if model.args.tie_word_embeddings else model.lm_head(chosen)
    return all_logits[:,:,mx.array([zero_id,one_id])].astype(mx.float32)
def decision_loss(model,batch,lengths,offsets,zero_id,one_id,prefix,positive_weight=1.):
    inputs,labels,pos=inputs_and_labels(batch,lengths,offsets,zero_id,one_id,prefix)
    logits=logits_at_decisions(model,inputs,pos,zero_id,one_id);weights=mx.where(labels==1,positive_weight,1.)
    loss=(nn.losses.cross_entropy(logits,labels)*weights).sum()/weights.sum()
    # The trainer's token counter counts actual supervised decisions, not weights.
    return loss,mx.array(labels.size,dtype=mx.int32)
