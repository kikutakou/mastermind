import argparse
import os
import pickle
import time
from collections import defaultdict
from itertools import permutations, product

from logzero import logger


class Time:
    @staticmethod
    def time_str(sec):
        if sec < 60:
            return f'{sec:5.2f} sec'
        min, sec = divmod(int(sec), 60)
        if min < 60:
            return f'{min} min {sec} sec'
        hour, min = divmod(int(min), 60)
        if hour < 24:
            return f'{hour} hour {min} min'
        day, hour = divmod(int(hour), 24)
        if day < 7:
            return f'{day} days {hour} hours'
        else:
            return f'{day} days'

    def __init__(self):
        self.start_time = time.time()

    def eta(self, count, total_count):
        assert total_count > 0
        if count > total_count:
            logger.error(f'WARNING: count > total ({count} > {total_count})')

        current = time.time() - self.start_time
        percent = 100.0 * count / total_count
        elapsed = self.time_str(current)
        speed = (count / current) if current else 0.0
        eta = self.time_str((total_count - count) / speed) if speed else '---'

        return f' {count} / {total_count} ({percent:5.2f} percent) done in {elapsed} (speed {speed:.2f}/s, eta {eta})'


def check(x, y):

    hits = 0
    blows = 0

    x_copy = list(x)
    for i, (v, w) in enumerate(zip(x, y)):
        if v == w:
            hits += 1
            x_copy[i] = None

    for i, (v, w) in enumerate(zip(x_copy, y)):
        if v is not None and w in x_copy:
            blows += 1

    return (hits, blows)


def check_all(x, patterns):
    d = defaultdict(list)
    for p in patterns:
        res = check(x, p)
        d[res].append(p)
    return dict(d)


ALL_COMB_WITH_DUP = list(product([1, 2, 3, 4, 5, 6], repeat=4))
ALL_COMB_NO_DUP = list(permutations([1, 2, 3, 4, 5, 6], 4))


class Node:

    def __init__(self, candidates):
        self.candidates = candidates
        self.next_move = None
        self.nexts = {}
        if len(self.candidates) > 1:
            self.solve()

    @staticmethod
    def score(d):
        s = [0, 0]
        for (h, b), p in d.items():
            s[0] += h * len(p)
            s[1] += b * len(p)
        return tuple(s)

    def solve(self):

        # find next move x and result dict d
        if len(self.candidates) == 2:
            x = self.candidates[0]
            d = check_all(x, self.candidates)
        else:
            h = None
            for x in ALL_COMB_WITH_DUP:
                d = check_all(x, self.candidates)
                m = max(map(len, d.values()))
                if h is None or m < h[0]:
                    h = (m, x, d)
                elif m == h[0] and self.score(d) > self.score(h[2]):
                    h = (m, x, d)
            x, d = h[1:]

        # set
        self.next_move = x
        for r, p in d.items():
            self.nexts[r] = Node(p)

    def str(self, indent=1):
        if self.next_move is None:
            return f'{self.candidates[0]}'
        sep = '\n' + ' |   ' * (indent - 1) + ' |---'
        move = ''.join(map(str, self.next_move))
        msg = f'{len(self.candidates)}({move})'
        msg += ''.join(f'{sep}{r} -> {n.str(indent + 1)}' for r, n in self.nexts.items())
        return msg

    def __str__(self):
        return self.str()

    def max_depth(self):
        if self.nexts:
            return max(n.max_depth() for n in self.nexts.values()) + 1
        else:
            return 0


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', action='store_true')
    parser.add_argument('-p', '--pickle-file', default='root.pickle')
    parser.add_argument('-d', '--allow-dup', action='store_true')
    args = parser.parse_args()

    if os.path.exists(args.pickle_file) and not args.force:
        with open(args.pickle_file, 'rb') as fb:
            logger.info(f'loading {args.pickle_file}')
            root = pickle.load(fb)
    else:
        root = Node(ALL_COMB_WITH_DUP if args.allow_dup else ALL_COMB_NO_DUP)
        with open(args.pickle_file, 'wb') as fb:
            logger.info(f'saving {args.pickle_file}')
            pickle.dump(root, fb)

    print(root)


if __name__ == '__main__':
    main()
