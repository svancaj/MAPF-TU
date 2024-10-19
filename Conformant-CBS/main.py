import sys
import os
import json
path = os.getcwd().split(os.path.sep)
path = os.path.sep.join(path[:-1])
sys.path.append(path)
proj_path = os.path.abspath(os.getcwd())
proj_path = proj_path.split('Conformant-CBS')
proj_path = os.path.join(proj_path[0], 'Conformant-CBS', 'pathfinding', 'testing')
previous_settings_file_path = os.path.join(proj_path, 'previous_settings.json')
import pathfinding
from pathfinding.testing.experiments import *


if __name__ == '__main__':
    
    #run_experiments(u=(1,2,3,4,5), agents=(2,4,6,8,10,12,14,16,18,20), sense_prob=(0,), edge_dist=('uni',),
    #                comm_mode=(False,), mbc=(False,), pc=(True,), bp=(True,), 
    #                maps=('kiva','empty08','empty16','empty24','random08','random16','random24'), reps=5, time_limit=1)

    run_experiments(u=(1,3,5), agents=(2,4,6,8,10,12,14,16,18,20), sense_prob=(0,), edge_dist=('uni',),
                    comm_mode=(False,), mbc=(False,), pc=(True,), bp=(True,), 
                    maps=('empty08','empty16','empty24','random08','random16','random24'), reps=5, time_limit=300)
