"""Console script for gridmetetl."""
from gridmetetl.etl import FpoNHM
import argparse
import datetime
from pathlib import Path


def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def valid_path(s):
    if Path(s).exists():
        return s
    else:
        raise argparse.ArgumentError(f'Path does not exist: {s}')

def valid_file(s):
    if Path(s).exists():
        return s
    else:
        raise argparse.ArgumentError(f'File does not exist: {s}')

def parser():
    my_parser = argparse.ArgumentParser(
        prog='gridmet_etl',
        description='map gridded climate data to polygon using zonal area weighted mean'
    )

    my_parser.add_argument('-t', '--extract_type', type=str,
                           help='extract method: (days) or (date)',
                           metavar='extraction type', default=None,
                           required=True, choices=['days', 'date'])

    my_parser.add_argument('-p', '--period', type=valid_date,
                           help='option: start date and end date of retrieval (YYYY-MM-DD)',
                           metavar='(YYYY-MM-DD)', default=None, nargs=2)

    my_parser.add_argument('-d', '--days', type=int,
                           help='option: number of days to retrieve; if specified take precedence over -s & -e option',
                           metavar='numdays', default=None)

    my_parser.add_argument('-f', '--file_prefix', type=str,
                           help='option: prefix for output files',
                           metavar='output_file_prefix', default='')

    my_parser.add_argument('-i', '--inpath', type=valid_path,
                           help='input_path (location of HRU shapefiles)',
                           metavar='input_path', default=None, required=True)

    my_parser.add_argument('-o', '--outpath', type=valid_path,
                        help='Output path (location of netCDF output files by shapefile output)', metavar='output_path',
                        default=None, required=True)

    my_parser.add_argument('-w', '--weightsfile', type=valid_file,
                           help='path/weight.csv - path/name of weight file',
                           metavar='weight_file', default=None, required=True)

    my_parser.add_argument('-v', '--variables', nargs='*', type=str,
                           help='override default vars',
                           choices=['tmax', 'tmin', 'ppt', 'rhmax', 'rhmin', 'ws', 'srad'],
                           metavar='GridMet_Variables',
                           default=['tmax', 'tmin', 'ppt', 'rhmax', 'rhmin', 'ws'])
    
    my_parser.add_argument('-V', '--verbose', help='output progress messages',
                           action='store_true', default=False, required=False)
    
    return my_parser

def args(parser):
    return parser.parse_args()

def get_extraction(parser, args):
    extract_type = None
    numdays = None
    startdate = None
    enddate = None
    if all(i is not None for i in [args.period, args.days]):
        parser.error('Either the --days or --period option must be specified not both')
    if all(i is None for i in [args.period, args.days]):
        parser.error('Either the --days or --period option must be specified')
    if args.extract_type is not None:
        extract_type = args.extract_type
        if args.extract_type == 'days':
            if args.days is not None:
                numdays = args.days
            else:
                parser.error('if -t --extract_type == days then -d must be specified')
        elif args.extract_type == 'date':
            if args.period is not None:
                startdate = args.period[0]
                enddate = args.period[1]
                if startdate >= enddate:
                    parser.error('when using -p the first date must occur before the second')
            else:
                parser.error('if -t --extract_type == dates then -p must be specified')
    else:
        parser.error('--extract_type must be specified')

    return extract_type, numdays, startdate, enddate

def get_file_prefix(args):
    if args.file_prefix is not None:
        return args.file_prefix
    else:
        return ''

def main(parser, args):
    """Console script for gridmetetl."""
    my_parser = parser
    my_args = args
    numdays = None
    startdate = None
    enddate = None
    idir = None
    odir = None
    wght_file = None
    extract_type = None
    file_prefix = None
    gm_vars = None

    extract_type, numdays, startdate, enddate = get_extraction(my_parser, my_args)
    idir = my_args.inpath
    odir = my_args.outpath
    wght_file = my_args.weightsfile
    file_prefix = get_file_prefix(args)
    gm_vars = my_args.variables
    verbose = my_args.verbose

    if verbose:
        print('starting script', flush=True)
    fp = FpoNHM()
    if verbose:
        print('instantiated', flush=True)

    try:
        ready = fp.initialize(gm_vars, idir, odir, wght_file,
                              etype=extract_type, days=numdays,
                              start_date=startdate, end_date=enddate,
                              fileprefix=file_prefix, verbose=verbose)
        if ready:
            if verbose:
                print('initalized\n', flush=True)
                print('running', flush=True)
            fp.run_weights()
            if verbose:
                print('finished running', flush=True)
            fp.finalize()
            if verbose:
                print('finalized', flush=True)
            return 0
        else:
            if extract_type == 'days':
                print('gridMET not updated continue with numdays -1', flush=True)
                fp.setnumdays(numdays - 1)
                if verbose:
                    print('initalized\n', flush=True)
                    print('running', flush=True)
                    print('finished running', flush=True)
                fp.finalize()
                if verbose:
                    print('finalized', flush=True)
                return 0
            else:
                print('error: extract did not return period specified, gridMET not updated', flush=True)
                return 1

    except NameError:
        print('An error: ')
        raise


if __name__ == "__main__":
    parser = parser()
    args = args(parser)

    main(parser, args)
