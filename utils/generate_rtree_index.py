import argparse
import pickle
import logging
import fiona
import sys

from pathlib import Path

from shapely.geometry import Polygon, shape
from shapely.geos import geos_version
from shapely import speedups

from rtree import index

def _setup_logging(verbose=False):
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    frmt = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format=frmt,
    )

def build_index(shp):
    '''
    Builds an index for the supplied polygon geometry. 
    Supports geojson and shapefile inputs. 
    @param [shp]: full path to shp or geojson file
    '''
    if speedups.available:
        logging.debug('Enabling GEOS speedups.')
        speedups.enable()
    else:
        logging.info('GEOS speedups not available.')

    #bboxes = []
    idx = index.Rtree('rtree')
    logging.info(f'Opening {Path(shp).name} for reading.')
    with fiona.open(shp,'r') as source:
        logging.info(f'Generating indexes for {len(source):,} polygons.')
        i = 0
        try:
            for item in source:
                i += 1
                # need to create a geomtry from the coords in the 
                # geometry, then coerce to bbox
                geom = Polygon(shape(item['geometry']))
                # insert ID and bounding box in the index
                idx.insert(int(item['id']),geom.bounds)
                if i % 10000 == 0:
                    logging.info(f'Processed {i:,} geometries.')

        except Exception as e:
            logging.error('Error generating spatial index from bounding boxes.')
            print(e)
            sys.exit(1)
        return idx 
 
def write_index(idx, fullPath):
    '''
    Writes out the index to the specified path. 
    @param [idx]: rtree object
    @param [fullPath]: Path where object should be written
    '''
    logging.debug(f'Writing out file {fullPath}')

    with open(fullPath, 'wb') as f:
        pickle.dump(idx,f)


if __name__ == '__main__':
    # parse input args and check that they exist
    parser = argparse.ArgumentParser(
        description='Build rtree for spatial data (polygons)')
    parser.add_argument('spatial_file',
        help='input spatial file (shp or json)')
    parser.add_argument('-v', '--verbose', 
        action='store_true',
        help='Log more verbosely.')
    args = parser.parse_args()
    _setup_logging(args.verbose)
    if not Path(args.spatial_file).exists():
        logging.error(f'Input file:\n{args.spatial_file}\nnot found!')
        sys.exit(1)
    logging.debug(args)

    idx = build_index(args.spatial_file)
    logging.info('Writing index...')
    write_index(idx,r'C:\DOE\test.STRTree')
