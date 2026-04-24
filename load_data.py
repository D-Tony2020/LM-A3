import os
import pickle

from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence

import nltk
nltk.download('punkt', quiet=True)
from transformers import T5TokenizerFast
import torch

PAD_IDX = 0
DECODER_BOS_TOKEN = '<extra_id_0>'


class T5Dataset(Dataset):

    def __init__(self, data_folder, split):
        self.split = split
        self.tokenizer = T5TokenizerFast.from_pretrained('google-t5/t5-small')
        self.decoder_bos_id = self.tokenizer.convert_tokens_to_ids(DECODER_BOS_TOKEN)
        self.data = self.process_data(data_folder, split, self.tokenizer)

    def process_data(self, data_folder, split, tokenizer):
        nl_path = os.path.join(data_folder, f'{split}.nl')
        with open(nl_path, 'r', encoding='utf-8') as f:
            nls = [line.strip() for line in f if line.strip()]

        sqls = None
        if split != 'test':
            sql_path = os.path.join(data_folder, f'{split}.sql')
            with open(sql_path, 'r', encoding='utf-8') as f:
                sqls = [line.strip() for line in f if line.strip()]
            assert len(nls) == len(sqls), \
                f'NL/SQL line-count mismatch in {split}: {len(nls)} vs {len(sqls)}'

        data = []
        for i, nl in enumerate(nls):
            enc = tokenizer(nl, return_tensors='pt')
            encoder_ids = enc['input_ids'][0]
            encoder_mask = enc['attention_mask'][0]

            if sqls is not None:
                sql_line = DECODER_BOS_TOKEN + sqls[i]
                dec_enc = tokenizer(sql_line, return_tensors='pt')
                decoder_ids = dec_enc['input_ids'][0]
            else:
                sql_line = DECODER_BOS_TOKEN
                decoder_ids = torch.tensor([self.decoder_bos_id], dtype=torch.long)

            data.append({
                'encoder_ids': encoder_ids,
                'encoder_mask': encoder_mask,
                'decoder_ids': decoder_ids,
                'sql_line': sql_line,
            })
        return data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        data_dict = self.data[idx]
        return data_dict['encoder_ids'], data_dict['encoder_mask'], \
            data_dict['decoder_ids'], data_dict['sql_line']


def normal_collate_fn(batch):
    """Pad encoder ids/masks and shift the decoder ids for teacher forcing.

    Returns (encoder_ids, encoder_mask, decoder_inputs, decoder_targets,
    initial_decoder_inputs).
    """
    encoder_ids = pad_sequence([b[0] for b in batch], batch_first=True, padding_value=PAD_IDX)
    encoder_mask = pad_sequence([b[1] for b in batch], batch_first=True, padding_value=0)

    decoder_padded = pad_sequence([b[2] for b in batch], batch_first=True, padding_value=PAD_IDX)
    decoder_inputs = decoder_padded[:, :-1].contiguous()
    decoder_targets = decoder_padded[:, 1:].contiguous()

    bos = batch[0][2][0].item()
    initial_decoder_inputs = torch.full((len(batch), 1), bos, dtype=torch.long)

    return encoder_ids, encoder_mask, decoder_inputs, decoder_targets, initial_decoder_inputs


def test_collate_fn(batch):
    """Test collate without labels: only encoder + initial decoder input."""
    encoder_ids = pad_sequence([b[0] for b in batch], batch_first=True, padding_value=PAD_IDX)
    encoder_mask = pad_sequence([b[1] for b in batch], batch_first=True, padding_value=0)

    bos = batch[0][2][0].item()
    initial_decoder_inputs = torch.full((len(batch), 1), bos, dtype=torch.long)

    return encoder_ids, encoder_mask, initial_decoder_inputs


def get_dataloader(batch_size, split):
    data_folder = 'data'
    dset = T5Dataset(data_folder, split)
    shuffle = split == 'train'
    collate_fn = normal_collate_fn if split != 'test' else test_collate_fn
    return DataLoader(dset, batch_size=batch_size, shuffle=shuffle, collate_fn=collate_fn)


def load_t5_data(batch_size, test_batch_size):
    train_loader = get_dataloader(batch_size, 'train')
    dev_loader = get_dataloader(test_batch_size, 'dev')
    test_loader = get_dataloader(test_batch_size, 'test')
    return train_loader, dev_loader, test_loader


def load_lines(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def load_prompting_data(data_folder):
    train_x = load_lines(os.path.join(data_folder, 'train.nl'))
    train_y = load_lines(os.path.join(data_folder, 'train.sql'))
    dev_x = load_lines(os.path.join(data_folder, 'dev.nl'))
    dev_y = load_lines(os.path.join(data_folder, 'dev.sql'))
    test_x = load_lines(os.path.join(data_folder, 'test.nl'))
    return train_x, train_y, dev_x, dev_y, test_x
