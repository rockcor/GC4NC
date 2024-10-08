#!/bin/bash
# Transferability
# Must obtain condensed graph of each methods by running performance.sh before running this script.
for method in random kcenter averaging vng gcondx geom sfgc doscond gcond msgc sgdd gcdm; do
  for dataset in cora ogbn-arxiv reddit; do
      python ../run_cross_arch.py -M $method -D $dataset
  done
done
