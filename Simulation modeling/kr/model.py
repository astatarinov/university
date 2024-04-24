import random
import simpy
import numpy as np

class Bank:
    def __init__(self, env, num_windows=1, type1_prob=0.75, max_time=5000, print_logs=True):

        self.num_windows = num_windows
        self.service_types = {
            0: {'time': 9, 'prob': type1_prob, 'bonus': 0.3, 'profit': 3, 'loss_cost': 1.1},
            1: {'time': 15, 'prob': 1 - type1_prob, 'bonus': 0.5, 'profit': 6, 'loss_cost': 2.5}
        }
        self.max_time = max_time
        self.env = env
        # self.queue = simpy.Store(self.env)
        self.counter = simpy.Resource(self.env, capacity=self.num_windows)
        self.customer_visits_data = {}
        self.print_logs = print_logs

        self.MIN_PATIENCE = 1
        self.MAX_PATIENCE = 3
        self.events = []


    def run_until_time(self, max_iter=10):

        try:
            self.env.process(self.source(max_iter))
            self.env.run(until=self.max_time)
        except simpy.Interrupt:
            return self.customer_visits_data
            
        return self.customer_visits_data


    def source(self, interval):
        """Source generates customers randomly"""
        customer_count = 0
        while True:
            task_type = np.random.choice(
                [0, 1], p=[self.service_types[0]['prob'], self.service_types[1]['prob']]
            )
            c = self.customer(name=f'Customer{customer_count}', task_type=task_type)
            self.env.process(c)
            t = random.expovariate(1.0 / interval)
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
                                   self.service_types[task_type]['bonus']))
    
            else:
                # We reneged
                if self.print_logs:
                    print('%7.4f %s: RENEGED after %6.3f' % (self.env.now, name, wait))

                self.events.append(("lost", self.service_types[task_type]['cost']))
        