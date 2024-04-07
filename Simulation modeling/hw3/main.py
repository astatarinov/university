from mesa import Agent, Model
import mesa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class PoliticalAgent(Agent):
    """An agent with fixed initial wealth."""

    def __init__(self, unique_id, model, x, u, extremist=False):
        # Pass the parameters to the parent class.
        super().__init__(unique_id, model)
        
        assert x >= -1 and x <= 1, 'x must be in [-1, 1]'
        
        self.x = x # opinion
        self.u = u # uncertainty lvl
        self.extremist = extremist

        self.new_x = self.x
        self.new_u = self.u

    def step(self):
        
        self.x = self.new_x
        self.u = self.new_u

    def __str__(self):

        return f"AgentId: {self.unique_id}, x: {self.x}, "


class PolicitalModel(Model):
    """A model with some number of agents."""

    def __init__(self, N, u=1.2, u_e=0.1, p_e=0.25, mu=0.5, delta=0, pairwise=True):
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
        self.pairwise = pairwise

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

    def calculate_pair_update(self, first: PoliticalAgent, second: PoliticalAgent):

        h_ij = min(first.x + first.u, second.x + second.u) - max(first.x - first.u, second.x - second.u)

        if h_ij > first.u:
            
            second.new_x = second.x + first.model.mu * (h_ij / first.u - 1) * (first.x - second.x)
            second.new_u = second.u + first.model.mu * (h_ij / first.u - 1) * (first.u - second.u)

            # adj to bounds 
            if second.new_x > 1:
                second.new_x = 1
            elif second.new_x < -1:
                second.new_x = -1

        if h_ij > second.u:
            first.new_x = first.x + first.model.mu * (h_ij / second.u - 1) * (second.x - first.x)
            first.new_u = first.u + first.model.mu * (h_ij / second.u - 1) * (second.u - first.u)
            
            # adj to bounds 
            if first.new_x > 1:
                first.new_x = 1
            elif first.new_x < -1:
                first.new_x = -1
        
    def step(self):
        """Advance the model by one step."""

        if self.pairwise:

            pairs = np.random.choice(
                self.schedule.agents, size=(int(self.num_agents / 2), 2),replace=False
            )
            # print([(i.unique_id, j.unique_id) for i, j in pairs])
            for a1, a2 in pairs:
                self.calculate_pair_update(a1, a2)
        
        self.schedule.step()
        self.datacollector.collect(self)