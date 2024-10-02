#!/bin/bash
echo '====start running===='
python benchmark/run_eval.py -M gcdm --save_path ./checkpoints --load_path ./data  --emia
