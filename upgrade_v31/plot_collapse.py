"""Static research figure from the audited diagnostic aggregates only."""
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
def main():
    path=HERE/'results/collapse_diagnostic.json';z=json.loads(path.read_text());a=json.loads((HERE/'results/collapse_diagnostic_audit.json').read_text());assert a['status']=='passed' and a['source_report_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    fig,axes=plt.subplots(1,2,figsize=(11,4.4));labels=['Base\nranked','Updated\nranked','Base\npermuted','Updated\npermuted'];states=['frozen_base','permuted_uniform_seed42_round1'];groups=['proposal_ranked','proposal_permuted'];x=np.arange(4);w=.35
    oracle=[];zero=[];positive=[];negative=[]
    for group in groups:
        for state in states:
            d=z['states'][state][group];oracle.append(d['teacher_forced_ground_truth_prefix']['auroc']);q=d['all_zero_prefix_without_ground_truth'];zero.append(q['auroc']);positive.append(q['mean_probability_given_positive']);negative.append(q['mean_probability_given_negative'])
    for offset,values,label,color in [(-w/2,oracle,'Oracle GT prefix','#8c8c8c'),(w/2,zero,'Zero prefix (no answer labels)','#3274a1')]:axes[0].bar(x+offset,values,w,label=label,color=color)
    axes[0].axhline(.5,color='black',linewidth=.8,linestyle=':');axes[0].set(title='Binary discrimination',ylabel='Conditional AUROC',ylim=(0,1));axes[0].legend(fontsize=8,loc='lower left')
    for offset,values,label,color in [(-w/2,positive,'Ground-truth positive','#3274a1'),(w/2,negative,'Ground-truth negative','#cf815b')]:axes[1].bar(x+offset,values,w,label=label,color=color)
    axes[1].axhline(.5,color='black',linewidth=.8,linestyle=':',label='Binary argmax boundary');axes[1].set(title='Zero-prefix probabilities',ylabel='Mean P(1 | token is 0 or 1)',ylim=(0,.65));axes[1].legend(fontsize=8,loc='upper right')
    for ax in axes:ax.set_xticks(x,labels);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    fig.suptitle('Frozen-checkpoint diagnosis: 32 proposal cases, two views\nExploratory conditional scores; oracle-prefix results are not deployable accuracy',fontsize=11);fig.tight_layout()
    for suffix in ['png','svg']:fig.savefig(HERE/f'collapse_probability.{suffix}',dpi=180,bbox_inches='tight')
    plt.close(fig)
if __name__=='__main__':main()
