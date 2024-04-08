from mesa import Agent, Model
import mesa
import numpy as np
from itertools import combinations
from collections import deque

class PoliticalAgent(Agent):
    """An agent with fixed initial wealth."""

    def __init__(self, unique_id, model, x, u, extremist=False):
        # Pass the parameters to the parent class.
        super().__init__(unique_id, model)
        
        assert x >= -1 and x <= 1, 'x must be in [-1, 1]'
        
        self.x = x # opinion
        self.u = u # uncertainty lvl
        self.extremist = extremist

        self.x_change = 0
        self.u_change = 0

    def step(self):

        # changes are calculated by the model for all agents
        self.x += self.x_change
        self.u += self.u_change

        # adj to bounds 
        if self.x > 1:
            self.x = 1
        elif self.x < -1:
            self.x = -1

        self.x_change = 0
        self.u_change = 0


    def __str__(self):

        return f"AgentId: {self.unique_id}, x: {self.x}, "


class PolicitalModel(Model):
    """An absolutely theoretical model"""

    def __init__(self, N, u=1.2, u_e=0.1, p_e=0.25, mu=0.5, delta=0, pairwise=True,
                  max_iter = 1000, change_threshold=1e-07, conv_check_periods_num=50):
        super().__init__()

        assert u >= 0 and u <= 2, 'u x must be in [0, 2]'
        assert u_e >= 0 and u_e <= 2, 'u_e x must be in [0, 2]'
        assert p_e >= 0 and p_e <= 1, 'p_e x must be in [0, 1]'
        assert N % 2 == 0, 'N has to be even'
        
        
        self.num_agents = N
        self.schedule = mesa.time.RandomActivation(self)
        self.u = u
        self.u_e = u_e # extremists uncertainty lvl
        self.p_e = p_e # extr share
        self.mu = mu
        self.delta = delta
        self.pairwise = pairwise # random pairs on each step if True, 1 vs all otherwise

        # if "everyone with everyone", effect of each contact is multiplied on mu /(N-1) 
        # (discussed at the seminar)
        self.mu_fact_coef = self.mu if self.pairwise else self.mu / (self.num_agents - 1)

        # Creating agents 
        x_array = np.random.uniform(-1, 1, self.num_agents)

        # suppose p_pos >= p_neg since we don't dif. extremist type
        # (discussed at the seminar)
        p_pos_div_p_neg = (1 + self.delta) / (1 - self.delta)                                                    
        p_neg = self.p_e / (1 + p_pos_div_p_neg)
        p_pos = self.p_e - p_neg

        self.P_NEG_BOUND = np.quantile(x_array, p_neg)
        self.P_POS_BOUND = np.quantile(x_array, 1 - p_pos)

        # Create agents
        for i, x in enumerate(x_array):
            if x <= self.P_NEG_BOUND:
                a = PoliticalAgent(i, self, x, self.u_e, extremist=True)
            elif x >= self.P_POS_BOUND:
                a = PoliticalAgent(i, self, x, self.u_e, extremist=True)
            else:
                a = PoliticalAgent(i, self, x, self.u)
            # Add the agent to the scheduler
            self.schedule.add(a)

        self.datacollector = mesa.datacollection.DataCollector(agent_reporters={"X": "x"})
        self.datacollector.collect(self)

        self.step_sum_change = 0
        self.model_datacollector = mesa.datacollection.DataCollector(model_reporters={"Step_sum_change": "step_sum_change"})

        # stopping parameters 
        self.max_iter = max_iter
        self.change_threshold = change_threshold
        self.conv_check_periods_num = conv_check_periods_num
        self.check_change_list = deque(maxlen=self.conv_check_periods_num)

    def calculate_pair_update(self, first: PoliticalAgent, second: PoliticalAgent):

        h_ij = min(first.x + first.u, second.x + second.u) - max(first.x - first.u, second.x - second.u)

        if h_ij > first.u:
            
            second.x_change += self.mu_fact_coef * (h_ij / first.u - 1) * (first.x - second.x)
            second.u_change += self.mu_fact_coef * (h_ij / first.u - 1) * (first.u - second.u)

        if h_ij > second.u:

            first.x_change += self.mu_fact_coef * (h_ij / second.u - 1) * (second.x - first.x)
            first.u_change += self.mu_fact_coef * (h_ij / second.u - 1) * (second.u - first.u)
            
        
    def step(self):
        """Advance the model by one step."""

        if self.pairwise:
            # generates random pairs of agents to affect each other
            pairs = np.random.choice(
                self.schedule.agents, size=(int(self.num_agents / 2), 2),replace=False
            )

        else: 
            # generates all possible unique pairs between agents
            pairs = combinations(self.schedule.agents, 2)

        for a1, a2 in pairs:
            self.calculate_pair_update(a1, a2)  

        self.step_sum_change = np.sum([abs(i.x_change) for i in self.schedule.agents])

        self.check_change_list.append(self.step_sum_change)

        self.model_datacollector.collect(self) # collect changes for statistics 

        self.schedule.step() # apply changes 

        self.datacollector.collect(self) # collect agents data


    def run(self):
        """Run until max_iter or stopping condition is achieved"""

        for _ in range(self.max_iter):

            self.step()

            if len(self.check_change_list)==self.conv_check_periods_num and \
            max(self.check_change_list) < self.change_threshold:
                break
