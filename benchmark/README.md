[//]: # (# Preparation)

# GC4NC: A Benchmark Framework for Graph Condensation on Node Classification with New Insights

Graph condensation (GC) is an emerging technique designed to learn a significantly smaller graph that retains the essential information of the original graph. This condensed graph has shown promise in accelerating graph neural networks while preserving performance comparable to those achieved with the original, larger graphs. 
Additionally, this technique facilitates downstream applications like neural architecture search and deepens our understanding of redundancies in large graphs. 
Despite the rapid development of GC methods, particularly for node classification, a unified evaluation framework is still lacking to systematically compare different GC methods or clarify key design choices for improving their effectiveness. 
To bridge these gaps, we introduce \textbf{GC4NC}, a comprehensive framework for evaluating diverse GC methods on node classification across multiple dimensions including performance, efficiency,  privacy preservation, 
denoising effects, NAS effectiveness, and transferability.  
Our systematic evaluation offers novel insights into how condensed graphs behave and the critical design choices that drive their success. These findings pave the way for future advancements in GC methods, enhancing both performance and expanding their real-world applications.


## Requirements

Please see `requirements.txt`.

<!--## Download Datasets

For cora, citeseer, flickr, reddit and yelp, the pyg or dgl will directly download them.
For arxiv, we use the datasets provided by [GraphSAINT](https://github.com/GraphSAINT/GraphSAINT). Our code will also automatically download it.-->


[//]: # (# Abstract)

[//]: # ()

[//]: # (Graph reduction for all graph algorithms especially for graph neural networks &#40;GNNs&#41;.)

[//]: # (This package aims to reduce the large, original graph into a small, synthetic and highly-informative graph.)

[//]: # ()

[//]: # (# Features)

[//]: # (* Covering 3 mainstream reduction strategies: Sparsificaiton, Coarsening and Condensation)

[//]: # (* Unified test tools for easily producing benchmarks)

## Benchmark Reproduction

All the scripts are in `benchmark` folder.

For Table 1 7 8, use `sh performacne.sh`.

For Figure 3, use `sh scalability.sh`.

For Figure 4, use `sh data_initialization.sh`.

For Figure 5 9, use `sh transferability.sh`.

For Table 2, use `sh nas.sh`.

For Table 3 10 11, use `sh graph_property_preservation.sh`.

For Table 4 12, use `sh robustness.sh`.
