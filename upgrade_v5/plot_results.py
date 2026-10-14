"""Export aggregate-only scientific plots and the implemented architecture."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE=Path(__file__).resolve().parent
def run():
    r=json.loads((HERE/'results/ranker_memory_results.json').read_text())
    g=r['growth'];xs=[x['memory_size'] for x in g]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(8.4,4.6),layout='constrained')
    ax.plot(xs,[x['validation_f1'] for x in g],marker='o',label='Validation (selects versions)',color='#167c80')
    ax.plot(xs,[x['test']['micro_f1_at_5'] for x in g],marker='s',label='Development test',color='#283a65')
    ax.set_xscale('symlog',linthresh=250)
    ax.set_xticks(xs,[f"{x['memory_size']:,}" for x in g]);ax.set_xlabel('Training episodes in residual memory (symlog scale)')
    ax.set_ylabel('Observed micro-F1@5');ax.set_ylim(.344,.356)
    ax.set_title('Frozen 8,000-admission base: more memory is not monotonic',loc='left',fontweight='bold',pad=14)
    ax.grid(axis='y',alpha=.18);ax.legend(loc='lower right',frameon=False)
    fig.savefig(HERE/'results/memory_growth.png',dpi=180);fig.savefig(HERE/'results/memory_growth.svg')
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(11.4,8),layout='constrained');ax.set_xlim(0,12);ax.set_ylim(0,10);ax.axis('off')
    def box(x,y,w,h,title,body,fill='#edf3f8',edge='#283a65'):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.10,rounding_size=0.08',facecolor=fill,edgecolor=edge,linewidth=1.3))
        ax.text(x+w/2,y+h*.68,title,ha='center',va='center',weight='bold',fontsize=10.5,color='#162a42')
        ax.text(x+w/2,y+h*.30,body,ha='center',va='center',fontsize=9.2,color='#34465a')
    def arrow(a,b):ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':'#52677d','lw':1.3})
    ax.text(.25,9.7,'PRISMATIC v0.5 | Implemented research pipeline',weight='bold',fontsize=17,color='#162a42')
    ax.text(.25,9.28,'4,000-case ranker evaluation + 50-case local-LLM evaluation; no clinical clearance',fontsize=10.5,color='#52677d')
    box(.35,7.85,6.35,1,'Admission snapshot + availability audit','Complaint, acuity, home medications; timing limits retained')
    box(.35,6.3,6.35,1,'Statistical candidates + residual-memory fusion','Word/character ensemble; fusion weight selected on validation')
    box(.35,4.75,6.35,1,'Retrieve cases + collect coarse risk flags','Training cases and TWOSIDES ATC-class graph')
    box(.35,3.2,6.35,1,'Local Qwen revision + parser recovery','Missing evidence = unknown; valid members survive parsing')
    box(.35,1.65,6.35,1,'Validation gate','Accept candidate edits only if validation F1 improves')
    box(.35,.1,3.05,1,'Historical predictions','Research candidates only',fill='#e7f3f1',edge='#167c80')
    box(3.65,.1,3.05,1,'Clinical status','Needs information; no orders',fill='#fff5df',edge='#b78529')
    for y in [7.85,6.3,4.75,3.2]:arrow((3.525,y-.1),(3.525,y-.55))
    arrow((2.0,1.55),(1.875,1.20));arrow((5.0,1.55),(5.175,1.20))
    box(7.45,7.85,4.0,1,'Training-only episode ledger','Observed records, not clinical truth',fill='#e7f3f1',edge='#167c80')
    box(7.45,6.05,4.0,1.25,'Frozen base + residual retrieval','8k base; 250 to 32k memory cases\n30 neighbors at every checkpoint',fill='#e7f3f1',edge='#167c80')
    box(7.45,4.25,4.0,1.15,'Validation replay + versioning','Promote or keep previous version\nTest feedback is rejected',fill='#e7f3f1',edge='#167c80')
    arrow((9.45,7.75),(9.45,7.4));arrow((9.45,5.95),(9.45,5.5));arrow((7.35,6.67),(6.8,6.8))
    ax.text(7.45,3.35,'What this does not yet establish',weight='bold',fontsize=10.5,color='#8b6325')
    ax.text(7.45,2.95,'• Saline indication, volume or rate\n• Clinician-rated order correctness\n• Ingredient-level safety clearance\n• Live FHIR task success\n• Superiority over faithful SafeRx',fontsize=10,va='top',linespacing=1.8,color='#52677d')
    fig.savefig(HERE/'results/architecture.png',dpi=180);fig.savefig(HERE/'results/architecture.svg')
    plt.close(fig)
    for path in (HERE/'results').glob('*.svg'):
        path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')

if __name__=='__main__':run()
