import random
import simpy
import numpy as np
import pandas as pd

class Bank:
    def __init__(self, env, num_windows=1, type1_prob=0.75, max_time=5000, print_logs=True):

        self.num_windows = num_windows
        self.service_types = {
            0: {'time': 9, 'prob': type1_prob, 'bonus': 0.3, 'profit': 3, 'loss_cost': 1.1},
            1: {'time': 15, 'prob': 1 - type1_prob, 'bonus': 0.5, 'profit': 6, 'loss_cost': 2.5}
        }
        self.interval = 10
        self.max_time = max_time
        self.env = env
        # self.queue = simpy.Store(self.env)
        self.counter = simpy.Resource(self.env, capacity=self.num_windows)
        self.customer_visits_data = {}
        self.print_logs = print_logs

        self.MIN_PATIENCE = 1
        self.MAX_PATIENCE = 3
        
        self.events = []

        self.cost_per_window = 0.03

    def run_until_time(self):
            
        self.env.process(self.source())
        self.env.run(until=self.max_time)
            
        return self.fin_result()


    def source(self):
        """Source generates customers randomly"""
        customer_count = 0
        while True:
            task_type = np.random.choice(
                [0, 1], p=[self.service_types[0]['prob'], self.service_types[1]['prob']]
            )
            c = self.customer(name=f'Customer{customer_count}', task_type=task_type)
            self.env.process(c)
            t = random.expovariate(1.0 / self.interval)
            yield self.env.timeout(t)
            customer_count += 1
            

    def customer(self, name, task_type):
        """Customer arrives, is served and leaves."""
        arrive = self.env.now
        if self.print_logs:
            print('%7.4f %s: Here I am' % (arrive, name))
    
        with self.counter.request() as req:
            patience = random.uniform(self.MIN_PATIENCE, self.MAX_PATIENCE)
            # Wait for the counter or abort at the end of our tether
            results = yield req | self.env.timeout(patience)
    
            wait = self.env.now - arrive
    
            if req in results:
                # We got to the counter
                if self.print_logs:
                    print('%7.4f %s: Waited %6.3f' % (self.env.now, name, wait))

                time_in_bank = self.service_types[task_type]['time']
                yield self.env.timeout(random.expovariate(1.0 / time_in_bank))
    
                    
                if self.print_logs:
                    print('%7.4f %s: Finished' % (self.env.now, name))

                self.events.append(("completed",
                                   self.service_types[task_type]['profit'],
                                   self.service_types[task_type]['bonus'], 
                                   0, 
                                   self.env.now),
                                )
    
            else:
                # We reneged
                if self.print_logs:
                    print('%7.4f %s: RENEGED after %6.3f' % (self.env.now, name, wait))

                self.events.append(("lost", 0, 0, self.service_types[task_type]['loss_cost'], self.env.now))


    def fin_result(self):
        # action, profit, bonus, loss, time

        data = pd.DataFrame(self.events, columns=['action', 'profit', 'bonus', 'loss', 'time'])
        totals = data[[ 'profit', 'bonus', 'loss',]].sum()

        fixed_cost = self.cost_per_window * self.num_windows * self.env.now
        net_profit = totals['profit'] + totals['bonus'] - totals['loss'] - fixed_cost

        return net_profit
        