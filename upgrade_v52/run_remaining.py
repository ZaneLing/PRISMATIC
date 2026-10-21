"""Complete the fixed experiment after development inference, with resumable files."""
import subprocess,time,sys
from common52 import *
PY=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv/bin/python'
MLX=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python'
def run(script,*args,mlx=False):
 subprocess.run([str(MLX if mlx else PY),str(HERE/script),*args],check=True,cwd=str(ROOT))
def main():
 while not (PRIVATE/'actor_lock.json').exists():time.sleep(15)
 for seed in [52,152]:
  if not (PRIVATE/f'qwen-{seed}-states.json').exists():run('learn.py','--seed',str(seed))
 if not (PRIVATE/'qwen-52-shuffle-states.json').exists():run('learn.py','--seed','52','--shuffle')
 if not (PRIVATE/'tool-52-states.json').exists():run('learn.py','--backbone','tool')
 if not (PRIVATE/'selection_lock.json').exists():run('freeze.py')
 run('actor.py','--splits','audit',mlx=True)
 run('actor.py','--model','llama','--splits','audit',mlx=True)
 run('evaluate.py')
 print('Frozen study complete. Report generation and manuscript verification are separate.',flush=True)
if __name__=='__main__':main()
