"""Medication-label-free structured features for conventional controls."""
import numpy as np
from scipy import sparse
from sklearn.preprocessing import normalize
from method_runtime import prefix

def features(cases, sizes):
    d, p, m = sizes
    widths = [d, p, d, p, m, m]
    coordinates = [[] for _ in widths]
    values = [[] for _ in widths]
    for row, case in enumerate(cases):
        history = prefix(case)
        prior = history[:-1]
        blocks = [set(history[-1][0]), set(history[-1][1]),
                  {x for v in prior for x in v[0]}, {x for v in prior for x in v[1]},
                  set(prior[-1][2]) if prior else set()]
        for block, ids in enumerate(blocks):
            for col in sorted(ids):
                coordinates[block].append((row, col)); values[block].append(1.)
        counts = {}
        for visit in prior:
            for col in set(visit[2]): counts[col] = counts.get(col, 0) + 1
        for col, count in sorted(counts.items()):
            coordinates[5].append((row, col)); values[5].append(count/len(prior))
    blocks = []
    for width, ij, data in zip(widths, coordinates, values):
        rows, cols = zip(*ij) if ij else ([], [])
        matrix = sparse.csr_matrix((np.asarray(data, dtype=np.float32), (rows, cols)), shape=(len(cases), width))
        blocks.append(normalize(matrix))
    return normalize(sparse.hstack(blocks, format='csr')).astype(np.float32)

def neighbor_probabilities(query, train, query_cases, train_cases, targets, ks=(5,20,50)):
    train_people = np.array([x['subject_hash'] for x in train_cases])
    result = {k: np.zeros((len(query_cases), targets.shape[1]), dtype=np.float32) for k in ks}
    for start in range(0, query.shape[0], 128):
        scores = (query[start:start+128]@train.T).toarray()
        for local, case in enumerate(query_cases[start:start+128]):
            scores[local, train_people == case['subject_hash']] = -np.inf
        indices = np.argsort(-scores, axis=1, kind='stable')[:, :max(ks)]
        assert np.isfinite(np.take_along_axis(scores, indices, axis=1)).all()
        for k in ks: result[k][start:start+len(indices)] = targets[indices[:, :k]].mean(1)
    return result
