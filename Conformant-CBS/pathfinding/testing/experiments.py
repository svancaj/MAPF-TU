"""
File for running some experiments.
"""
import os.path
import sys
from pathfinding.planners.operator_decomposition_a_star import *
from pathfinding.simulator import *
from shutil import copyfile

proj_path = os.path.abspath(os.getcwd())
proj_path = proj_path.split('Conformant-CBS')
proj_path = os.path.join(proj_path[0], 'Conformant-CBS')
maps_path = os.path.join(proj_path, 'maps')

MAP_FILES = {
    'kiva': f'{os.path.join(maps_path, "kiva.map")}',
    'empty08': f'{os.path.join(maps_path, "empty08.map")}',
    'empty16': f'{os.path.join(maps_path, "empty16.map")}',
    'empty24': f'{os.path.join(maps_path, "empty24.map")}',
    'random08': f'{os.path.join(maps_path, "random08.map")}',
    'random16': f'{os.path.join(maps_path, "random16.map")}',
    'random24': f'{os.path.join(maps_path, "random24.map")}',
}

map_seed = 96372106
initial_agent_seed = 10737296


class Experiments:

    def __init__(self):
        self.output_folder = os.path.join(proj_path, 'experiments', 'Online Runs')
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        self.picat_folder = os.path.join(proj_path, 'picat_instances')
        if not os.path.exists(self.picat_folder):
            os.makedirs(self.picat_folder)

        self.num_of_reps = 1
        self.min_best_case = False
        self.agents_num = 2
        self.uncertainty = 0
        self.time_limit = 10
        self.reps = 10
        self.file_prefix = 'default - '

    def run_online_experiments(self, agent_num, sense, commy, dist, use_pc, use_bp, maps):

        objective = 'min best case' if self.min_best_case else 'min worst case'
        self.file_prefix = \
            f'{agent_num} agents - {self.uncertainty} uncertainty - {sense} sensing - comm {commy} -' \
            f' {objective} - distribution - {dist} - pc {use_pc} - bp {use_bp}'
        for map_type in maps:
            results_file = self.file_prefix + f' - {map_type}_results.csv'

            print(
                f"- STARTED ONLINE {map_type} | {self.agents_num} AGENTS | UNCERTAINTY: {self.uncertainty} |"
                f" SENSE: {sense} | COMM: {commy} | DISTRIBUTION: {dist} | MIN BEST TIME: {self.min_best_case} |"
                f" PC: {use_pc} | BP: {use_bp}")

            random.seed(map_seed)

            map_file = MAP_FILES[map_type]
            tu_problem = TimeUncertaintyProblem(map_file)
            tu_problem.generate_problem_instance(self.uncertainty)

            self.run_and_log_online_experiments(tu_problem, map_type, results_file, sense, commy, dist, use_pc, use_bp)

    def run_and_log_online_experiments(self, tu_problem, map_type, results_file, sensing_prob, communication, dist,
                                       use_pc, use_bp, to_print=True):
        final_folder = os.path.join(self.output_folder, map_type, f'{self.agents_num} agents')
        if not os.path.exists(final_folder):
            os.makedirs(final_folder)
        final_results_path = os.path.join(final_folder, results_file)
        temp_path = os.path.join(self.output_folder, 'IN PROGRESS - ' + results_file)
        with open(temp_path, 'w') as temp_file:
            temp_file.write('Experiment Number,'
                            'Map Seed,'
                            'Number of Agents,'
                            'Agents Seed,'
                            'Uncertainty,'
                            'PC,'
                            'Bypass,'
                            'Timeout,'
                            'initial time,'
                            'octu Time,'
                            'initial Min Cost,'
                            'initial Max Cost,'
                            'initial uncertainty,'
                            'initial true cost,'
                            'nodes expanded initially,'
                            'octu Min Cost,'
                            'octu Max Cost,'
                            'octu uncertainty,'
                            'final true cost,'
                            'Sensing Probability,'
                            'Distribution,'
                            'Objective,'
                            'Communication,'
                            'Min SIC,'
                            'Max SIC,'
                            'True SIC\n'
                            )

        success = 0
        random.seed(initial_agent_seed)
        sol_folder = os.path.join(proj_path, 'solutions')
        for i in range(self.reps):
            agent_seed = initial_agent_seed + i
            random.seed(agent_seed)
            if to_print:
                print(f'Started run #{i + 1}, agent seed: {agent_seed}, number of agents: {self.agents_num}')
            tu_problem.generate_agents(self.agents_num)
            tu_problem.fill_heuristic_table(self.min_best_case)
            tu_problem.print_picat_instance(os.path.join(self.picat_folder,
                    map_type + "_agents-" + str(self.agents_num) + "_unc-" + str(self.uncertainty) + "_" + str(i) + ".pi"))
            sim = MAPFSimulator(tu_problem, sensing_prob, edge_dist=dist)

            try:
                loaded_sol = TimeUncertaintySolution.load(self.agents_num, self.uncertainty, map_type, agent_seed,
                                                          map_seed, self.min_best_case, use_pc, use_bp, sol_folder)
                if loaded_sol and loaded_sol.paths == {}:  # It was a timed out solution
                    raise OutOfTimeError
                start_time = time.time()
                online_sol = sim.begin_execution(self.min_best_case, use_pc, use_bp, time_limit=self.time_limit,
                                                 communication=communication, initial_sol=loaded_sol)
                octu_time = time.time() - start_time
                if not loaded_sol:
                    octu_time -= sim.online_planner.initial_plan.time_to_solve

                success += 1
                online_sol.create_movement_tuples()

                octu_cost = online_sol.cost
                octu_tu = octu_cost[1] - octu_cost[0]
                final_true_cost = sim.calc_solution_true_cost(online_sol)

                init_sol = sim.online_planner.initial_plan
                init_time = init_sol.time_to_solve
                init_cost = init_sol.cost
                init_tu = init_cost[1] - init_cost[0]
                init_true_cost = sim.calc_solution_true_cost(init_sol)
                min_sic = init_sol.sic[0]
                max_sic = init_sol.sic[1]
                random.seed(agent_seed)
                tu_problem.generate_agents(self.agents_num)
                sim.online_planner.tu_problem = tu_problem
                root_sol = sim.online_planner.offline_planner.create_root().sol
                true_sic = sim.calc_solution_true_cost(root_sol)

                if not loaded_sol:
                    init_sol.save(self.agents_num, self.uncertainty, map_type, agent_seed, map_seed, self.min_best_case,
                                  use_pc, use_bp, sol_folder)

            except OutOfTimeError:  # Simulator threw a timeout
                if loaded_sol:
                    init_sol = loaded_sol
                    init_time = loaded_sol.time_to_solve
                else:
                    init_sol = sim.online_planner.initial_plan
                    init_time = sim.online_planner.initial_plan.time_to_solve
                    init_sol.save(self.agents_num, self.uncertainty, map_type, agent_seed, map_seed, self.min_best_case,
                                   use_pc, use_bp, sol_folder)
                octu_cost = -1, -1
                init_cost = -1, -1
                octu_time = -1
                init_tu = -1
                octu_tu = -1
                init_true_cost = -1
                final_true_cost = -1
                min_sic = -1
                max_sic = -1
                true_sic = -1

            with open(temp_path, 'a') as temp_map_result_file:
                objective = 'Min Best Case' if self.min_best_case else 'Min Worst Case'
                results = f'{i + 1},' \
                    f'{map_seed},' \
                    f'{self.agents_num},' \
                    f'{agent_seed},' \
                    f'{self.uncertainty},' \
                    f'{use_pc},' \
                    f'{use_bp},' \
                    f'{self.time_limit},' \
                    f'{init_time},' \
                    f'{octu_time},' \
                    f'{init_cost[0]},' \
                    f'{init_cost[1]},' \
                    f'{init_tu},' \
                    f'{init_true_cost},' \
                    f'{init_sol.nodes_generated},' \
                    f'{octu_cost[0]},' \
                    f'{octu_cost[1]},' \
                    f'{octu_tu},' \
                    f'{final_true_cost},' \
                    f'{sensing_prob},' \
                    f'{dist},' \
                    f'{objective},' \
                    f'{communication},' \
                    f'{min_sic},' \
                    f'{max_sic},' \
                    f'{true_sic}\n'
                temp_map_result_file.write(results)

        copyfile(temp_path, final_results_path)
        os.remove(temp_path)

    def run_online_combinations(self, agent_num, tu, sense, reps, edge_dist, comm_mode, mbc, pc, bp, time_lim, maps):

        sense /= 100
        for dist in edge_dist:
            for comm in comm_mode:
                for goal in mbc:
                    for use_pc in pc:
                        for use_bp in bp:
                            self.min_best_case = goal
                            self.uncertainty = tu
                            self.agents_num = agent_num
                            self.time_limit = time_lim
                            self.reps = reps
                            self.run_online_experiments(agent_num=agent_num, sense=sense, commy=comm, dist=dist,
                                                        use_pc=use_pc, use_bp=use_bp, maps=maps)


def run_experiments(u=(0, 1, 2, 4), agents=(8, ), sense_prob=(0, 100), edge_dist=('min', 'max', 'uni', ), reps=100,
                    comm_mode=(True, False), mbc=(True, False), pc=(True, ), bp=(False, ), maps=('small_blank_map', ), time_limit=100):

    exp = Experiments()

    for uncertainty in u:
        for number_of_agents in agents:
            for sp in sense_prob:
                exp.run_online_combinations(number_of_agents, uncertainty, sp, reps=reps, edge_dist=edge_dist,
                                            comm_mode=comm_mode, mbc=mbc, maps=maps, pc=pc, bp=bp, time_lim=time_limit)

    print("Finished Experiments")

#run_experiments()
