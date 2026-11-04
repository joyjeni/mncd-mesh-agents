| Scenario | n queries | Accuracy | Wilson 95% CI | CI width |
|---|---|---|---|---|
| S1_baseline_linear | 200 | 44.0% | [37.3%, 50.9%] | 13.6 pp |
| S2_mesh_p2p | 200 | 97.5% | [94.3%, 98.9%] | 4.6 pp |
| S3_mesh_2_failed | 200 | 97.0% | [93.6%, 98.6%] | 5.0 pp |
| S4_mesh_20pct_loss | 200 | 97.0% | [93.6%, 98.6%] | 5.0 pp |
| S5_karnataka_apmc_mesh | 15 | 93.3% | [70.2%, 98.8%] | 28.6 pp |
| S6_karnataka_apmc_baseline | 15 | 53.3% | [30.1%, 75.2%] | 45.1 pp |

Agents are simulated with a fixed competence parameter, so these accuracies measure the aggregation protocol under that model, not LLM quality. Scenarios with n = 15 cannot separate methods that differ by less than ~30 pp; a publishable comparison needs n >= 300 per arm.
