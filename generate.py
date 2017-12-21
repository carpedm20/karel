#!/usr/bin/env python
import os
import argparse
import numpy as np

from karel import KarelWithCurlyParser, KarelForSynthesisParser
from karel import str2bool, makedirs, pprint, beautify, TimeoutError

try:
    from tqdm import trange
except:
    trange = range


if __name__ == '__main__':
    data_arg = argparse.ArgumentParser()
    data_arg.add_argument('--num_train', type=int, default=1000000)
    data_arg.add_argument('--num_test', type=int, default=5000)
    data_arg.add_argument('--num_val', type=int, default=5000)
    data_arg.add_argument('--num_examples', type=int, default=2)
    data_arg.add_argument('--parser_type', type=str, default='curly', choices=['curly', 'synthesis'])
    data_arg.add_argument('--data_dir', type=str, default='data')
    data_arg.add_argument('--max_depth', type=int, default=5)
    data_arg.add_argument('--mode', type=str, default='token', choices=['text', 'token'])
    data_arg.add_argument('--beautify', type=str2bool, default=False)
    data_arg.add_argument('--world_height', type=int, default=8, help='Height of square grid world')
    data_arg.add_argument('--world_width', type=int, default=8, help='Width of square grid world')
    config = data_arg.parse_args()

    # Make directories
    makedirs(config.data_dir)
    datasets = ['train', 'test', 'val']

    # Generate datasets
    if config.parser_type == "curly":
        parser = KarelWithCurlyParser()
    elif config.parser_type == "synthesis":
        parser = KarelForSynthesisParser()

    if config.mode == 'text':
        for name in datasets:
            data_num = getattr(config, "num_{}".format(name))

            text = ""
            text_path = os.path.join(config.data_dir, "{}.txt".format(name))

            for _ in trange(data_num):
                code = parser.random_code(stmt_max_depth=config.max_depth)
                if config.beautify:
                    code = beautify(code)
                text += code  + "\n"

            with open(text_path, 'w') as f:
                f.write(text)
    else:
        for name in datasets:
            data_num = getattr(config, "num_{}".format(name))

            inputs, outputs, codes, code_lengths = [], [], [], []
            for _ in trange(data_num):
                while True:
                    parser.new_game(world_size=(config.world_width, config.world_height))
                    input = parser.get_state()

                    code = parser.random_code(stmt_max_depth=config.max_depth)
                    #pprint(code)

                    try:
                        parser.run(code)
                        output = parser.get_state()
                    except TimeoutError:
                        continue
                    except IndexError:
                        continue

                    inputs.append(input)
                    outputs.append(output)

                    token_idxes = parser.lex_to_idx(code, details=True)
                    codes.append(token_idxes)
                    code_lengths.append(len(token_idxes))
                    break

            npz_path = os.path.join(config.data_dir, name)
            np.savez(npz_path,
                     inputs=inputs,
                     outputs=outputs,
                     codes=codes,
                     code_lengths=code_lengths)
