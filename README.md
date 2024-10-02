[//]: # (# Preparation)

# GC4NC: A Benchmark Framework for Graph Condensation on Node Classification with New Insights

Graph condensation (GC) is an emerging technique designed to learn a significantly smaller graph that retains the essential information of the original graph. This condensed graph has shown promise in accelerating graph neural networks while preserving performance comparable to those achieved with the original, larger graphs. 
Additionally, this technique facilitates downstream applications like neural architecture search and deepens our understanding of redundancies in large graphs. 
Despite the rapid development of GC methods, particularly for node classification, a unified evaluation framework is still lacking to systematically compare different GC methods or clarify key design choices for improving their effectiveness. 
To bridge these gaps, we introduce **GC4NC**, a comprehensive framework for evaluating diverse GC methods on node classification across multiple dimensions including performance, efficiency,  privacy preservation, 
denoising effects, NAS effectiveness, and transferability.  
Our systematic evaluation offers novel insights into how condensed graphs behave and the critical design choices that drive their success. These findings pave the way for future advancements in GC methods, enhancing both performance and expanding their real-world applications.


## Requirements

Please use `pip install -r benchmark/requirements.txt`.

## Download Datasets

For cora, citeseer, flickr, reddit and yelp, the pyg or dgl will directly download them.
For arxiv, we use the datasets provided by [GraphSAINT](https://github.com/GraphSAINT/GraphSAINT). Our code will also automatically download it.
You can specify the load and save path by `python train_all.py --save_path xxx --load_path xxx`

## Benchmark Reproduction

Test environments by `sh test_main.sh` and `sh test_eval.sh`.

All the scripts are in `benchmark/scripts` folder. Please first generate the condensed graph by running `sh benchmark/scripts/performacne.sh`.

For Table 1, use `sh benchmark/scripts/performacne.sh`.

For Table 2, use `sh benchmark/scripts/privacy.sh`.

For Table 3, use `sh benchmark/scripts/robustness.sh`.

For Table 4, use `sh benchmark/scripts/nas.sh`.

For Table 5, use `sh benchmark/scripts/graph_property_preservation.sh`.

For Figure 3, use `sh benchmark/scripts/scalability.sh`.

For Figure 4, use `sh benchmark/scripts/transferability.sh`.

For Figure 5, use `sh benchmark/scripts/data_initialization.sh`.




