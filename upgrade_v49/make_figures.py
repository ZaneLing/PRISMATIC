"""Publication-style plots using completed aggregate measurements only."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import *

def main():
    audit=json.loads((HERE/'results/audit.json').read_text());curve=json.loads((HERE/'results/round_curve.json').read_text())
    transfer=json.loads((HERE/'results/transfer.json').read_text());assert curve['complete'] and transfer['complete']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(15,4.8),gridspec_kw={'width_ratios':[1.35,1,1]})
    names=['direct','saferx','skemex','rxrsi_base','rxrsi_selected'];labels=['Direct\nrefinement','SafeRx\nadaptation','SkeMex\nmemory core','RxRSI\ninitial','RxRSI\nretained'];xx=np.arange(len(names))
    for offset,key,label,color in [(-.18,'drug_micro_f1','Drug F1','#266b98'),(.18,'core_order_micro_f1','Core4 F1','#cf8c32')]:
        vals=[100*audit['methods'][n]['metrics'][key] for n in names]
        axes[0].bar(xx+offset,vals,.34,label=label,color=color)
    axes[0].set_xticks(xx,labels,fontsize=8);axes[0].set_ylabel('F1 (%)');axes[0].set_title('A. Same-backbone local adaptations');axes[0].legend(frameon=False,fontsize=8)
    states=curve['trajectory'];xs=[r['cases_seen'] for r in states]
    for key,label,color in [('drug_micro_f1','Drug F1','#266b98'),('core_order_micro_f1','Core4 F1','#cf8c32')]:
        vals=[100*r['metrics'][key] for r in states]
        axes[1].plot(xs,vals,'o-',label=label,color=color)
        axes[1].annotate(f'{vals[-1]:.2f}',(xs[-1],vals[-1]),xytext=(0,8),textcoords='offset points',ha='center',fontsize=9)
    axes[1].set_xticks(xs);axes[1].set_xlabel('New reflection cases (second phase)');axes[1].set_ylabel('Full-test F1 (%)');axes[1].set_title('B. Frozen retained-state trajectory');axes[1].legend(frameon=False,fontsize=8)
    entries=[('Qwen3-4B',audit['methods']['rxrsi_base']['metrics'],audit['methods']['rxrsi_selected']['metrics']),
      ('Llama-3.2-3B',transfer['methods']['rxrsi_base'],transfer['methods']['rxrsi_selected'])]
    for i,(label,a,b) in enumerate(entries):
        axes[2].plot([0,1],[100*a['drug_micro_f1'],100*b['drug_micro_f1']],'o-',label=label,color=['#266b98','#975fa0'][i])
        axes[2].annotate(f"{100*b['drug_micro_f1']:.2f}",(1,100*b['drug_micro_f1']),xytext=(6,0),textcoords='offset points',va='center',fontsize=9)
    axes[2].set_xticks([0,1],['Initial','Retained']);axes[2].set_xlim(-.12,1.3);axes[2].set_ylabel('Drug F1 (%)');axes[2].set_title('C. Frozen-state cross-backbone transfer');axes[2].legend(frameon=False,fontsize=8)
    for ax in axes:ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.set_ylim(bottom=0)
    fig.suptitle('MIMIC-IV: 1,082 admissions, new/change orders in hours 6–12',fontsize=14,y=1.01)
    fig.text(.01,-.04,'Exploratory, historically exposed test. SafeRx/SkeMex are limited adaptations; no full-author-method superiority is implied.\nThe first 72 reflection cases retained no rule. Identical retained states reuse predictions. FLAME component transfer is reported separately.',fontsize=9)
    fig.tight_layout();out=HERE/'figures';out.mkdir(exist_ok=True)
    for suffix in ['svg','png']:fig.savefig(out/('prescription_results.'+suffix),dpi=180,bbox_inches='tight')
    plt.close(fig)
    print('Wrote aggregate result figures')
if __name__=='__main__':main()
