# RxRSIAgent: current architecture and boundaries

The current selected pipeline is shown below. It uses three LLM calls and a supervised numeric calibrator. The text-memory channel has no accepted update. Product/source checks do not establish full clinical applicability. Historical eighteen-domain interfaces remain in the clinical registry and have not all become validated tools.

```mermaid
flowchart TD
 A[Public case and options] --> B[Call 1: facts, entities, intent]
 B --> C[Drug label tool: identity, route, sections]
 C --> D[Call 2: compare options and cite evidence]
 D --> E[Executable source-span and arithmetic checks]
 E --> F[Call 3: decision and uncertainty]
 F --> G{Eligible short known names and margin >= 0.2?}
 G -- Yes --> H[Supervised calibrated choice]
 G -- No --> I[Keep source-agent choice]
 J[625 training cases] --> K[Scoped text proposals or numeric training]
 K --> L[190 proposal then197 guard]
 L --> M[Freeze before test]
 M --> G
 H --> N[Expose original draft separately; no inherited explanation]
```

[Full results and limits](CURRENT_RESULTS.en.md)

Current entry:`rxrsiagent/selected_agent.py`. Historical interface details:[v0.34 archive](versions/v0.34_source/RXRSI_DESIGN.en.md).
