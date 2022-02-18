# IoT Parking Meter Simulation
# By Aussie Schnore

import random

# From stackoverflow
# https://stackoverflow.com/questions/2065553/get-all-numbers-that-add-up-to-a-number
def _sum_to_n(n, size, limit=None):
    """Produce all lists of `size` positive integers in decreasing order
    that add up to `n`."""
    if size == 1:
        yield [n]
        return
    if limit is None:
        limit = n
    start = (n + size - 1) // size
    stop = min(limit, n - size + 1) + 1
    for i in range(start, stop):
        for tail in _sum_to_n(n - i, size - 1, i):
            yield [i] + tail

def group_list(report_list, group_cnt):
    # Given a list of spot indexs group in to 'group_cnt' sublists
    report_shedule = []
    # Padding added to ensure there are enough values to create groups
    # and to give randomness to how many are sent per time interval
    padding = (group_cnt * 2) * [-200]
    report_list = report_list + padding
    random.shuffle(report_list)
    list_len = len(report_list)
    # Find groups 
    n = list_len
    size = group_cnt
    list_of_lists = _sum_to_n(n, size)
    groupings = next(list_of_lists)
    # fill groups with index
    index = 0
    for this_group_size in groupings:
        this_group = report_list[index:index+this_group_size]
        report_shedule.append(this_group)
        index = index+this_group_size
    return(report_shedule)



if __name__ == "__main__":
    # testing
    report_list = range(50)
    random.shuffle(report_list)

    grped_list = group_list(report_list, 60)
