from PIL import Image, ImageFilter
from plexapi.server import PlexServer
import requests
import shutil
import os
import re
import imagehash
from tmdbv3api import TMDb, Search, Movie, Discover, TV, Episode, Season
from pymediainfo import MediaInfo
import json
from pathlib import PureWindowsPath, PurePosixPath
import cv2
import time
from app.models import Plex

# Remove the module-level database queries - these will be moved to functions
# config = Plex.query.filter(Plex.id == '1')  # REMOVED
# plex = PlexServer(config[0].plexurl, config[0].token)  # REMOVED

# Keep the non-database related globals
tmdb = TMDb()
poster_url_base = 'https://www.themoviedb.org/t/p/original'
search = Search()
movie = Movie()
discover = Discover()
tmdbtv = Episode()

# Initialize these as None - they'll be loaded when needed
banner_4k = None
mini_4k_banner = None
banner_dv = None
banner_hdr10 = None
banner_new_hdr = None
atmos = None
dtsx = None

# Constants
size = (2000,3000)
bannerbox= (0,0,2000,220)
mini_box = (0,0,350,275)
hdr_box = (0,1342,493,1608)
a_box = (0,1608,493,1766)
cutoff = 7

def get_config():
    """Get the Plex configuration from database"""
    return Plex.query.filter(Plex.id == '1').first()

def get_plex_server():
    """Get PlexServer instance using config from database"""
    config = get_config()
    return PlexServer(config.plexurl, config.token)

def get_logger():
    """Get logger - moved here to avoid circular imports"""
    from app.scripts import logger
    return logger

def load_image_assets():
    """Load image assets when needed"""
    global banner_4k, mini_4k_banner, banner_dv, banner_hdr10, banner_new_hdr, atmos, dtsx
    
    if banner_4k is None:
        banner_4k = cv2.imread("app/img/4K-Template.png", cv2.IMREAD_UNCHANGED)
        banner_4k = Image.fromarray(banner_4k)
        
    if mini_4k_banner is None:
        mini_4k_banner = cv2.imread("app/img/4K-mini-Template.png", cv2.IMREAD_UNCHANGED)
        mini_4k_banner = Image.fromarray(mini_4k_banner)
        
    if banner_dv is None:
        banner_dv = cv2.imread("app/img/dolby_vision.png", cv2.IMREAD_UNCHANGED)
        banner_dv = Image.fromarray(banner_dv)
        
    if banner_hdr10 is None:
        banner_hdr10 = cv2.imread("app/img/hdr10.png", cv2.IMREAD_UNCHANGED)
        banner_hdr10 = cv2.cvtColor(banner_hdr10, cv2.COLOR_BGR2RGBA)
        banner_hdr10 = Image.fromarray(banner_hdr10)
        
    if banner_new_hdr is None:
        banner_new_hdr = cv2.imread("app/img/hdr.png", cv2.IMREAD_UNCHANGED)
        banner_new_hdr = Image.fromarray(banner_new_hdr)
        
    if atmos is None:
        atmos = cv2.imread("app/img/atmos.png", cv2.IMREAD_UNCHANGED)
        atmos = Image.fromarray(atmos)
        
    if dtsx is None:
        dtsx = cv2.imread("app/img/dtsx.png", cv2.IMREAD_UNCHANGED)
        dtsx = Image.fromarray(dtsx)

def get_tmdb_guid(g):
    g = g[1:-1]
    g = re.sub(r'[*?<>|]', '', g)
    return g

def get_tmdb_poster(tmp_poster, poster):
    logger = get_logger()
    try:
        response = requests.get(poster)
        with open(tmp_poster, 'wb') as f:
            f.write(response.content)
        logger.debug('TMDB poster downloaded')
        return tmp_poster
    except Exception as e:
        logger.error(f"Error downloading TMDB poster: {e}")
        return None

def check_banners(film_poster, size):
    logger = get_logger()
    load_image_assets()  # Load images when needed
    
    # Your existing check_banners logic here
    # (I'm keeping the function signature but you'll need to add your implementation)
    pass

def film_banner_decision(film, tmp_poster, film_banners, size, resolution, audio, hdr):
    logger = get_logger()
    load_image_assets()  # Load images when needed
    
    # Your existing film_banner_decision logic here
    # (I'm keeping the function signature but you'll need to add your implementation)
    pass

def upload_poster(film_poster, title, db, r, film_table, film, banner_file):
    logger = get_logger()
    
    # Your existing upload_poster logic here
    # (I'm keeping the function signature but you'll need to add your implementation)
    pass

def remove_tmp_files(film_poster):
    logger = get_logger()
    try:
        if os.path.exists(film_poster):
            os.remove(film_poster)
        logger.debug('Temporary files removed')
    except Exception as e:
        logger.error(f"Error removing temporary files: {e}")

def get_plex_hdr(media_item, plex_server):
    """Get HDR information from Plex media item"""
    logger = get_logger()
    
    # Your existing get_plex_hdr logic here
    # (I'm keeping the function signature but you'll need to add your implementation)
    pass

def add_season_to_db(db, title, table, guid, banner_file, s_bak):
    """Add season to database"""
    logger = get_logger()
    
    # Your existing add_season_to_db logic here
    # (I'm keeping the function signature but you'll need to add your implementation)
    pass

# Add any other functions that were in your original module.py file here
# Make sure to use get_config() and get_plex_server() instead of the global variables
