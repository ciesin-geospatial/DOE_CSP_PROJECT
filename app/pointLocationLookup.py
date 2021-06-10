from datetime import date
import app_config as cfg 
import json
import logging
import pickle
import sys
import fiona
import numpy as np
import helpers
import xarray as xr

from pathlib import Path
from scipy.spatial import KDTree
from shapely.geometry import Point, Polygon, shape
from rtree import index
from haversine import haversine, Unit
from urllib.parse import urlparse

# set basic logging for when module is imported 
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# patch module-level attribute to enable pickle to work
#kdtree.node = kdtree.KDTree.node
#kdtree.leafnode = kdtree.KDTree.leafnode
#kdtree.innernode = kdtree.KDTree.innernode

# TODO: fix lat/longitude written to JSON file

''' Module to lookup features based on a point location. Uses rtrees if they exist. '''

''' GLOBALS '''
# markdown text template

# layer dictionaries. defaultLayers is always queried for model parameters. Other layers are added
# to the defaultLayers in the method call. 
# TODO: need to move to JSON files
# TODO: calculate distances to water plants, desal & power plant

# generalized country layer
countryLayer = {
    'country':{'poly':cfg.gis_query_path / 'countries_generalized.shp'}
}

countyLayer = {
    'county':{'poly':cfg.gis_query_path / 'us_county.shp'}
}

# default theme layers
defaultLayers = {
    'county':{'poly':cfg.gis_query_path / 'us_county.shp'},
    'dni':{'raster':cfg.gis_query_path / 'DNI.tif'},
    'ghi':{'raster':cfg.gis_query_path / 'GHI.tif'},
    'desalPlants':{'point':cfg.gis_query_path / 'global_desal.shp'},
    #'desalPlants':{'point':cfg.gis_query_path / 'global_desal_plants.geojson'},
    'powerPlants':{'point':cfg.gis_query_path / 'power_plants.geojson'},
    #'waterPrice':{'point':cfg.gis_query_path / 'CityWaterCosts.shp'},
    'waterPrice':{'point':cfg.gis_query_path / 'global_water_tarrifs.geojson'},
    'weatherFile':{'point':cfg.gis_query_path / 'global_weather_file.geojson'},
    'canals':{'point':cfg.gis_query_path / 'canals-vertices.geojson'},
    'waterProxy':{'point':cfg.gis_query_path / 'roads_proxy.shp'},
    'tx_county':{'poly':cfg.gis_query_path / 'tx_county_water_prices.shp'},

}

# lookup for URLs of regulatory information by state
regulatory_links = {
    'TX': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgOANT2xM5CppPXMk42iBLMJypBpnY-tDaTxYFoibcuF_kaPvjYbJczqu6N5ImNL8d7aXU6WU16iXy/pubhtml?gid=1175080604&single=true',
    'AZ': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgOANT2xM5CppPXMk42iBLMJypBpnY-tDaTxYFoibcuF_kaPvjYbJczqu6N5ImNL8d7aXU6WU16iXy/pubhtml?gid=802223381&single=true',
    'FL': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgOANT2xM5CppPXMk42iBLMJypBpnY-tDaTxYFoibcuF_kaPvjYbJczqu6N5ImNL8d7aXU6WU16iXy/pubhtml?gid=1153194759&single=true',
    'CA': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgOANT2xM5CppPXMk42iBLMJypBpnY-tDaTxYFoibcuF_kaPvjYbJczqu6N5ImNL8d7aXU6WU16iXy/pubhtml?gid=1162276707&single=true',
    'NV': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgOANT2xM5CppPXMk42iBLMJypBpnY-tDaTxYFoibcuF_kaPvjYbJczqu6N5ImNL8d7aXU6WU16iXy/pubhtml?gid=736651906&single=true',
    'CO': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgOANT2xM5CppPXMk42iBLMJypBpnY-tDaTxYFoibcuF_kaPvjYbJczqu6N5ImNL8d7aXU6WU16iXy/pubhtml?gid=334054884&single=true',
}

restrictionsLayers = {
    'landUse':{'poly':cfg.gis_query_path / 'county.shp'},
}

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


def lookupLocation(pt, mapTheme='default', verbose=False):
    ''' Method to check inputs and lookup parameters based on location. 
    Generates Markdown text (based on theme) and updates the parameters for the 
    model. 
    @param [pt]: list or tuple of point coordinates in latitude / longitude (x,y)
    @param [mapTheme]: name of map theme. '''
    _setup_logging(verbose)

    # check that coord is lat/long 
    logging.debug('Checking point coords...')
    if not -90 < float(pt[0]) < 90:
        logging.error('latitude out of bounds, check point location')
        return None
    if not -180 < float(pt[1]) < 180:
        logging.error('longitude out of bounds, check point location')
        return None

    logging.debug(f'Clicked point: {pt}')

    # get layer dictionary based on theme name
    themeLyrs = _getThemeLayers(mapTheme)
    logging.info(f'finding locations of {len(themeLyrs)} layers.')

    # find out the country (and state, if in the U.S.)
    country = _findIntersectFeatures(pt,countryLayer['country']['poly'])
    # if in the U.S., get the state
    if country is None:
        logging.info('site location outside country land areas')
    elif country['properties']['iso_merged'] == 'US':
        logging.info('getting state / county')
        state = _findIntersectFeatures(pt,countyLayer['county']['poly'])
    else:
        logging.info('international query')
    # parse the dictionary, getting intersecting / closest features for each
    closestFeatures = dict()
    logging.debug('Performing intersections')

    if not country: # outside land areas
        logging.info('water, only getting subset of features')
        # TODO: refactor to use method or better logic, not hard-coded keys! 
        exclude = set(['county','desalPlants','powerPlants','canals','waterProxy','tx_county'])
        for key, value in themeLyrs.items():
            if key in exclude:
                closestFeatures[key] = ''
            else:
                if 'point' in value.keys():
                    closestFeatures[key] = _findClosestPoint(pt,value['point'])
                elif 'poly' in value.keys():
                    closestFeatures[key] = _findIntersectFeatures(pt,value['poly'])
                elif 'raster' in value.keys():
                    tmp = _getRasterValue(pt, value['raster'])
                    # convert to float so it can be serialized as json
                    if tmp:
                        closestFeatures[key] = float(tmp)
                    else:
                        closestFeatures[key] = ''      
    # U.S. case
    elif country['properties']['iso_merged'] == 'US':
        for key, value in themeLyrs.items():
            if 'point' in value.keys():
                closestFeatures[key] = _findClosestPoint(pt,value['point'])
            elif 'poly' in value.keys():
                closestFeatures[key] = _findIntersectFeatures(pt,value['poly'])
            elif 'raster' in value.keys():
                tmp = _getRasterValue(pt, value['raster'])
                # convert raster value returned to float so it can be serialized as json
                if tmp:
                    closestFeatures[key] = float(tmp)
                else:
                    closestFeatures[key] = ''
    else:
        logging.info('international, only getting subset of features')
        # TODO: refactor to use method or better logic, not hard-coded keys! 
        exclude = set(['county','powerPlants','canals','waterProxy'])
        for key, value in themeLyrs.items():
            if key in exclude:
                closestFeatures[key] = ''
            else:
                if 'point' in value.keys():
                    closestFeatures[key] = _findClosestPoint(pt,value['point'])
                elif 'poly' in value.keys():
                    closestFeatures[key] = _findIntersectFeatures(pt,value['poly'])
                elif 'raster' in value.keys():
                    tmp = _getRasterValue(pt, value['raster'])
                    # convert to float so it can be serialized as json
                    if tmp:
                        closestFeatures[key] = float(tmp)
                    else:
                        closestFeatures[key] = ''
    # update the map data JSON file
    logging.info('Updating map json')
    _updateMapJson(closestFeatures, pt)
    # return the markdown
    return(_generateMarkdown(mapTheme,closestFeatures,pt))

def getClosestInfrastructure(pnt):
    ''' Get the closest desal and power plant locations '''
    logging.info('Getting plant info...')
    # first, check if we are outside the U.S. 
    country = _findIntersectFeatures(pnt,countryLayer['country']['poly'])
    if not country: 
        return None

    if country['properties']['iso_merged'] == 'US':
        desal = _findClosestPoint(pnt,defaultLayers['desalPlants']['point'])
        plant = _findClosestPoint(pnt,defaultLayers['powerPlants']['point'])
        canal = _findClosestPoint(pnt,defaultLayers['canals']['point'])
        water = _findClosestPoint(pnt,defaultLayers['waterProxy']['point'])
        return {
            'desal':[desal['properties']['Latitude'],desal['properties']['Longitude']],
            'plant':[plant['geometry']['coordinates'][1],plant['geometry']['coordinates'][0]],
            'canal':[canal['geometry']['coordinates'][1],canal['geometry']['coordinates'][0]],
            'water':[water['properties']['latitude'],water['properties']['longitude']],
        }
    else:
        desal = _findClosestPoint(pnt,defaultLayers['desalPlants']['point'])
        return {
            'desal':[desal['properties']['Latitude'],desal['properties']['Longitude']]
        }

def _getRasterValue(pt,raster):
    ''' lookup a raster value at a given point. Currently, only works for single-band
    rasters, behaviour for multi-band or time-enabled uncertain. '''
    with xr.open_rasterio(raster) as xarr:
        val = xarr.sel(x=pt[1],y=pt[0], method='nearest')
        return val.data.item(0)

def _calcDistance(start_pnt, end_pnt):
    ''' get the great circle distance from two lat/long coordinate pairs
    using the Haversine method (approximation)'''
    return(haversine(start_pnt,end_pnt,unit=Unit.KILOMETERS))
    return(str(closestFeatures))

def _getThemeLayers(mapTheme):
    ''' return the list of layers to search based on the map theme '''
    # TODO: read the lists from a JSON file using the helper module

    if mapTheme.lower() == 'default':
        return defaultLayers
    elif mapTheme.lower() == 'restrictions':
        return {**defaultLayers, **restrictionsLayers}

def _findMatchFromCandidates(pt,intersectLyr,candidates):
    '''open the layer and search through the candidate matches
    to find the true intersection with the point. '''
    ptGeom = Point([pt[1],pt[0]])
    # open the polygon and subset to the candidates
    with fiona.open(intersectLyr) as source:
        features = list(source)
    #featureSubset = map(features.__getitem__,candidates)
    for candidate in candidates:
        feature = features[candidate]

        if ptGeom.within(Polygon(shape(feature['geometry']))):
            return(feature)

    # if no match found, return the last checked. 
    return(feature)

def _findIntersectFeatures(pt,intersectLyr):
    ''' find features in the supplied layers that intersect the provided point 
    @param [pt]: list or tuple of point coordinates in latitude / longitude (x,y)
    @param [lyrs]: list or tuple of polygon layers to find the point
    '''
    # make the point a poly geometry
    queryPoly = Point(pt).buffer(0.1)
    bounds = list(queryPoly.bounds)
    # rtree uses a different order: left, bottom, right, top
    bounds = (bounds[1],bounds[0],bounds[3],bounds[2])
    # open the layer and find the matches
    logging.info(f'Finding intersections with {intersectLyr.stem}...')
    rtreeFile = Path(f'{intersectLyr.parent}/{intersectLyr.stem}')
    if rtreeFile.exists:
        logging.info('Using pre-built rtree index')
        idx = index.Index(str(rtreeFile.absolute()))
        possibleMatches = [x for x in idx.intersection(bounds)]
    else:
        logging.info('No index found, using slow method!!!')
        # TODO: open & find with slow method
    
    if len(possibleMatches) == 0:
        logging.info(f'No matching feature foound for {intersectLyr.stem}')
        return None
    elif len(possibleMatches) == 1:
        # single match 
        with fiona.open(intersectLyr) as source:
            features = list(source)
            ## TODO: do the intersect! 
            return features[possibleMatches[0]]
    else:
        # call the method to do polygon intersection to 
        # get the exact match from the list of possibles
        # currently not being used...
        return _findMatchFromCandidates(pt,intersectLyr,possibleMatches)
        
def _findClosestPoint(pt,lyr):
    ''' find the closest point or line to the supplied point
    @param [pt]: list or tuple of point coordinates in latitude / longitude (x,y)
    @param [closestLayers]: list of point or line layers
    ''' 
    # TODO: update max dist, I believe it's in DD, not meters or km
    queryPoint = np.asarray([pt[1],pt[0]]) 
    # open each layer and find the matches
    logging.info(f'Finding closes point for {lyr.stem}...')
    # check for kdtree
    kdFile = Path(f'{lyr.parent}/{lyr.stem}.kdtree')
    if kdFile.exists:
        logging.info('using pre-built index')
        with open(kdFile,'rb') as f:
            idx = pickle.load(f)
            closestPt = idx.query(queryPoint)
            logging.debug(closestPt)
    else:
        with fiona.open(lyr) as source:
            features = list(source)
        pts = np.asarray([feat['geometry']['coordinates'] for feat in features])
        # TODO: finish the search function for non-KDTree points
        
    if not closestPt:
        return None    
    # get the matching point
    with fiona.open(lyr) as source:
        features = list(source)
        match = features[closestPt[1]]
        return(match)

    # update json file
    try:
        helpers.json_update(data=mParams, filename=cfg.map_json)
    except FileNotFoundError:
        helpers.initialize_json(data=mParams, filename=cfg.map_json)

def _generateMarkdown(theme, atts, pnt):
    ''' generate the markdown to be returned for the current theme '''
    # TODO: something more elegant than try..except for formatted values that crash on None
    # handle the standard theme layers (all cases)
    mdown = f"Located near {atts['weatherFile']['properties'].get('City').replace('[','(').replace(']', ')')}, {atts['weatherFile']['properties'].get('State')}  \n"
    dni = atts.get('dni')
    ghi = atts.get('ghi')
    if all((dni,ghi)):
        mdown += f"DNI: {dni:,.1f}   GHI:{ghi:,.1f}   kWh/m2/day  \n" 
    else:
        mdown += "DNI: -   GHI:-  kWh/m2/day  \n"
    if atts['desalPlants']:
        desal_pt = [atts['desalPlants']['properties'].get('Latitude'),atts['desalPlants']['properties'].get('Longitude')]
        desal_dist = _calcDistance(pnt,desal_pt)
        mdown += f"**Closest desalination plant** ({desal_dist:,.1f} km) name: {atts['desalPlants']['properties'].get('Project_na')}\n"
        desal = atts['desalPlants']['properties']
        try:
            mdown += f"Capacity: {float(desal.get('Capacity')):,.0f} m3/day  \n"
        except Exception as e:
            logging.error(e)
            mdown += f"Capacity: -  \n"    
        mdown += f"Technology: {desal.get('Technology')}  \n"
        mdown += f"Feedwater:  {desal.get('Feedwater')}  \n"
        mdown += f"Customer type: {desal.get('Customer_t')}  \n"

    if atts['canals']:
        canal_pt = [atts['canals']['geometry'].get('coordinates')[1],atts['canals']['geometry'].get('coordinates')[0]]
        canal_dist = _calcDistance(pnt,canal_pt)
        mdown +=f"**Closest Canal / piped water infrastructure** ({canal_dist:,.1f} km) "
        canal_name = atts['canals']['properties'].get('Name')
        if canal_name is None:
            mdown += '  \n'
        else:
            mdown += f"{canal_name}  \n"

    # water proxy
    if atts['waterProxy']:
        water_pt = [atts['waterProxy']['properties'].get('latitude'), atts['waterProxy']['properties'].get('longitude')]
        water_dist = _calcDistance(pnt,water_pt)
        mdown +=f"**Closest Water Proxy Location** ({water_dist:,.1f} km) "
        water_name = atts['waterProxy']['properties'].get('FULLNAME')
        if water_name is None:
            mdown+= '  \n'
        else:
            mdown+= f"{water_name}  \n"
    # power plants
    if atts['powerPlants']:
        power = atts['powerPlants']['properties']
        power_pt = [atts['powerPlants']['geometry']['coordinates'][1],atts['powerPlants']['geometry']['coordinates'][0]]
        power_dist = _calcDistance(pnt,power_pt)
        mdown += f"**Closest power plant** ({power_dist:,.1f} km): {power.get('Plant_name')}  \n"

        mdown += f"Primary Generation: {power.get('Plant_primary_fuel')}  \n"
        try:
            mdown += f"Nameplate Capacity: {power.get('Plant_nameplate_capacity__MW_'):,.0f} MW  \n"
        except:
            mdown += f"Production: -  \n"
        try:
            mdown += f"Number of Generators: {power.get('Number_of_generators')}  \n"
        except:
            mdown += f"Number of Generators: -  \n"
        try: 
            mdown += f"Annual Net Generation: {power.get('Plant_annual_net_generation__MW'):,.0f} MWh  \n"
        except:
            mdown += "Annual Net Generation: - MWh  \n"
        try:
            mdown += f"Year of data: {power.get('Data_Year')}  \n"
        except:
            pass
        # try:
        #     mdown += f"Condenser Heat: {power.get('Total_Pote'):,1f} MJ (29 C < T < 41 C)  \n"
        # except:
        #     mdown += f"Condenser Heat: -  \n"

    water = atts['waterPrice']['properties']
    mdown += f"**Residential Water Prices** (2018)  \n"
    try:
        mdown += f"Utility provider: {water.get('UtilityShortName')}  \n"
        mc6 = water.get('CalcTot6M3CurrUSD')
        mc15 = water.get('CalcTot15M3CurrUSD')
        mc50 = water.get('CalcTot50M3CurrUSD')
        mc100 = water.get('CalcTot100M3CurrUSD')
        if not mc6:
            mdown += f"Consumption to 6m3: $ - /m3  \n"
        elif float(mc6) < 0.005:
            mdown += f"Consumption to 6m3: $ - /m3  \n"
        else:
            mdown += f"Consumption to 6m3: ${float(mc6)/6:,.2f}/m3  \n"
        if not mc15:
            mdown += f"Consumption to 15m3: $ - /m3  \n"
        elif float(mc15) < 0.005:
            mdown += f"Consumption to 15m3: $ - /m3  \n"
        else:
            mdown += f"Consumption to 15m3: ${float(mc15)/15:,.2f}/m3  \n"
               
        if not mc50:
            mdown += f"Consumption to 50m3: $ - /m3  \n"
        elif float(mc50) < 0.005:
            mdown += f"Consumption to 50m3: $ - /m3  \n"
        else:
            mdown += f"Consumption to 50m3: ${float(mc50)/50:,.2f}/m3  \n"

        if not mc100:
            mdown += f"Consumption to 100m3: $ - /m3  \n"
        elif float(mc100) < 0.005:
            mdown += f"Consumption to 100m3: $ - /m3  \n"
        else:
            mdown += f"Consumption to 100m3: ${float(mc100)/100:,.2f}/m3  \n"

        address = water.get('WebAddress')
        if address: 
            url_parsed = urlparse(address)
            mdown += f"[Utility Web Site]({url_parsed.scheme + '://' + url_parsed.netloc + '/'})  \n"
            mdown += f"[Utility Price List]({address})  \n"
    except Exception as e:
        logging.error(e)
        mdown += f"Residential price: -  \n"


    if atts['tx_county']:
        tx_prices = atts['tx_county']['properties']
        mdown += f'**Texas County Water Prices**  \n'
        comm_price = tx_prices.get('comm_avg')
        res_price = tx_prices.get('res_avg')
        if comm_price:
            mdown += f'Average Commercial Price: ${comm_price:,.2f}/m3  \n'
        else:
            mdown += "Average Commercial Price: $-  \n"
        if res_price:
            mdown += f"Average Residential Price: ${res_price:,.2f}/m3  \n"
        else:
            mdown += "Average Residential Prices: $-  \n"
    else:
        logging.info('No Texas County!!!')

    if atts['county']:
        state = atts['county']['properties'].get('STATEAB')
        #link = f'<a href="{regulatory_links[state]}" target="_blank">{state}</a>'
        if state in regulatory_links.keys():
            mdown += f"**Regulatory Framework**  \n"
            link = f"[Regulatory information for {state}]({regulatory_links.get(state)})"
            mdown += link + '  \n'

    return mdown
    return(str(atts))

def _updateMapJson(atts, pnt):

    mParams = dict()
    # update dictionary
    wx = atts['weatherFile']['properties']
    mParams['file_name'] = str(cfg.weather_path / wx.get('filename'))
    mParams['water_price'] = atts['waterPrice']['properties'].get('CalcTot6M3CurrUSD')
    # mParams['water_price_res'] = dfAtts.Avg_F5000gal_res_perKgal.values[0]
    mParams['latitude'] = pnt[0]
    mParams['longitude'] = pnt[1]
    if atts['desalPlants']:
        desal_pt = [atts['desalPlants']['properties'].get('Latitude'),atts['desalPlants']['properties'].get('Longitude')]
        mParams['dist_desal_plant'] = _calcDistance(pnt,desal_pt)
    else:
        mParams['dist_desal_plant'] = None
    if atts['powerPlants']:
        power_pt = [atts['powerPlants']['geometry']['coordinates'][1],atts['powerPlants']['geometry']['coordinates'][0]]
        mParams['dist_power_plant'] = _calcDistance(pnt,power_pt)
    else:
        mParams['dist_power_plant'] = None

    # mParams['dist_water_network'] = dfAtts.WaterNetworkDistance.values[0] / 1000
    mParams['ghi'] = atts.get('ghi')
    mParams['dni'] = atts.get('dni')
    if atts['waterProxy']:
        water_pt = [atts['waterProxy']['properties'].get('latitude'), atts['waterProxy']['properties'].get('longitude')]
        mParams['dist_water_network'] = _calcDistance(pnt,water_pt)
    else:
        mParams['dist_water_network'] = None

    mParams['state'] = wx.get('State')
    mParams['city'] = wx.get('City')
    mParams['Country'] = wx.get('Country')
    mParams['water_price'] = atts['waterPrice']['properties'].get('Water_bill')

    mParams['latitude'] = pnt[0]
    mParams['longitude'] = pnt[1]
    # mParams['water_price_res'] = dfAtts.Avg_F5000gal_res_perKgal.values[0]
    # mParams['dni'] = dfAtts.ANN_DNI.values[0]
    # mParams['ghi'] = dfAtts.GHI.values[0]
    # mParams['dist_desal_plant'] = dfAtts.DesalDist.values[0] / 1000
    # mParams['dist_water_network'] = dfAtts.WaterNetworkDistance.values[0] / 1000
    # mParams['dist_power_plant'] = dfAtts.PowerPlantDistance.values[0] / 1000

    # dump to config file
        # update json file
    logging.info('Writing out JSON...')
    try:
        helpers.json_update(data=mParams, filename=cfg.map_json)
    except FileNotFoundError:
        helpers.initialize_json(data=mParams, filename=cfg.map_json)

if __name__ == '__main__':
    ''' main method for testing/development '''
    import datetime
    start = datetime.datetime.now()
    _setup_logging(False)
    logging.info('starting test...')
    #ptCoords = (-73.988033,41.035572) # matches two counties
    #ptCoords = (-119.0, 26.0) # doesn't match any counties
    #ptCoords = (34.0, -115.0) # matches one county
    ptCoords = (37.0,-110.0)
    #lookupLocation(ptCoords)

    #print(getClosestPlants(ptCoords))
    #print(_calcDistance([0,0],[1,1]))
    ptCoords = (34.0, 115.0) 
    lookupLocation(ptCoords)
    end = datetime.datetime.now()
    print(f'total process took {end - start}')