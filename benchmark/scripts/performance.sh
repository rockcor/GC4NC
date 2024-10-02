# Performance
# For geom, we obtain its performance by the source code of the authors but condense graph by our package for other experiments except performance.
# For sfgc, we obtain its performance by the source code of the authors.
# If you want to run gdem, please first run their raw repo to generate spectral decompositon and put them in corresponding data folder.
for method in random herding kcenter averaging vng gcondx geom sfgc gcsntk doscond gcond msgc sgdd gcdm; do
  for dataset in cora citeseer pubmed ogbn-arxiv flickr reddit yelp; do
    case $dataset in
      cora|citeseer)
        for r in 0.1 0.25 0.5; do
          python ../train_all.py -M $method -D $dataset -R $r
        done
        ;;
      pubmed)
        for r in 0.01 0.1 0.5; do
          python ../train_all.py -M $method -D $dataset -R $r
        done
        ;;
      ogbn-arxiv)
        for r in 0.001 0.005 0.01; do
          python ../train_all.py -M $method -D $dataset -R $r
        done
        ;;
      flickr)
        for r in 0.001 0.005 0.01; do
          python ../train_all.py -M $method -D $dataset -R $r
        done
        ;;
      reddit|yelp)
        for r in 0.0005 0.001 0.002; do
          python ../train_all.py -M $method -D $dataset -R $r
        done
        ;;
    esac
  done
done

# Whole results
for dataset in cora citeseer ogbn-arxiv flickr reddit yelp; do
  python ../run_eval.py -D $dataset -W
done
