from pathlib import Path
import argparse
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
import pytorch_lightning as pl
from elfragmentador.train import build_train_parser, main_train
from elfragmentador.model import PepTransformerModel
from elfragmentador.spectra import sptxt_to_csv


def convert_sptxt():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "file",
        type=argparse.FileType("r"),
        nargs="+",
        help="Input file(s) to convert (sptxt)",
    )

    args = parser.parse_args()

    print([x.name for x in args.file])

    for f in args.file:
        out_file = f.name + ".csv"
        if Path(out_file).exists():
            print(
                f"Skipping conversion of '{f.name}' "
                f"to '{out_file}', "
                f"because {out_file} exists."
            )
        else:
            print(f"Converting '{f.name}' to '{out_file}'")
            sptxt_to_csv(f.name, out_file)


def evaluate_checkpoint():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "checkpoint",
        type=argparse.FileType("r"),
        help="Input checkpoint to convert evaluate.",
    )
    parser.add_argument(
        "spectral_libs",
        type=argparse.FileType("r"),
        nargs="+",
        help="Input Spectra library(es) to evaluate the model on.",
    )

    args = parser.parse_args()
    raise NotImplementedError
    mod = PepTransformerModel.load_from_checkpoint(args.checkpoint.name)


def train():
    pl.seed_everything(2020)
    parser = build_train_parser()
    args = parser.parse_args()
    dict_args = vars(args)
    print("\n====== Passed command line args/params =====\n")
    for k, v in dict_args.items():
        print(f">> {k}: {v}")

    mod = PepTransformerModel(**dict_args)
    main_train(mod, args)
