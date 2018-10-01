import numpy as np


def calc_scatters(K):
    """
    Calculate scatter matrix:
    scatters[i,j] = {scatter of the sequence with starting frame i and ending frame j}
    """
    n = K.shape[0]
    K1 = np.cumsum([0] + list(np.diag(K)))
    K2 = np.zeros((n+1, n+1))
    K2[1:, 1:] = np.cumsum(np.cumsum(K, 0), 1)
    diagK2 = np.diag(K2)
    i = np.arange(n).reshape((-1, 1))
    j = np.arange(n).reshape((1, -1))
    scatters = (
            K1[1:].reshape((1, -1)) - K1[:-1].reshape((-1, 1)) - (
                diagK2[1:].reshape((1, -1)) + diagK2[:-1].reshape((-1, 1))
                - K2[1:, :-1].T - K2[:-1, 1:]
            ) / ((j - i + 1).astype(float) + (j == i-1).astype(float))
    )
    scatters[j < i] = 0
    return scatters


def cpd_nonlin(K, ncp, lmin=1, lmax=100000, backtrack=True, verbose=True, out_scatters=None):
    """ Change point detection with dynamic programming
    K - square kernel matrix
    ncp - number of change points to detect (ncp >= 0)
    lmin - minimal length of a segment
    lmax - maximal length of a segment
    backtrack - when False - only evaluate objective scores (to save memory)
    Returns: (cps, obj)
        cps - detected array of change points: mean is thought to be constant on [ cps[i], cps[i+1] )
        obj_vals - values of the objective function for 0..m changepoints
    """
    m = int(ncp)  # prevent numpy.int64

    (n, n1) = K.shape
    assert(n == n1), "Kernel matrix awaited."

    assert(n >= (m + 1) * lmin)
    assert(n <= (m + 1) * lmax)
    assert(lmax >= lmin >= 1)

    if verbose:
        print("Precomputing scatters...")
    J = calc_scatters(K)

    if out_scatters is not None:
        out_scatters[0] = J

    if verbose:
        print("Inferring best change points...")
    # I[k, l] - value of the objective for k change-points and l first frames
    I = 1e101 * np.ones((m + 1, n + 1))
    I[0, lmin:lmax] = J[0, lmin - 1:lmax - 1]

    if backtrack:
        # p[k, l] --- "previous change" --- best t[k] when t[k+1] equals l
        p = np.zeros((m + 1, n + 1), dtype=int)
    else:
        p = np.zeros((1, 1), dtype=int)

    for k in range(1, m + 1):
        for l in range((k + 1) * lmin, n + 1):
            tmin = max(k * lmin, l - lmax)
            tmax = l - lmin + 1
            c = J[tmin:tmax, l - 1].reshape(-1) + I[k - 1, tmin:tmax].reshape(-1)
            I[k, l] = np.min(c)
            if backtrack:
                p[k, l] = np.argmin(c)+tmin

    # Collect change points
    cps = np.zeros(m, dtype=int)

    if backtrack:
        cur = n
        for k in range(m, 0, -1):
            cps[k - 1] = p[k, cur]
            cur = cps[k - 1]

    scores = I[:, n].copy()
    scores[scores > 1e99] = np.inf
    return cps, scores


def cpd_auto(K, ncp, vmax, desc_rate=15, min_segments=10, **kwargs):
    """Main interface
    Detect change points automatically selecting their number
        K       - kernel between each pair of frames in video
        ncp     - maximum ncp
        vmax    - special parameter
    Optional arguments:
        lmin     - minimum segment length
        lmax     - maximum segment length
        desc_rate - rate of descriptor sampling (vmax always corresponds to 1x)
    Note:
        - cps are always calculated in subsampled coordinates irrespective to
            desc_rate
        - lmin and m should be in agreement
    ---
    Returns: (cps, costs)
        cps   - best selected change-points
        costs - costs for 0,1,2,...,m change-points
    Memory requirement: ~ (3*N*N + N*ncp)*4 bytes ~= 16 * N^2 bytes
    That is 1,6 Gb for the N=10000.
    """
    m = ncp
    (_, scores) = cpd_nonlin(K, m, backtrack=False, **kwargs)

    N = K.shape[0]
    N2 = N * desc_rate  # length of the video before subsampling

    penalties = np.zeros(m + 1)
    # Prevent division by zero (in case of 0 changes)
    ncp = np.arange(1, m + 1)
    penalties[1:] = (vmax * ncp/(2.0 * N2)) * (np.log(float(N2) / ncp) + 1)

    costs = scores/float(N) + penalties
    m_best = int(np.argmin(costs))
    m_best = max(min_segments, m_best)
    m_best = min(m_best, N)
    (cps, scores2) = cpd_nonlin(K, m_best, **kwargs)
    return cps, scores2
