"""Pinned author workflows with explicit transport and compatibility adapters.

No gold labels enter inference. Original repositories remain unmodified locally.
MDAgents needs documented source-level compatibility/correctness repairs;
their applied text and hashes are recorded by the protocol, not hidden as native.
"""
import ast
import hashlib
import importlib.util
import random
import re
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
RESOURCES = Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources'
sys.path.insert(0, str(ROOT/'upgrade_v8'))
from public_client import request
from agent import BASE

PINS = {'MedAgents': 'aaeff0499e169b41faf810cbca59504e3ee2788c',
        'MDAgents': '3adbd760ca809b4e7b0c1085d68314b6e7d91e1b'}
MODEL = 'deepseek/deepseek-v4.1-flash'


class APITransportFailure(RuntimeError):
    pass


class WorkflowBudgetExhausted(RuntimeError):
    pass


class Calls:
    def __init__(self, call_limit=80, output_limit=24000):
        self.rows = []
        self.call_limit = call_limit
        self.output_limit = output_limit

    def invoke(self, messages, max_tokens=1024, temperature=0):
        remaining = self.output_limit-sum(r.get('output_tokens') or 0 for r in self.rows)
        if len(self.rows) >= self.call_limit or remaining <= 0:
            raise WorkflowBudgetExhausted('Declared per-case budget exhausted')
        record = request(messages, MODEL, min(max_tokens, remaining),
                         role='medical_agent_author_adapter', temperature=temperature)
        if record.get('error'):
            raise APITransportFailure('Transport failure is not an incorrect model answer')
        self.rows.append(record)
        return record['raw']


def parse_answer(raw, n):
    """Strict answer-marked letter extraction, independent of ground truth."""
    raw = str(raw).replace('**', '').replace('\\boxed{', 'Answer: ').replace('}', '')
    raw = re.sub(r"(?m)^\s*['`]+", '', raw)
    patterns = [r'(?im)^\s*(?:(?:final|best|correct)\s+)?(?:answer|option|choice)\s*(?:is\s*)?[:=]\s*[\(\[]?([A-E])\b',
                r'(?i)\b(?:(?:the|correct|best)\s+)?(?:answer|option|choice)\s+is\s*[:\-]?\s*[\(\[]?([A-E])\b']
    found = []
    for pattern in patterns:
        found.extend((m.start(), m.group(1).upper()) for m in re.finditer(pattern, raw))
    if not found and re.fullmatch(r'\s*[\(\[]?[A-E][\)\].]?\s*', raw):
        found = [(0, re.search('[A-E]', raw).group())]
    answer = max(found)[1] if found else None
    return answer if answer in [chr(65+i) for i in range(n)] else None


def author_functions(path, namespace, replacements=()):
    text = path.read_text()
    for before, after in replacements:
        assert before in text, 'Pinned source replacement target changed'
        text = text.replace(before, after)
    tree = ast.parse(text)
    selected = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and getattr(n, 'name', '') != 'Agent']
    # The MedAgents constants are part of its prompts; other imports are supplied.
    selected += [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('NUM_QD','NUM_OD') for t in n.targets)]
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def medagents(case, calls):
    from nltk.tokenize import sent_tokenize
    base = RESOURCES/'MedAgents'
    ns = {'re': re, 'sent_tokenize': sent_tokenize}
    author_functions(base/'prompt_generator.py', ns)
    author_functions(base/'data_utils.py', ns)
    # Preserve a returned report if a formatting marker is absent; do not crash
    # or hallucinate a replacement report/answer.
    original_clean = ns['cleansing_syn_report']
    ns['cleansing_syn_report'] = lambda q,o,r: original_clean(q,o,r) if 'Total Analysis:' in r else f'Question: {q}\nOptions: {o}\nTotal Analysis: {r}'
    author_functions(base/'utils.py', ns)
    class Handler:
        def get_output_multiagent(self, user_input, temperature=0, max_tokens=512, system_role=''):
            return calls.invoke([{'role':'system','content':system_role}, {'role':'user','content':user_input}], max_tokens, temperature)
    options = {chr(65+i): value for i,value in enumerate(case['options'])}
    result = ns['fully_decode'](None, None, case['dialogue'], options, None, Handler(),
                               SimpleNamespace(method='syn_verif', max_attempt_vote=3), None)
    raw = result['raw_output']
    return {'prediction': parse_answer(raw,len(options)), 'raw_output': raw,
            'author_parser_prediction': result['pred_answer'],
            'workflow': {'question_experts':len(result['question_domains']),
                         'option_experts':len(result['option_domains']),
                         'vote_rounds':len(result['vote_history'])}}


MDA_REPAIRS = (
    ('print(f"{\'\\U0001F468\\u200D\\u2696\\uFE0F\'} moderator\'s final decision (by majority vote):", _decision)',
     'print("moderator final decision (by majority vote):", _decision)'),
    ('    final_answer = None\n', '    final_answer = dict(round_opinions[1])\n'),
    ('Investigation:\\n{initial_assessment_report}\\n\\nQuestion: {question}',
     'Investigation:\\n{initial_assessment_report}\\n{assessment_report}\\n{compiled_report}\\n\\nQuestion: {question}'),
    ("    lines = group_info.split('\\n')",
     "    lines = [re.sub(r'^[#\\s]*', '', line.replace('**', '').replace('–', '-').replace('—', '-')).strip() for line in group_info.split('\\n')]"),
    ('groups = [group.strip() for group in recruited.split("Group") if group.strip()]',
     'groups = [group.strip() for group in recruited.split("Group") if re.match(r"^\\d+\\s*[-–—]", group.strip())]'),
    ("agents_info = [agent_info.split(\" - Hierarchy: \") for agent_info in recruited.split('\\n') if agent_info]",
     "agents_info = [agent_info.split(\" - Hierarchy: \") for agent_info in recruited.replace('**','').replace('–','-').replace('—','-').split('\\n') if re.match(r'^\\s*\\d+\\.', agent_info)][:5]"),
)


def mdagents(case, calls):
    from pptree import Node
    from prettytable import PrettyTable
    rng = random.Random(int(hashlib.sha256(case['id'].encode()).hexdigest()[:8],16))
    class Agent:
        def __init__(self, instruction, role, examplers=None, model_info=None, img_path=None):
            self.role = role
            self.messages = [{'role':'system','content':instruction}]
            for e in examplers or []:
                self.messages += [{'role':'user','content':e['question']},
                                  {'role':'assistant','content':e['answer']+'\n\n'+e['reason']}]
        def chat(self, message, img_path=None, chat_mode=True):
            self.messages.append({'role':'user','content':message})
            response = calls.invoke(self.messages, 1024)
            self.messages.append({'role':'assistant','content':response})
            return response
        def temp_responses(self, message, img_path=None):
            self.messages.append({'role':'user','content':message})
            return {0.0: calls.invoke(self.messages,1024)}
    ns = {'Agent':Agent, 'random':rng, 're':re, 'Node':Node, 'PrettyTable':PrettyTable,
          'print':lambda *a,**k:None, 'cprint':lambda *a,**k:None,
          'print_tree':lambda *a,**k:None}
    author_functions(RESOURCES/'MDAgents/utils.py', ns, MDA_REPAIRS)
    question = case['dialogue']+' Options: '+' '.join(f'({chr(65+i)}) {x}' for i,x in enumerate(case['options']))
    difficulty = ns['determine_difficulty'](question, 'adaptive')
    args = SimpleNamespace(dataset='public_option_qa')
    if difficulty == 'basic':
        result = ns['process_basic_query'](question, [], MODEL, args)
    elif difficulty == 'intermediate':
        result = ns['process_intermediate_query'](question, [], MODEL, args)
    elif difficulty == 'advanced':
        result = ns['process_advanced_query'](question, MODEL, args)
    else:
        return {'prediction':None, 'workflow':{'difficulty':difficulty}, 'raw_output':''}
    while isinstance(result,dict):
        result = next(iter(result.values()))
    return {'prediction':parse_answer(result,len(case['options'])), 'raw_output':result,
            'workflow':{'difficulty':difficulty}}


def run(method, case, call_limit=80, output_limit=24000):
    calls = Calls(call_limit,output_limit)
    # Drop labels and metadata before invoking either workflow.
    actor_case = {k:case[k] for k in ('id','dialogue','options')}
    if case.get('type') in ('contraindication','interaction'):
        # RxSafe source items are consultations, not standalone questions.
        # Give author workflows the same explicit task instruction as our actor.
        actor_case['dialogue'] = BASE+'\nCurrent consultation:\n'+case['dialogue']
    try:
        result = {'medagents':medagents, 'mdagents':mdagents}[method](actor_case,calls)
        result['status'] = 'complete' if result['prediction'] else 'invalid_final_answer'
    except WorkflowBudgetExhausted:
        result = {'prediction':None, 'status':'budget_exhausted'}
    except (IndexError,KeyError,ValueError,TypeError) as exc:
        result = {'prediction':None,'status':'workflow_parse_failure','error_type':type(exc).__name__}
    return {**result, 'case_id':case['id'], 'calls':calls.rows}
