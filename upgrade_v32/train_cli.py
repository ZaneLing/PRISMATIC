"""Use the original MLX training loop with the registered binary-decision loss."""
import argparse,functools,json,sys
from pathlib import Path
from mlx_lm import lora
from decision_loss import decision_loss
def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--decision-arm',required=True,choices=['teacher_uniform','zero_uniform','teacher_balanced','zero_balanced']);parser.add_argument('--decision-config',required=True);args,rest=parser.parse_known_args();sys.argv=[sys.argv[0]]+rest
    c=json.loads(Path(args.decision_config).read_text());prefix,balance=args.decision_arm.split('_')
    loss=functools.partial(decision_loss,offsets=c['decision_offsets'],zero_id=c['zero_token_id'],one_id=c['one_token_id'],prefix=prefix,positive_weight=c['training_positive_weight'] if balance=='balanced' else 1.)
    original=lora.train
    def train_with_binary_loss(*args,**kwargs):kwargs['loss']=loss;return original(*args,**kwargs)
    lora.train=train_with_binary_loss;lora.main()
if __name__=='__main__':main()
