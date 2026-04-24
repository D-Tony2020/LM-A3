import os

import torch

import transformers
from transformers import T5ForConditionalGeneration, T5Config
from transformers.pytorch_utils import ALL_LAYERNORM_LAYERS
import wandb

DEVICE = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

T5_CHECKPOINT = 'google-t5/t5-small'


def setup_wandb(args):
    """Initialize a wandb run from the parsed argparse namespace."""
    wandb.init(
        project=getattr(args, 'wandb_project', 'a4-text2sql'),
        name=getattr(args, 'experiment_name', 'experiment'),
        config={k: v for k, v in vars(args).items()},
    )


def initialize_model(args):
    """Either finetune the pretrained `t5-small` checkpoint or train a model
    with the same architecture from random initialization.
    """
    if getattr(args, 'finetune', False):
        model = T5ForConditionalGeneration.from_pretrained(T5_CHECKPOINT)
    else:
        config = T5Config.from_pretrained(T5_CHECKPOINT)
        model = T5ForConditionalGeneration(config)
    return model.to(DEVICE)


def mkdir(dirpath):
    if not os.path.exists(dirpath):
        try:
            os.makedirs(dirpath)
        except FileExistsError:
            pass


def save_model(checkpoint_dir, model, best):
    mkdir(checkpoint_dir)
    name = 'best.pth' if best else 'latest.pth'
    torch.save(model.state_dict(), os.path.join(checkpoint_dir, name))


def load_model_from_checkpoint(args, best):
    """Rebuild the architecture and load weights from disk.

    Looks for the checkpoint produced by `train_t5.train` under
    `checkpoints/{ft|scr}_experiments/{experiment_name}/`.
    """
    model = initialize_model(args)
    model_type = 'ft' if getattr(args, 'finetune', False) else 'scr'
    name = 'best.pth' if best else 'latest.pth'
    ckpt_dir = os.path.join('checkpoints', f'{model_type}_experiments',
                            getattr(args, 'experiment_name', 'experiment'))
    ckpt_path = os.path.join(ckpt_dir, name)
    if os.path.exists(ckpt_path):
        state = torch.load(ckpt_path, map_location=DEVICE)
        model.load_state_dict(state)
    return model


def initialize_optimizer_and_scheduler(args, model, epoch_length):
    optimizer = initialize_optimizer(args, model)
    scheduler = initialize_scheduler(args, optimizer, epoch_length)
    return optimizer, scheduler


def initialize_optimizer(args, model):
    decay_parameters = get_parameter_names(model, ALL_LAYERNORM_LAYERS)
    decay_parameters = [name for name in decay_parameters if 'bias' not in name]
    optimizer_grouped_parameters = [
        {
            'params': [p for n, p in model.named_parameters()
                       if (n in decay_parameters and p.requires_grad)],
            'weight_decay': args.weight_decay,
        },
        {
            'params': [p for n, p in model.named_parameters()
                       if (n not in decay_parameters and p.requires_grad)],
            'weight_decay': 0.0,
        },
    ]

    if args.optimizer_type == 'AdamW':
        return torch.optim.AdamW(
            optimizer_grouped_parameters, lr=args.learning_rate, eps=1e-8,
            betas=(0.9, 0.999),
        )
    raise NotImplementedError(f'Unsupported optimizer: {args.optimizer_type}')


def initialize_scheduler(args, optimizer, epoch_length):
    num_training_steps = epoch_length * args.max_n_epochs
    num_warmup_steps = epoch_length * args.num_warmup_epochs

    if args.scheduler_type == 'none':
        return None
    if args.scheduler_type == 'cosine':
        return transformers.get_cosine_schedule_with_warmup(
            optimizer, num_warmup_steps, num_training_steps)
    if args.scheduler_type == 'linear':
        return transformers.get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps, num_training_steps)
    raise NotImplementedError(f'Unsupported scheduler: {args.scheduler_type}')


def get_parameter_names(model, forbidden_layer_types):
    result = []
    for name, child in model.named_children():
        result += [
            f'{name}.{n}'
            for n in get_parameter_names(child, forbidden_layer_types)
            if not isinstance(child, tuple(forbidden_layer_types))
        ]
    result += list(model._parameters.keys())
    return result
