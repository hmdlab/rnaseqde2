#! /usr/bin/env python3

"""
Convert gene annotation GTF to BED for each features (exon, transcript, gene)

Usage:
  gtf2bed.py <gtf>

"""


import sys
import os

import numpy as np
import pandas as pd
from gtfparse import read_gtf


def pack_name(id: pd.Series, feature_name: pd.Series):
    return "ID=" + id + ";Name=" + feature_name


def main():
    gtf_path = sys.argv[1]

    gtf_df = read_gtf(gtf_path)
    gtf_df.strand = gtf_df.strand.replace('nan', '.')
    # gtf_df.columns
    # Index(['seqname', 'source', 'feature', 'start', 'end', 'score', 'strand',
    #        'frame', 'havana_gene', 'gene_id', 'tag', 'index', 'gene_type', 'level',
    #        'gene_name', 'transcript_id', 'transcript_name', 'havana_transcript',
    #        'ont', 'transcript_type', 'exon_id', 'exon_number',
    #        'transcript_support_level', 'protein_id', 'ccdsid'],
    #       dtype='object')

    features = ['gene', 'transcript', 'exon']

    gtf_dfs = {}
    for f in features:
        gtf_dfs[f] = gtf_df.query("feature == '{}'".format(f))

    # NOTE: bed_columns
    # 'chr', 'start', 'end', 'name', 'score', 'strand',
    # 'thick_start', 'thick_end', 'itemRgb', 'block_count', 'block_sizes', 'block_starts'

    # TODO: to output bed12

    root, ext = os.path.splitext(gtf_path)

    # Gene record
    for f in features:
        gtf_df = gtf_dfs[f]
        zeros_ = np.zeros(len(gtf_df.index)).astype(int)
        starts_ = gtf_df.start - 1
        ends_ = gtf_df.end

        ids = gtf_df["{}_id".format(f)]

        if f != 'exon':
            names = gtf_df["{}_name".format(f)]
        else:
            names = gtf_df['transcript_name'] + ':' + gtf_df['exon_number']

        bed_df = pd.DataFrame({
            'chr': gtf_df.seqname,
            'start': starts_,
            'end': ends_,
            'name': pack_name(ids, names),
            'score': zeros_,
            'strand': gtf_df.strand})

        output_path = "{}_{}.bed".format(root, f)
        print(output_path)

        with open(output_path, 'w') as f:
            bed_df.to_csv(f, sep="\t", header=False, index=False)


if __name__ == '__main__':
    main()
