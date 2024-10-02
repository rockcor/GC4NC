#!/bin/bash
# Privacy Preservation
methods=("gcond" "gcondx" "doscond" "sgdd" "gdem" "geom" "sfgc")

for method in "${methods[@]}"; do
  for dataset in cora citeseer ogbn-arxiv; do
    python ../run_eval.py -D $dataset -M $method -W --emia
  done

  for dataset in cora citeseer ogbn-arxiv; do
    python ../run_eval.py -D $dataset -M $method --emia
  done
done
