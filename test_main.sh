#!/bin/bash
echo '====start running===='
python benchmark/train_all.py -M gcdm --save_path ./checkpoints --load_path ./data  
