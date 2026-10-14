"""Draw the implemented system and distinguish inference from training feedback."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch

HERE=Path(__file__).resolve().parent
fig,ax=plt.subplots(figsize=(15,7.6))
fig.patch.set_facecolor('#f6f8fc');ax.set_facecolor('#f6f8fc')
ax.set_xlim(0,15);ax.set_ylim(0,7.6);ax.axis('off')
ax.text(.35,7.15,'RxRSIAgent | Prescription generation and supervised evolution',fontsize=19,weight='bold',color='#17243b')
ax.text(.35,6.72,'Implemented v0.6 • local patient data • validation selects the deployed variant',fontsize=12,color='#455873')
xs=[.35,4.05,7.75,11.45];width=3.2;height=1.35
def box(x,y,title,body,fill):
    ax.add_patch(FancyBboxPatch((x,y),width,height,boxstyle='round,pad=0.03,rounding_size=.12',facecolor=fill,edgecolor='#c3cfdf'))
    ax.text(x+.15,y+1.04,title,fontsize=12,weight='bold',color='#17243b')
    ax.text(x+.15,y+.72,body,fontsize=10.5,va='top',linespacing=1.5,color='#33465f')
def arrow(a,b):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=15,color='#60738e',linewidth=1.6))
top=[('1  Patient snapshot','Complaint, acuity, home meds\nNo current target prescription'),
 ('2  Prescription tools','Learned drug-selection policy\nJoint order templates + episodes'),
 ('3  Selected planner','Active: learned policy\nCandidate: local LLM + memory'),
 ('4  Research prescription','Drug / route / dose / unit / freq.\nUnknown fields stay unknown')]
for x,(title,body) in zip(xs,top):box(x,4.65,title,body,'#e4eefb')
for x in xs[:-1]:arrow((x+width,5.32),(x+3.7,5.32))
bottom=[('8  Version selection','Fixed validation replay\nPromote or keep prior version'),
 ('7  Update system','Policy weights + case memory\nJoint order-template statistics'),
 ('6  Typed error feedback','Missed / extra medications\nRoute / dose / frequency errors'),
 ('5  Training GT comparison','Predict before revealing labels\nScore GT automatically')]
for x,(title,body) in zip(xs,bottom):box(x,2.1,title,body,'#e1f3ed')
for x in xs[1:]:arrow((x,2.78),(x-.5,2.78))
arrow((13.05,4.65),(13.05,3.45))
ax.text(13.25,3.94,'Training only',fontsize=10,color='#2f715d')
arrow((1.95,3.45),(1.95,4.65))
ax.text(2.1,3.94,'New version',fontsize=10,color='#2f715d')
ax.text(.35,1.43,'Test labels → scoring only. No test-label feedback into policy, memory or planner selection.',fontsize=12,weight='bold',color='#17243b')
ax.text(.35,.91,'What evolves now: prescription policy weights, training episodes and order templates. LLM weights remain frozen.',fontsize=11,color='#455873')
ax.text(.35,.48,'Next mechanisms: regression-tested skill edits and GT-based LLM fine-tuning. These are not claimed as completed.',fontsize=11,color='#455873')
fig.savefig(HERE/'architecture.png',dpi=150,bbox_inches='tight');plt.close(fig)
