'''Main file for running experiments.

'''

import logging

from __init__ import setup
from lib import exp
from lib.data import setup as setup_data
from lib.exp import setup as setup_model
from lib.train import setup as setup_optimizer, main_loop
from lib.utils import print_section
from models import build_model

'''
import lib.data
from lib import exp, setup_reload
from lib.gen import setup_generation
from lib.loss import get_gan_loss
, train
from models import build, make_iterator_generator
'''


logger = logging.getLogger('cortex')




def main(eval_mode=False):
    '''Main function for continuous BGAN.

    '''
    data_args = exp.ARGS['data']
    model_args = exp.ARGS['model']
    optimizer_args = exp.ARGS['optimizer']
    train_args = exp.ARGS['train']

    print_section('LOADING DATA') ##############################################
    setup_data(**data_args)

    print_section('MODEL') #####################################################
    logger.info('Building model...')
    logger.info('Model args: {}'.format(model_args))
    models, criteria, results = build_model(**model_args)
    setup_model(models, criteria, results)

    print_section('OPTIMIZER') #################################################
    setup_optimizer(**optimizer_args)

    if eval_mode:
        return
    print_section('TRAIN') #####################################################
    main_loop(**train_args)


def reload_model(model_file):
    setup_reload(model_file)
    main(eval_mode=True)



if __name__ == '__main__':
    import torch
    use_cuda = torch.cuda.is_available()
    setup(use_cuda)

    try:
        main()
    except KeyboardInterrupt:
        print 'Cancelled'
        exit(0)