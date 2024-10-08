#!/bin/bash
# Data Initialization
for method in gcondx geom doscond gcond msgc; do
  for dataset in cora ogbn-arxiv reddit; do
    for init in random averaging kcenter herding; do
        python ../train_all.py -M $method -D $dataset --init $init
    done
  done
done
