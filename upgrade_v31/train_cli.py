"""Use the installed trainer with a completion-only loss that excludes padding.

The installed default uses steps <= sequence_length on a next-token target,
which includes the first padded target. We pass a strict mask to the public
trainer loss argument without editing the installed library.
"""
import mlx.core as mx
import mlx.nn as nn
from mlx_lm import lora

def completion_loss(model,batch,lengths):
    inputs=batch[:,:-1];targets=batch[:,1:];logits=model(inputs);steps=mx.arange(1,targets.shape[1]+1)
    mask=(steps>=lengths[:,0:1])&(steps<lengths[:,1:]);count=mask.sum()
    return (nn.losses.cross_entropy(logits,targets)*mask).astype(mx.float32).sum()/count,count

def main():
    original=lora.train
    def train_with_completion_mask(*args,**kwargs):
        kwargs['loss']=completion_loss
        return original(*args,**kwargs)
    lora.train=train_with_completion_mask
    lora.main()
if __name__=='__main__':main()
