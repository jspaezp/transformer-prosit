from collections import namedtuple
import pandas as pd
from elfragmentador import constants, annotate
from pandas.core.frame import DataFrame
from torch import Tensor
from typing import Dict, List, Optional, Sequence, Union

SequencePair = namedtuple("SequencePair", "aas, mods")


def encode_mod_seq(seq):
    """
    Encodes a peptide sequence to a numeric vector

    Example
    =======
    >>> samp_seq = "_AAIFVVAR_"
    >>> print(constants.MAX_SEQUENCE)
    30
    >>> out = encode_mod_seq(samp_seq)
    >>> out
    SequencePair(aas=[1, 1, 8, 5, 19, 19, 1, 15, ..., 0], mods=[0, 0, 0,..., 0, 0])
    >>> len(out)
    2
    >>> [len(x) for x in out]
    [30, 30]
    """
    seq_out = [0] * constants.MAX_SEQUENCE
    mod_out = [0] * constants.MAX_SEQUENCE

    try:
        split_seq = list(annotate.peptide_parser(seq))
        seq_out_i = [constants.ALPHABET[x[:1]] for x in split_seq]
        mod_out_i = [
            constants.MOD_PEPTIDE_ALIASES[x] if len(x) > 1 else 0 for x in split_seq
        ]
        mod_out_i = [constants.MOD_INDICES.get(x, 0) for x in mod_out_i]
        seq_out[: len(seq_out_i)] = seq_out_i
        mod_out[: len(mod_out_i)] = mod_out_i
    except ValueError:
        print(seq)
        raise ValueError

    return SequencePair(seq_out, mod_out)


def decode_mod_seq(
    seq_encoding: List[int], mod_encoding: Optional[List[int]] = None
) -> str:
    out = []

    if mod_encoding is None:
        mod_encoding = [0] * len(seq_encoding)

    for i, s in enumerate(seq_encoding):
        if s == 0:
            break

        out.append(constants.ALPHABET_S[s])
        if mod_encoding[i] != 0:
            out.append(f"[{constants.MOD_INDICES_S[mod_encoding[i]]}]")

    return "".join(out)


def get_fragment_encoding_labels(
    annotated_peaks: Optional[Union[Dict[str, int], Dict[str, float]]] = None
) -> Union[List[Union[int, float]], List[int], List[str]]:
    """
    Gets either the laels or an sequence that encodes a spectra

    Examples
    ========
    >>> get_fragment_encoding_labels()
    ['z1b1', 'z1y1',  ..., 'z3b29', 'z3y29']
    >>> get_fragment_encoding_labels({'z1y2': 100, 'z2y2': 52})
    [0, 0, 0, 100, ..., 0, 52, ...]
    """

    # TODO just redefine this to use the constant keys for fragments ...
    encoding = []
    ion_encoding_iterables = {
        "ION_TYPE": "".join(sorted(constants.ION_TYPES)),
        "CHARGE": [f"z{z}" for z in range(1, constants.MAX_FRAG_CHARGE + 1)],
        "POSITION": list(range(1, constants.MAX_ION + 1)),
    }

    # TODO implement neutral losses ...  if needed
    for charge in ion_encoding_iterables[constants.ION_ENCODING_NESTING[0]]:
        for pos in ion_encoding_iterables[constants.ION_ENCODING_NESTING[1]]:
            for ion in ion_encoding_iterables[constants.ION_ENCODING_NESTING[2]]:
                key = f"{charge}{ion}{pos}"
                if annotated_peaks is None:
                    encoding.append(key)
                else:
                    encoding.append(annotated_peaks.get(key, 0))

    return encoding


def decode_fragment_tensor(
    sequence: str,
    tensor: Union[List[int], Tensor],
) -> DataFrame:
    """
    Returns a data frame with annotations from sequence
    and a tensor encoding a spectra

    Example
    =======
    >>> import torch
    >>> foo = decode_fragment_tensor("AAACK", torch.arange(0, (constants.NUM_FRAG_EMBEDINGS)))
    >>> foo.head()
      Fragment        Mass  Intensity
    0     z1b1   72.044390        0.0
    1     z1y1  147.112804        1.0
    2     z1b2  143.081504        2.0
    3     z1y2  307.143453        3.0
    4     z1b3  214.118618        4.0
    >>> # import matplotlib.pyplot as plt
    >>> # plt.vlines(foo['Mass'], 0, foo['Intensity'])
    >>> # plt.show()
    """
    key_list = constants.FRAG_EMBEDING_LABELS
    fragment_ions = annotate.get_peptide_ions(sequence)
    masses = [fragment_ions.get(k, 0) for k in key_list]
    intensities = [float(x) for x in tensor]

    assert len(intensities) == len(masses), print(
        f"Int {len(intensities)}: \n{intensities}\n\nmasses {len(masses)}: \n{masses}"
    )

    out_dict = {"Fragment": key_list, "Mass": masses, "Intensity": intensities}
    out_df = pd.DataFrame(out_dict)
    out_df = out_df[out_df["Mass"] != 0].copy()

    return out_df
