
import torch

from torch.optim.adagrad import Adagrad
from torch.optim.lr_scheduler import ReduceLROnPlateau

import re


def add_constraints_to_job(job, mdmm_module):

    module_name = re.sub(r"\s", "", str(mdmm_module))

    lambdas = [c.lmbda for c in mdmm_module]
    slacks = [c.slack for c in mdmm_module if hasattr(c, 'slack')]

    lr, initial_lr = next((g['lr'], g['initial_lr']) for g in job.optimizer.param_groups if g['name'] == 'default')
    job.optimizer.add_param_group(
        {'name': f"lambdas_{module_name}", 'params': lambdas, 'lr': -lr, 'initial_lr': -initial_lr})

    if len(slacks) > 0:
        job.optimizer.add_param_group(
            {'name': f"slacks_{module_name}", 'params': slacks, 'lr': lr, 'initial_lr': initial_lr})
    
    # TODO: remove everything below once fixed in pytorch
    if isinstance(job.optimizer, Adagrad):
        init_acc_val = job.optimizer.defaults['initial_accumulator_value']
        for p in lambdas + slacks:
            state = job.optimizer.state[p]
            state['step'] = 0
            state['sum'] = torch.full_like(p, init_acc_val, memory_format=torch.preserve_format)
    scheduler = job.kge_lr_scheduler._lr_scheduler
    if isinstance(scheduler, ReduceLROnPlateau):
        scheduler.min_lrs += [scheduler.min_lrs[0]] * 2
