#!/usr/bin/env python3
"""
Download gnomAD gene constraint metrics.
These tell us how tolerant/intolerant genes are to loss-of-function mutations.

Data includes:
- pLI: Probability of being Loss-of-function Intolerant (>0.9 = constrained)
- LOEUF: Loss-of-function Observed/Expected Upper-bound Fraction (lower = more constrained)
- Missense constraint scores
"""

import gzip
import os
import shutil
import urllib.request

DATA_DIR = 'data'

# gnomAD v4.1 constraint metrics (latest)
GNOMAD_V4_CONSTRAINT_URL = 'https://storage.googleapis.com/gcp-public-data--gnomad/release/4.1/constraint/gnomad.v4.1.constraint_metrics.tsv'

# gnomAD v2.1.1 pLoF metrics (has more detailed gene-level data)
GNOMAD_V2_LOF_URL = 'https://storage.googleapis.com/gcp-public-data--gnomad/release/2.1.1/constraint/gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz'


def download_file(url, dest_path):
    """Download a file with progress indication."""
    print(f"Downloading {url}")
    print(f"  -> {dest_path}")
    
    def progress_hook(count, block_size, total_size):
        if total_size > 0:
            percent = min(100, count * block_size * 100 / total_size)
            mb_downloaded = count * block_size / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\r  Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='', flush=True)
    
    urllib.request.urlretrieve(url, dest_path, progress_hook)
    print()  # newline after progress


def decompress_bgz(bgz_path, output_path):
    """Decompress a .bgz (bgzip) file - compatible with gzip."""
    print(f"Decompressing {bgz_path}")
    with gzip.open(bgz_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"  -> {output_path}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("=" * 60)
    print("Downloading gnomAD Gene Constraint Metrics")
    print("=" * 60)
    print()
    print("This data tells us how tolerant/intolerant genes are to mutations:")
    print("  - pLI > 0.9: Gene is intolerant to loss-of-function (essential)")
    print("  - LOEUF < 0.35: Strongly constrained genes")
    print()
    
    # Download v4.1 constraint metrics
    v4_path = os.path.join(DATA_DIR, 'gnomad_v4_constraint.tsv')
    if os.path.exists(v4_path):
        print(f"File already exists: {v4_path}")
        print("  Delete it to re-download.")
    else:
        download_file(GNOMAD_V4_CONSTRAINT_URL, v4_path)
    
    print()
    
    # Download v2.1.1 pLoF metrics (compressed)
    v2_bgz_path = os.path.join(DATA_DIR, 'gnomad_v2_lof_metrics.txt.bgz')
    v2_path = os.path.join(DATA_DIR, 'gnomad_v2_lof_metrics.txt')
    
    if os.path.exists(v2_path):
        print(f"File already exists: {v2_path}")
        print("  Delete it to re-download.")
    else:
        download_file(GNOMAD_V2_LOF_URL, v2_bgz_path)
        decompress_bgz(v2_bgz_path, v2_path)
        # Clean up compressed file
        os.remove(v2_bgz_path)
    
    print()
    print("=" * 60)
    print("Download complete!")
    print("=" * 60)
    print()
    print("Files downloaded:")
    for f in ['gnomad_v4_constraint.tsv', 'gnomad_v2_lof_metrics.txt']:
        fpath = os.path.join(DATA_DIR, f)
        if os.path.exists(fpath):
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            print(f"  {f}: {size_mb:.1f} MB")
    
    print()
    print("Next step: Run 'python import_gnomad.py' to import into database")


if __name__ == '__main__':
    main()
