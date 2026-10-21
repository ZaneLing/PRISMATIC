"""Scientific plot from saved aggregates only."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common53 import *
def main():
    r=json.loads((HERE/'results/audit.json').read_text());fig,axes=plt.subplots(2,3,figsize=(12,6.5))
    endpoints=[('missed_drugs_per_patient','Missed drug identities'),('extra_drugs_per_patient','Extra drug identities'),('joint_errors_per_patient','Complete-tuple discrepancies')]
    for row,model in enumerate(['qwen','llama']):
        for col,(metric,label) in enumerate(endpoints):
            ax=axes[row,col]
            for seed,color in zip([53,153,253],['#0072B2','#D55E00','#009E73']):
                seq=r['trajectories'][model]['library_'+str(seed)]
                ax.plot([x['feedback'] for x in seq],[x['metrics'][metric] for x in seq],marker='o',markersize=3,color=color,label='Case order '+str(seed))
            ax.axhline(r['metrics'][model]['fixed']['metrics'][metric],color='#555555',ls='--',lw=1,label='Frozen actor')
            ax.set_title(model.capitalize()+' — '+label,fontsize=10);ax.set_xlabel('Feedback patients seen');ax.set_ylabel('Errors per audit patient ↓');ax.grid(alpha=.2)
            ax.set_xticks([0,32,64,96,128,160,192])
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,ncol=4,loc='lower center',frameon=False)
    fig.suptitle('RxRSIAgent: all frozen rounds on the same 256 new patients',fontsize=14)
    fig.tight_layout(rect=[0,.07,1,.94]);fig.savefig(HERE/'results/retention.png',dpi=170);plt.close(fig)
if __name__=='__main__':main()
