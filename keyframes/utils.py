def batch(iterable, n=1):
    length = len(iterable)
    for ndx in range(0, length, n):
        end_index = min(ndx + n, length)
        n_elemnets = end_index - ndx
        yield n_elemnets, iterable[ndx:end_index]
