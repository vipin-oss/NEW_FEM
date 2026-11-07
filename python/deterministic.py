"""Deterministic numeric stack.

Import this *before* numpy anywhere a result file is written.  The BLAS thread
count fixes the summation order, and with it the last digits of every reduced
quantity.  It matters most where a printed number is a difference of nearly
equal eigenvalues: the smallest flexoelectric coupling of the design map moves
by 2 % between one and many threads, which is enough to change its second
significant digit.  Nothing here fixes a random seed: the package draws no
random numbers.
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.environ.setdefault("PYTHONHASHSEED", "0")
