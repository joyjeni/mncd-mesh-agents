| Framework | Coordination | Context sharing | Fault tolerance | Replicated context | Distress signaling | Tool-selection benchmark | Reference |
|---|---|---|---|---|---|---|---|
| AutoGen [Wu+ 2023] | Centralized GroupChat | Shared message log | No | No | No | MATH 69.5% | arXiv:2308.08155 |
| MetaGPT [Hong+ 2024] | Assembly-line SOPs | Pub/sub (filtered) | Partial (role retry) | No | No | HumanEval 85.9% | ICLR 2024 / arXiv:2308.00352 |
| CAMEL [Li+ 2023] | Role-playing pair | Inception prompting | No | No | No | n/a (instruction) | NeurIPS 2023 |
| LangGraph [LangChain 2024] | Directed graph | State channels | Checkpoints | No (single state) | No | n/a (framework) | langchain.com/langgraph |
| ToolLLaMA [Qin+ 2023] | Single-agent DFSDT | n/a | n/a | n/a | n/a | ToolBench pass rate 66.7% | ICLR 2024 / arXiv:2307.16789 |
| **MNCD (this work)** | **P2P mesh + gossip** | **Topic pub/sub + gossip [Demers 1987]** | **Yes (97% acc. with 2/5 dead)** | **Yes (R=3)** | **Yes (τ=0.55)** | **ToolBench-syn 97.5%** | **this paper** |