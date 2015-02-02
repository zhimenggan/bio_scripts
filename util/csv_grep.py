#!/usr/bin/env python3
# https://github.com/shenwei356/bio_scripts
# Author     : Wei Shen
# Contact    : shenwei356@gmail.com
# LastUpdate : 2015-02-01

import argparse
import csv
import logging
import sys
import re

# ===================================[ args ]=================================

parser = argparse.ArgumentParser(description="Grep CSV file")

parser.add_argument('csvfile', nargs='*', type=argparse.FileType('r'),
                    default=sys.stdin, help='Input file(s)')
parser.add_argument("-v", "--verbose", help='Verbosely print information',
                    action="count", default=0)

parser.add_argument('-o', '--outfile', nargs='?', type=argparse.FileType('w'),
                    default=sys.stdout, help='Output file [STDOUT]')
parser.add_argument("-k", '--key', type=int, default=1,
                    help='Column number of key in csvfile')
parser.add_argument("-H", "--ignoretitle", help="Ignore title",
                    action="store_true")
parser.add_argument("-F", '--fs', type=str, default="\t",
                    help='Field separator [\\t]')
parser.add_argument("-Q", '--qc', type=str, default='"',
                    help='Quote char["]')

parser.add_argument('-p', '--pattern', nargs='?', type=str,
                    help='Query pattern')
parser.add_argument('-pf', '--patternfile', nargs='?', type=str,
                    help='Pattern file')
parser.add_argument("-pk", type=int, default=1, nargs='?',
                    help='Column number of key in pattern file')

parser.add_argument("-r", "--regexp", help='Pattern is regular expression',
                    action="store_true")
parser.add_argument("-n", "--invert", help="Invert match (do not match)",
                    action="store_true")

args = parser.parse_args()

# logging level
if args.verbose >= 2:
    logginglevel = logging.DEBUG
elif args.verbose == 1:
    logginglevel = logging.INFO
else:
    logginglevel = logging.WARN
logging.basicConfig(level=logginglevel,
                    format="[%(levelname)s] %(message)s")

# check args
if not args.pattern and not args.patternfile:
    logging.error("one or both of option -p and -pf needed")
    sys.exit(1)

# ===================================[ read patterns ]========================

patterns = dict()

# pattern from command line
if args.pattern:
    patterns[args.pattern] = 1

# pattern from pattern file
if args.patternfile:
    with open(args.patternfile, newline='') as patternfile:
        reader = csv.reader(patternfile, delimiter=args.fs, quotechar=args.qc)
        for row in reader:
            nrow = len(row)
            if nrow == 0:
                continue
            if nrow < args.pk:
                logging.error(
                    "-pk ({}) is beyond number of column ({})".format(args.pk, nrow))
                sys.exit(1)
            elif args.pk < 1:
                args.pk = 1

            patterns[row[args.pk - 1].strip()] = 1

logging.info("load {} patterns: [{}]".format(len(patterns),
                                             ', '.join(x for x in patterns.keys())))
logging.info("column number of key in pattern: {}".format(args.pk))
logging.info("Column number of key in csvfile: {}".format(args.key))

# pre compile the pattern
if args.regexp:
    for p in patterns:
        patterns[p] = re.compile(p)

# ===================================[ read csv ]=============================

cnt, sum = 0, 0
writer = csv.writer(args.outfile, delimiter=args.fs, quotechar=args.qc,
                    quoting=csv.QUOTE_MINIMAL)

stdinflag = False

# If "iter(sys.stdin.readline, '')" in the flowing for-loop, first line
# of stdin will be missing
if args.csvfile is sys.stdin:
    logging.info("read data from STDIN")
    stdinflag = True
    args.csvfile = [iter(sys.stdin.readline, '')]

for f in args.csvfile:
    if not stdinflag:
        logging.info("read data from file")
        f = iter(f.readline, '')
    reader = csv.reader(f, delimiter=args.fs, quotechar=args.qc)

    once = True
    for row in reader:
        if args.ignoretitle and once:  # Ignore title
            once = False
            continue

        sum += 1

        nrow = len(row)
        if nrow == 0:
            continue
        if nrow < args.key:
            logging.error(
                "-k ({}) is beyond number of column ({})".format(args.key, nrow))
            sys.exit(1)
        elif args.key < 1:
            args.key = 1
        key = row[args.key - 1].strip()

        logging.debug("line: {}; key: {}; row: {}".format(sum, key, row))

        hit = False
        if args.regexp:  # use regular expression
            for p in patterns.values():
                if p.search(key):
                    hit = True
                    break
        else:
            if key in patterns:  # full match
                hit = True

        if args.invert:
            if hit:
                continue
        else:
            if not hit:
                continue
        cnt += 1
        writer.writerow(row)

proportion = cnt / sum if not sum == 0 else 0;
logging.info("hit proportion: {:.2%} ( {} / {} )".format(proportion, cnt, sum))
