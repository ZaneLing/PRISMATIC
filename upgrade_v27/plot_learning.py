"""Publication-oriented static plots from audited aggregate development results."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
def main():
    s=json.loads((HERE/'results/rsi_development_summary.json').read_text());assert s['status']=='complete'
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,3,figsize=(13.5,4.5),gridspec_kw={'width_ratios':[1,1,1.3]})
    colors={'uniform_policy':'#667085','own_error_rule_agent':'#126C8F'}
    for ax,panel in zip(axes[:2],['full','molecular']):
        p=s['panels'][panel]
        for arm,label in [('uniform_policy','Shared policy'),('own_error_rule_agent','Policy + agent memory')]:
            rows=p['proposal_curves'][arm];x=[r['training_patients'][0] for r in rows];values=np.array([r['proposal_patient_f1'] for r in rows])*100
            mean=values.mean(1);sd=values.std(1,ddof=1)
            ax.plot(x,mean,marker='o' if arm=='uniform_policy' else 's',linestyle='--' if arm=='uniform_policy' else '-',label=label,color=colors[arm],markersize=4)
            ax.fill_between(x,mean-sd,mean+sd,alpha=.12,color=colors[arm])
        ax.set_title(('Full 271-class' if panel=='full' else 'Molecular 219-class')+' panel',loc='left',weight='bold')
        ax.set_xlabel('Training patients');ax.set_ylabel('Proposal patient F1 (%)');ax.set_ylim(52,63);ax.set_xticks([1423,4269,7115]);ax.grid(axis='y',alpha=.15)
    axes[0].legend(frameon=False,fontsize=8,loc='upper left')
    ax=axes[2];labels=[];y=0
    for panel in ['full','molecular']:
        for control,label in [('uniform_policy','Shared policy'),('greedy_error_rules','Greedy rules'),('shuffled_evidence_rule_agent','Shuffled agent')]:
            q=s['panels'][panel]['own_agent_minus_control'][control]['patient_f1'];m=100*q['difference'];lo,hi=np.array(q['patient_ci95'])*100
            ax.errorbar(m,y,xerr=[[m-lo],[hi-m]],fmt='o',color='#126C8F' if panel=='full' else '#A35D26',capsize=3,markersize=4)
            labels.append(('Full' if panel=='full' else 'Molecular')+' / '+label);y+=1
        y+=.35
    ax.set_yticks([0,1,2,3.35,4.35,5.35],labels);ax.invert_yaxis();ax.axvline(0,color='#667085',linestyle='--',linewidth=.8)
    ax.set_title('Agent increment on guard',loc='left',weight='bold');ax.set_xlabel('F1 difference (percentage points)');ax.grid(axis='x',alpha=.15)
    fig.suptitle('Rule-memory evolution: data-growth gains and incremental contribution',x=.045,ha='left',fontsize=14,weight='bold')
    fig.text(.045,.025,'Development only. Left: mean ± seed SD (3 seeds), proposal selects versions. Right: 4,000 patient-paired resamples after seed averaging.',fontsize=8,color='#475467')
    fig.tight_layout(rect=[0,.065,1,.94],w_pad=2)
    out=HERE.parent/'paper/figures';out.mkdir(exist_ok=True)
    for ext in ['png','svg']:fig.savefig(out/('rule_memory_development.'+ext),dpi=180,bbox_inches='tight')
    plt.close(fig)
    print(json.dumps({'status':'written','source':'upgrade_v27/results/rsi_development_summary.json','outputs':['paper/figures/rule_memory_development.png','paper/figures/rule_memory_development.svg']}))
if __name__=='__main__':main()
