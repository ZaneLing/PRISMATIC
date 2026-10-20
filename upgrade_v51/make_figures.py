"""Scientific plot of frozen trajectories; no patient-level content."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent

def main():
 a=json.loads((HERE/'results/trajectory.json').read_text());b=json.loads((HERE/'results/cloud/trajectory.json').read_text());c=json.loads((HERE/'results/cloud/controls_transfer.json').read_text());assert a['complete'] and b['complete'] and c['complete']
 replay=json.loads((HERE/'results/decoder_replay.json').read_text())
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
 fig,axes=plt.subplots(1,3,figsize=(12.4,3.8))
 for d,label,color in [(a,'Local proposer','#c06b37'),(b,'Aggregate proposer / original decoder','#286a9c')]:
  rr=d['trajectory'];x=[r['cases_seen'] for r in rr]
  for ax,metric in zip(axes[:2],['drug_micro_f1','core_order_micro_f1']):ax.plot(x,[100*r['metrics'][metric] for r in rr],'-o',label=label,color=color,linewidth=2,markersize=5)
  axes[2].step(x,[r['retained'] for r in rr],where='post',label=label,color=color,linewidth=2);axes[2].scatter(x,[r['retained'] for r in rr],color=color,s=25)
 for ax,metric in zip(axes[:2],['drug_micro_f1','core_order_micro_f1']):
  rr=replay['trajectories']['aggregate'];ax.plot([r['cases_seen'] for r in rr],[100*r['metrics'][metric] for r in rr],':s',color='#286a9c',label='Same states / compatible decoder',linewidth=2,markersize=4)
 for ax,metric in zip(axes[:2],['drug_micro_f1','core_order_micro_f1']):ax.axhline(100*c['methods']['qwen']['static_ranked_draft'][metric],linestyle='--',color='#777777',linewidth=1.3,label='Static ranked draft')
 for ax,title in zip(axes,['A  Drug-set agreement','B  Joint-order agreement','C  Retained skill state']):
  ax.set_title(title,loc='left',fontsize=11);ax.set_xlabel('Cumulative reflection admissions');ax.set_xticks([0,24,48,72]);ax.grid(axis='y',alpha=.2);ax.set_ylim(bottom=0)
 axes[0].set_ylabel('Drug F1 (%)');axes[1].set_ylabel('Core4 F1 (%)');axes[2].set_ylabel('Accepted skills (count)')
 n=max(r['retained'] for d in [a,b] for r in d['trajectory']);axes[2].set_yticks(range(n+2));axes[2].set_ylim(0,n+1)
 handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=2,frameon=False,bbox_to_anchor=(.5,1.02))
 fig.text(.5,.005,'Exploratory audit: 48 historically exposed admissions; same 72 reflection cases in both runs. State growth is not clinical efficacy.',ha='center',fontsize=9,color='#444444')
 fig.tight_layout(rect=[0,.06,1,.85]);(HERE/'figures').mkdir(exist_ok=True)
 for suffix in ['png','svg']:fig.savefig(HERE/f'figures/evolution.{suffix}',dpi=180,bbox_inches='tight')
 svg=HERE/'figures/evolution.svg';svg.write_text('\n'.join(x.rstrip() for x in svg.read_text().splitlines())+'\n')
 plt.close(fig)
if __name__=='__main__':main()
