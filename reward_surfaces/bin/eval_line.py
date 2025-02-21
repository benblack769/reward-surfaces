import argparse
import json
import os
import torch
from reward_surfaces.utils.surface_utils import readz
from pathlib import PurePath
from reward_surfaces.algorithms import evaluate
from reward_surfaces.agents import make_agent
import numpy as np
from reward_surfaces.utils.surface_utils import filter_normalize
torch.set_num_threads(1)


bigint = 1000000000000


def main():
    parser = argparse.ArgumentParser(description='run a particular evaluation job')
    parser.add_argument('params', type=str)
    parser.add_argument('dir', type=str, help="direction to search for threshold")
    parser.add_argument('outputfile', type=str)
    parser.add_argument('--num-steps', type=int, default=bigint)
    parser.add_argument('--num-episodes', type=int, default=bigint)
    parser.add_argument('--device', type=str, default="cpu")
    parser.add_argument('--length', type=int, default=5)
    parser.add_argument('--max-magnitude', type=float, default=0.1)

    args = parser.parse_args()

    info = json.load(open(PurePath(args.outputfile).parent.parent / "info.json"))
    checkpoint = os.path.basename(args.outputfile)

    agent, steps = make_agent(info['agent_name'], info['env'], PurePath(args.params).parent.parent, info['hyperparameters'], device=args.device)

    params = [v.cpu().detach().numpy() for v in torch.load(args.params, map_location=torch.device('cpu')).values()]
    if info['random_dir_seed'] is not None:
        seed = info['random_dir_seed']
        np.random.seed(seed+hash(args.outputfile) % (1 << 30))
        direction = [filter_normalize(p) for p in params]
    else:
        direction = readz(args.dir)

    if info['scale_dir']:
        dir_sum = sum(np.sum(x) for x in direction)
        if dir_sum != 0:
            direction = [d/dir_sum for d in direction]

    # High resolution in first segment
    for i in range(1, 10):
        mm = args.max_magnitude
        weights = [p + d*i*mm / (10*args.length) for p, d in zip(params, direction)]
        agent.set_weights(weights)
        evaluator = agent.evaluator()
        eval_results = evaluate(evaluator, args.num_episodes, args.num_steps)
        eval_results['checkpoint'] = checkpoint
        out_fname = f"{args.outputfile},0.{i}.json"
        eval_results["offset"] = i*mm/(10*args.length)

        with open(out_fname, 'w') as file:
            file.write(json.dumps(eval_results))

    for i in range(args.length):
        mm = args.max_magnitude
        weights = [p + d*i*mm/args.length for p, d in zip(params, direction)]
        agent.set_weights(weights)
        evaluator = agent.evaluator()
        eval_results = evaluate(evaluator, args.num_episodes, args.num_steps)
        eval_results['checkpoint'] = checkpoint
        out_fname = f"{args.outputfile},{i}.json"
        eval_results["offset"] = i*mm/args.length

        with open(out_fname, 'w') as file:
            file.write(json.dumps(eval_results))


if __name__ == "__main__":
    main()
