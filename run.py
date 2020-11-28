#%%
import logging
import sys
import glob
import os
import argparse
import numpy as np
import pandas as pd
from AntClique import AntClique

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] - %(message)s', datefmt='%H:%M:%S')

def read_graph(graph_loc):
    """Reads dimacs styled graphs"""
    graph_adj = {}
    with open(graph_loc) as f:
        for i, line in enumerate(f):
            if i == 0:
                logging.info(f'Reading graph: {" ".join(line.strip().split()[1:])}')
            elif line.startswith('p'):
                _, _, vertices_num, edges_num = line.split()
                logging.info(f'Vertices: {vertices_num}, Edges: {edges_num}')
            elif line.startswith('e'):
                _, v1, v2 = line.split()
                if v1 == v2:
                    continue

                if v1 not in graph_adj:
                    graph_adj[v1] = {}
                if v2 not in graph_adj:
                    graph_adj[v2] = {}

                l = graph_adj[v1].get(v2, {})
                graph_adj[v1][v2] = l
                graph_adj[v2][v1] = l
            else:
                continue

    return graph_adj

def parse_input_args():
    root_parser = argparse.ArgumentParser(add_help=False)
    
    root_parser.add_argument(
        '--input-dir', dest='input_dir',
        help='Run the program on all files inside input-dir')
    
    root_parser.add_argument(
        '-i', '--input-path', dest='input_path',
        help='Input path for single file', default=os.path.join('input_graphs', 'anna.col'))

    root_parser.add_argument(
        '-o', '--output-prefix', dest='output_prefix',
        help='Output path for reports.', default='graph-results')

    parser = argparse.ArgumentParser(description='run')
    subparsers = parser.add_subparsers(dest='method', help='Available methods')
    subparsers.required = True
    
    # options for ant-clique
    parser_aco = subparsers.add_parser('aco', help='Use ant-clique algorithm', parents=[root_parser])
    parser_aco.add_argument(
        '--ants',
        dest='num_ants', help='num_ants', default=7)
    parser_aco.add_argument(
        '--taomin',
        dest='taomin', help='taomin', default=0.01)
    parser_aco.add_argument(
        '--taomax',
        dest='taomax', help='taomax', default=4)
    parser_aco.add_argument(
        '--alpha',
        dest='alpha', help='alpha', default=2)
    parser_aco.add_argument(
        '--rho',
        dest='rho', help='rho', default=.995)
    parser_aco.add_argument(
        '--max_cycles',
        dest='max_cycles', help='max_cycles', default=1000)
    parser_aco.add_argument(
        '--runs_per_graph',
        dest='runs_per_graph', help='runs_per_graph', default=3)
    

    # options for soumits algorithm

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_input_args()
    if args.input_dir:
        input_files = glob.glob(os.path.join(args.input_dir, '*'))
    else:
        input_files = [args.input_path]

    output_path = f'{args.output_prefix}.{args.method}'

    # do method specific processing here
    if args.method == 'aco':
        results = []
        obj = AntClique(args.num_ants, args.taomin, args.taomax, args.alpha, args.rho, args.max_cycles)

        for f in input_files:
            graph = read_graph(f)
            outputs = []
            for i in range(args.runs_per_graph):
                logging.info(f'Run {i}')
                outputs.append(obj.run(graph))
            
            sizes = [o[0] for o in outputs]
            times = [o[1] for o in outputs]
            cycles = [o[2] for o in outputs]

            out_json = {
                'filename': [f],
                'size->mean(stdev)': [f'{np.mean(sizes):.4f}({np.std(sizes):.4f})'],
                'time->mean(stdev)': [f'{np.mean(times):.4f}({np.std(times):.4f})'],
                'cycles->mean(stdev)': [f'{np.mean(cycles):.4f}({np.std(cycles):.4f})']
            }
            log_msg = "Final results-> " + ", ".join(f"{k}: {v}" for k, v in out_json.items())
            
            results.append(pd.DataFrame(out_json))
            logging.info(log_msg)
            print('\n')


        combined_results = pd.concat(results)
        combined_results.to_csv(output_path, index=False)





    