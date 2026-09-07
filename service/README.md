# MNCD HTTP microservice

> ACRS Objective 3. Default consensus is **score-sum**. Live data.gov.in only;
> no invented prices. Proposal-stage: no accuracy target.

```bash
python service/app.py 43133
curl -X POST http://127.0.0.1:43133/mesh -H 'Content-Type: application/json' \
  -d '{"ranks":[{"agent":"A0","ranking":[["tool",0.8]]}],"consensus":"score_sum"}'
```

Default consensus is **score-sum** (`consensus_pick`). Pass `"consensus":"borda"`
for `consensus_pick_borda`.
