"""Synthetic equivalence checks for the declared author-core adaptations."""
import copy, hashlib, json
from pathlib import Path
import numpy as np
import torch
from author_cores import armr, safedrug, ROOT
from method_runtime import sparse_molecular_pad, prefix, armr_input, loss_for

HERE = Path(__file__).resolve().parent

def delta(a, b):
    torch.testing.assert_close(a, b, rtol=2e-4, atol=2e-5)
    return float((a-b).detach().abs().max())

def main():
    torch.set_num_threads(1)
    torch.manual_seed(42)
    sizes = (12, 9, 8)
    ddi = np.zeros((8, 8), dtype=np.float32)
    ddi[0, 1] = ddi[1, 0] = 1
    ehr = np.eye(8, dtype=np.float32)
    molecules = json.loads((ROOT/'v27-molecules/atc4_molecules.json').read_text())
    classes = sorted(molecules)[:8]
    core = safedrug()
    graphs, nfp, projection = core.buildMPNN({c: [molecules[c][0]['smiles']] for c in classes}, dict(enumerate(classes)), device='cpu')
    args = (sizes, ddi, np.eye(8, dtype=np.float32), graphs, nfp, projection)
    # The identity mask is only a small synthetic equivalence fixture.
    torch.manual_seed(7)
    original = core.SafeDrugModel(*args, emb_dim=16, device=torch.device('cpu')).eval()
    core.MolecularGraphNeuralNetwork.pad = sparse_molecular_pad
    torch.manual_seed(7)
    adapted = core.SafeDrugModel(*args, emb_dim=16, device=torch.device('cpu')).eval()
    embedding_delta = delta(original.MPNN_emb, adapted.MPNN_emb)
    fixed = adapted.MPNN_emb.detach()
    del adapted.MPNN_emb
    adapted.register_buffer('MPNN_emb', fixed)
    sequence = [[[0, 1], [0], [0, 2]], [[2, 3], [1, 2], []]]
    a, al = original(sequence); b, bl = adapted(sequence)
    forward_delta = delta(a, b)
    (a.square().sum()+al).backward(); (b.square().sum()+bl).backward()
    gradients = []
    for (an, ap), (bn, bp) in zip(original.named_parameters(), adapted.named_parameters()):
        assert an == bn and (ap.grad is None) == (bp.grad is None)
        if ap.grad is not None:
            gradients.append(delta(ap.grad, bp.grad))
    assert gradients and 'MPNN_emb' in adapted.state_dict()
    # A checkpoint restores the fixed random molecule representation too.
    restored = core.SafeDrugModel(*args, emb_dim=16, device=torch.device('cpu')).eval()
    del restored.MPNN_emb
    restored.register_buffer('MPNN_emb', torch.zeros_like(fixed))
    restored.load_state_dict(adapted.state_dict())
    restored_delta = delta(adapted(sequence)[0], restored(sequence)[0])
    report = {'SafeDrug': {'dense_sparse_embedding_max_abs_delta': embedding_delta,
        'forward_max_abs_delta': forward_delta, 'registered_gradient_max_abs_delta': max(gradients),
        'registered_gradient_tensors': len(gradients), 'checkpoint_forward_max_abs_delta': restored_delta,
        'two_step_optimizer': 'pending'}}
    adapted.train()
    optimizer = torch.optim.Adam(adapted.parameters(), lr=.0005)
    target = np.zeros((1, 8), dtype=np.float32); target[0, [0, 2]] = 1
    case = {'visit': 1, 'source': [{'codes': x} for x in sequence]}
    for _ in range(2):
        optimizer.zero_grad(set_to_none=True)
        loss = loss_for(adapted, 'SafeDrug', [case], target, {'ddi': ddi}, torch.device('cpu'), .85, np.random.default_rng(42))
        assert torch.isfinite(loss); loss.backward(); optimizer.step()
    report['SafeDrug']['two_step_optimizer'] = 'passed'
    # Verify masking independently of the final code label contents.
    changed = copy.deepcopy(case); changed['source'][-1]['codes'][2] = [1, 4, 7]
    assert prefix(case) == prefix(changed) and sequence[-1][2] == []
    assert torch.backends.mps.is_available()
    cpu = armr().MyNet(16, sizes, 3, torch.tensor(ehr), torch.tensor(ddi)).eval()
    gpu = armr().MyNet(16, sizes, 3, torch.tensor(ehr, device='mps'), torch.tensor(ddi, device='mps')).to('mps').eval()
    gpu.load_state_dict(cpu.state_dict())
    ci = armr_input([case, changed], sizes, torch.device('cpu'))
    gi = [x.to('mps') for x in ci]
    co = cpu(*ci); go = gpu(*gi)
    forward_delta = delta(co, go.cpu())
    co.square().sum().backward(); go.square().sum().backward()
    gradients = []
    for (an, ap), (bn, bp) in zip(cpu.named_parameters(), gpu.named_parameters()):
        assert an == bn and (ap.grad is None) == (bp.grad is None)
        if ap.grad is not None: gradients.append(delta(ap.grad, bp.grad.cpu()))
    gpu.train(); optimizer = torch.optim.Adam(gpu.parameters(), lr=.0002)
    for _ in range(2):
        optimizer.zero_grad(set_to_none=True)
        loss = loss_for(gpu, 'ARMR', [case, changed], np.repeat(target, 2, axis=0), {'sizes': sizes}, torch.device('mps'), .85, np.random.default_rng(42))
        assert torch.isfinite(loss); loss.backward(); optimizer.step()
    report['ARMR'] = {'cpu_mps_forward_max_abs_delta': forward_delta,
        'cpu_mps_gradient_max_abs_delta': max(gradients), 'gradient_tensors': len(gradients),
        'two_step_optimizer': 'passed', 'current_label_masking': 'passed'}
    report.update(status='passed', clinical_data_loaded=False, scientific_performance_measured=False,
        torch_version=torch.__version__, tolerance={'rtol': 2e-4, 'atol': 2e-5},
        runtime_sha256=hashlib.sha256((HERE/'method_runtime.py').read_bytes()).hexdigest())
    (HERE/'results/training_runtime_probe.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)

if __name__ == '__main__': main()
