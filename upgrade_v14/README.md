# v0.14 — Real MedAgentBench FHIR runtime

[English results](RESULTS.en.md) · [中文结果](RESULTS.zh.md)

The official published Java application, configuration and public benchmark database are extracted from a pinned OCI image. An isolated native macOS ARM Java runtime runs the unchanged application on `127.0.0.1:18080`. No system-wide Java/Docker installation is made. Archive checksums and runtime differences are recorded in `results/runtime_provenance.json`.

```bash
python upgrade_v14/bootstrap_fhir.py
python upgrade_v14/launch_fhir.py  # keep the local server running
python upgrade_v14/probe_fhir_state.py
```

The integration probe performs actual HTTP create/read/update/delete requests and an invalid transaction. It cleans up only resources it created and checks original resource counts. This is engineering validation, **not an agent benchmark score**.

Sources: [official MedAgentBench](https://github.com/stanfordmlgroup/MedAgentBench), [Amazon Corretto archive/checksum documentation](https://docs.aws.amazon.com/corretto/latest/corretto-21-ug/downloads-list.html). The original wrapper's POST handling is recorded against official commit `99260117137b09f04837a8c18d18a1107efa55ae`; its grader evaluates submitted action history without actually sending POST. Future agent results must distinguish that original trace criterion from real persisted state.
