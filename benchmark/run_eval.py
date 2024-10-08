import os
import sys

if os.path.abspath('../..') not in sys.path:
    sys.path.append(os.path.abspath('../..'))
if os.path.abspath('..') not in sys.path:
    sys.path.append(os.path.abspath('..'))

from graphslim.config import get_args
from graphslim.dataset import *
from graphslim.evaluation import Evaluator, PropertyEvaluator

if __name__ == '__main__':
    args = get_args()
    data = get_dataset(args.dataset, args, load_path=args.load_path)
    if args.eval_whole:
        # evaluator = PropertyEvaluator(args)
        evaluator = Evaluator(args)
        if args.eval_mia:
            evaluator.MIA_evaluate(data, reduced=False, model_type=args.eval_model)
        else:
            evaluator.evaluate(data, reduced=False, model_type=args.eval_model)

    else:
        if args.attack is not None:
            data = attack(data, args)
            args.save_path = f'checkpoints'
        #evaluator = PropertyEvaluator(args)
        evaluator = Evaluator(args)
        if args.eval_mia:
            evaluator.MIA_evaluate(data, reduced=True, model_type=args.eval_model)
        else:
            evaluator.evaluate(data, reduced=True, model_type=args.eval_model)
        #evaluator.MIA_evaluate(data, reduced=True, model_type='GCN')
