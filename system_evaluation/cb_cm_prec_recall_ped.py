# Copy of cb_cm_single_ped.py with simple controller instead of tulip controller.
import sys
sys.path.append("..")
import numpy as np
import os
import pdb
from pathlib import Path
from experiment_file import *
from collections import OrderedDict as od
from print_utils import print_cm, print_param_cm
# from ..custom_env import cm_dir, is_set_to_mini
try: 
    from system_evaluation.simple_markov_chain import construct_mc as cmp
    from system_evaluation.simple_markov_chain.setup_mc import call_MC, call_MC_param
except:
    from simple_markov_chain import construct_mc as cmp
    from simple_markov_chain.setup_mc import call_MC, call_MC_param

import matplotlib as plt
# from figure_plot import probability_plot
import time
import json
import sys
from formula import *
sys.setrecursionlimit(10000)

def get_confusion_matrix():
    C, param_C = cmp.confusion_matrix(cm_fn)
    return C, param_C

def init(MAX_V=6):
    Ncar = int(MAX_V*(MAX_V+1)/2 + 4)
    return Ncar

def save_results(INIT_V, P, precision_recall, result_type, true_env):
    results_folder = f"{cm_dir}/probability_results"
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    fname_v = f"{results_folder}/{result_type}_cm_ped_vmax_"+str(MAX_V)+"_initv.json"
    fname_p = f"{results_folder}/{result_type}_cm_ped_vmax_"+str(MAX_V)+"_prob.json"
    fname_pr = f"{results_folder}/{result_type}_cm_ped_vmax_"+str(MAX_V)+"_pr_pairs.json"

    with open(fname_v, 'w') as f:
        json.dump(INIT_V, f)
    with open(fname_p, 'w') as f:
        json.dump(P, f)
    with open(fname_pr, 'w') as f:
        json.dump(precision_recall, f)
        
def initialize(MAX_V, Ncar, maxv_init=None):
    '''
    Inputs::
    MAX_V: Maximum speed that the car can travel at
    Ncar: Maximum discrete states for the car
    vmax_init: Max initial speed of the car (specified if different from MAX_V)

    Outputs::
    Vlow: Minimum car speed (0)
    Vhigh: Maximum car speed (MAX_V)
    xped: Pedestrian position
    '''

    Vlow = 0
    Vhigh = MAX_V
    
    if maxv_init:
        xmax_stop = maxv_init*(maxv_init+1)/2 + 1 # earliest stopping point for car 
    else:
        xmax_stop = Vhigh*(Vhigh+1)/2 + 1 # earliest stopping point for car 
    
    xped, xcar_stop = set_crosswalk_cell(Ncar, xmax_stop)
    formula = formula_ev_good(xcar_stop, Vhigh, Vlow)
    return Vlow, Vhigh, xped, formula

def simulate(MAX_V=6):
    Ncar = init(MAX_V=MAX_V)
    INIT_V, P, prec_recall = compute_probabilities(Ncar, MAX_V,true_env_type="ped")
    save_results(INIT_V, P, prec_recall, "prec_recall", "ped")

def compute_probabilities(Ncar, MAX_V, true_env_type="ped"):
    Vlow, Vhigh, xped, formula = initialize(MAX_V, Ncar)
    prec_recall = [(0.4, 0.9), (0.7, 0.8), (0.82, 0.6), (0.9, 0.4), (0.95, 0.2)]
    INIT_V = dict()
    P = dict()
    print("===========================================================")
    print("Specification: ")
    print(formula)
    
    for k in range(len(prec_recall)):
        INIT_V[k] = []
        P[k] = []
        prec, recall = prec_recall[k]

        for vcar in range(1, MAX_V+1):  # Initial speed at starting point
            state_f = lambda x,v: (Vhigh-Vlow+1)*(x-1) + v
            start_state = "S"+str(state_f(1,vcar))
            print(start_state)
            S, state_to_S = cmp.system_states_example_ped(Ncar, Vlow, Vhigh)
            
            true_env = str(1) # Sidewalk 3
            O = {"ped", "obs", "empty"}
            class_dict = {0: {'ped'}, 1: {'obs'}, 2: {'empty'}}
            state_info = dict()
            state_info["start"] = start_state

            C = cmp.construct_CM_from_pr(prec, recall)
            
            M = call_MC(S, O, state_to_S, C, class_dict, true_env, true_env_type, state_info, Ncar, xped, Vhigh)
            result = M.prob_TL(formula)
            P[k].append(result[start_state])

            print('Probability of eventually reaching good state for initial speed, {}, and max speed, {} is p = {}:'.format(vcar, MAX_V, result[start_state]))
            # Store results:
            INIT_V[k].append(vcar)
            
    return INIT_V, P, prec_recall

if __name__=="__main__":
    MAX_V = 6
    simulate(MAX_V=MAX_V)