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


# REMOVED: These module-level database queries cause Flask application context errors
# config = Plex.query.filter(Plex.id == '1').first()
# plex = PlexServer(config.plexurl, config.token)

# Initialize TMDB globals (these don't require Flask context)
tmdb = TMDb()
poster_url_base = 'https://www.themoviedb.org/t/p/original'
search = Search()
movie = Movie()
discover = Discover()
tmdbtv = Episode()

# Initialize image globals as None - will be loaded when needed
banner_4k = None
mini_4k_banner = None
banner_dv = None
banner_hdr10 = None
banner_new_hdr = None
atmos = None
dtsx = None

# Constants
size = (2000,3000)
bannerbox = (0,0,2000,220)
mini_box = (0,0,350,275)
hdr_box = (0,1342,493,1608)
a_box = (0,1608,493,1766)
cutoff = 7

def get_config():
    """Get Plex configuration from database - must be called within Flask app context"""
    return Plex.query.filter(Plex.id == '1').first()

def get_plex_server():
    """Get PlexServer instance - must be called within Flask app context"""
    config = get_config()
    return PlexServer(config.plexurl, config.token)

def get_logger():
    """Get logger to avoid circular import issues"""
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
    g = re.sub(r'[*?:"<>| ]',"",g)
    g = re.sub("Guid","",g)
    g = g.split(",")
    f = filter(lambda a: "tmdb" in a, g)
    g = list(f)
    g = str(g[0])
    gv = [v for v in g if v.isnumeric()]
    g = "".join(gv)
    logger = get_logger()
    logger.debug(g)
    return g
    
def tmdb_poster_path(b_dir, i, g, episode, season):
    logger = get_logger()
    config = get_config()
    tmdb.api_key = config.tmdb_api
    
    if episode == '':
        logger.debug("is a film")
        tmdb_search = movie.details(movie_id=g)
        poster2_search = movie.images(movie_id=g)
        logger.debug(poster2_search)
        logger.info(i.title)
        poster = tmdb_search.poster_path
        return poster
    else:
        logger.debug("is TV")
        logger.debug(g+':'+season+'_'+episode)
        if g == '':
            if i.grandparentTitle == '':
                tmdb_search = tmdbtv.details(name=i.parentTitle, episode_num=episode, season_num=season)
            else:
                tmdb_search = tmdbtv.details(name=i.grandparentTitle, episode_num=episode, season_num=season)
        else:
            tmdb_search = tmdbtv.details(tv_id=g, episode_num=episode, season_num=season)
        poster = tmdb_search.still_path 
        return poster

def get_tmdb_poster(fname, poster):
    logger = get_logger()
    req = requests.get(poster_url_base+poster, stream=True)
    logger.debug("tmdb: "+poster_url_base+poster)
    logger.debug(fname)
    if req.status_code == 200:
        with open(fname, 'wb') as f:
            for chunk in req:
                f.write(chunk)
        return fname
    else:
        logger.error("Can't get poster from TMDB")

def check_banners(tmp_poster, size):
    logger = get_logger()
    try:
        background = cv2.imread(tmp_poster, cv2.IMREAD_ANYCOLOR)
        background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
        background = Image.fromarray(background)
        background = background.resize(size,Image.LANCZOS)

        # Wide banner box
        bannerchk = background.crop(bannerbox)
        # Mini Banner Box
        minichk = background.crop(mini_box)
        # Audio Box
        audiochk = background.crop(a_box)
        # HDR Box
        hdrchk = background.crop(hdr_box)
        # POSTER HASHES
        # Wide Banner
        poster_banner_hash = imagehash.average_hash(bannerchk)
        # Mini Banner
        poster_mini_hash = imagehash.average_hash(minichk)
        # Audio Banner
        poster_audio_hash = imagehash.average_hash(audiochk)
        # HDR Banner
        poster_hdr_hash = imagehash.average_hash(hdrchk)
        # General Hashes
        chk_banner = Image.open("app/img/chk-4k.png")
        chk_banner_hash = imagehash.average_hash(chk_banner)
        chk_mini_banner = Image.open("app/img/chk-mini-4k2.png")
        chk_mini_banner_hash = imagehash.average_hash(chk_mini_banner)
        chk_hdr = Image.open("app/img/chk_hdr.png")
        chk_hdr_hash = imagehash.average_hash(chk_hdr)
        chk_dolby_vision = Image.open("app/img/chk_dolby_vision.png")
        chk_dolby_vision_hash = imagehash.average_hash(chk_dolby_vision)
        chk_hdr10 = Image.open("app/img/chk_hdr10.png")
        chk_hdr10_hash = imagehash.average_hash(chk_hdr10)
        chk_new_hdr = Image.open("app/img/chk_hdr_new.png")
        chk_new_hdr_hash = imagehash.average_hash(chk_new_hdr)
        atmos_box = Image.open("app/img/chk_atmos.png")
        chk_atmos_hash = imagehash.average_hash(atmos_box)
        dtsx_box = Image.open("app/img/chk_dtsx.png")
        chk_dtsx_hash = imagehash.average_hash(dtsx_box)
        wide_banner = mini_banner = audio_banner = hdr_banner = old_hdr = False
        if poster_banner_hash - chk_banner_hash <= cutoff:
            wide_banner = True
        if poster_mini_hash - chk_mini_banner_hash <= cutoff:
            mini_banner = True
        if (
            poster_audio_hash - chk_atmos_hash < cutoff
            or poster_audio_hash - chk_dtsx_hash < cutoff
        ):
            audio_banner = True
        if poster_hdr_hash - chk_hdr_hash < cutoff:
            old_hdr = True
        if (
            poster_hdr_hash - chk_new_hdr_hash < cutoff 
            or poster_hdr_hash - chk_dolby_vision_hash < cutoff 
            or poster_hdr_hash - chk_hdr10_hash < cutoff
        ):
            hdr_banner = True
        #background.save(tmp_poster)
        return wide_banner, mini_banner, audio_banner, hdr_banner,  old_hdr
    except OSError as e:
        logger.error('Cannot open image: '+repr(e))

def get_poster(i, tmp_poster, title, b_dir, height, width, r):
    logger = get_logger()
    plex = get_plex_server()
    
    logger.debug(i.title+' Getting poster')
    imgurl = plex.transcodeImage(
        i.thumbUrl,
        height=height,
        width=width,
        imageFormat='png'
    )
    img = requests.get(imgurl, stream=True)
    filename = tmp_poster
    valid = ''
    try:
        if img.status_code == 200:
            img.raw.decode_content = True
            with open(filename, 'wb') as f:                        
                for chunk in img:
                    f.write(chunk)
            try:
                img = cv2.imread(tmp_poster, cv2.IMREAD_ANYCOLOR)
                cv2.imwrite(tmp_poster, img)
            except Exception as e:
                logger.error(repr(e))
        else:
            logger.info("Get Poster: "+title+ ' cannot find the poster for this film')
    except OSError as e:
        logger.error('Get Poster OSError: '+repr(e))
    except Exception as e:
        logger.error('Get Poster Exception: '+repr(e))

    valid = validate_image(tmp_poster)
    if valid == True:
        return tmp_poster, valid
    else:
        try: 
            poster = re.sub('static', '/config', r[0].poster)
            if poster:
                if poster:
                    tmp_poster = '/tmp/'+re.sub('/config/backup/films/', '', poster)
                    img = cv2.imread(poster, cv2.IMREAD_ANYCOLOR)
                    cv2.imwrite(tmp_poster, img)                    
                    return tmp_poster, valid
        except:
            logger.warning("poster is blank, getting poster from TMDB")
            if 'movie' in i.guid:
                t = re.sub('plex://movie/', '', i.guid)
                tmp_poster = re.sub(' ','_', '/tmp/'+t+'_poster.png')
                g = str(i.guids)
                g = get_tmdb_guid(g)
                poster = tmdb_poster_path(b_dir, i, g, '', '')
                tmp_poster = get_tmdb_poster(tmp_poster, poster)
            elif 'episode' in i.guid:
                t = re.sub('plex://episode/', '', i.guid)
                tmp_poster = re.sub(' ','_', '/tmp/'+t+'_poster.png')
                g = str(i.guids)
                g = get_tmdb_guid(g)
                season = str(i.parentIndex)
                episode = str(i.index)
                poster = tmdb_poster_path(b_dir, i, g, episode, season)            
                tmp_poster = get_tmdb_poster(tmp_poster, poster)
            return tmp_poster, valid
    
def get_season_poster(ep, tmp_poster, config):
    logger = get_logger()
    plex = get_plex_server()
    
    logger.debug(ep.title+' Getting poster')
    title = ep.title
    height=3000
    width=2000
    #logger.debug(config.plexurl+ep.parentThumb+'?X-Plex-Token='+config.token)
    imgurl = plex.transcodeImage(
        config.plexurl+ep.parentThumb+'?X-Plex-Token='+config.token,
        height=height,
        width=width,
        imageFormat='png'
    )
    img = requests.get(imgurl, stream=True)
    filename = tmp_poster
    try:
        if img.status_code == 200:
            img.raw.decode_content = True
            with open(filename, 'wb') as f:                        
                for chunk in img:
                    f.write(chunk)
            return tmp_poster 
        else:
            logger.info("Get Poster: "+title+ ' - cannot find the poster for this film')
    except OSError as e:
        logger.error('Get Poster OSError: '+repr(e))
    except Exception as e:
        logger.error('Get Poster Exception: '+repr(e))    

def get_plex_hdr(i, plex):
    logger = get_logger()
    ekey = i.key
    m = plex.fetchItems(ekey)
    for m in m:
        try:
            if m.media[0].parts[0].streams[0].DOVIPresent == True:
                hdr_version='Dolby Vision'
                try:
                    i.addLabel('Dolby Vision', locked=False)
                except:
                    pass
                if m.media[0].parts[0].streams[0].DOVIProfile == 5:
                    logger.error(i.title+" is version 5")
            elif 'HDR' in m.media[0].parts[0].streams[0].displayTitle:
                hdr_version='HDR'
                try:
                    i.addLabel('HDR', locked=False)
                except:
                    pass
            else:
                hdr_version = 'none'
            return hdr_version
        except IndexError:
            pass

def validate_image(tmp_poster):
    logger = get_logger()
    try:
        img = Image.open(tmp_poster)
        img.verify()
        logger.debug("Image is valid")
        valid = True
        return valid
    except Exception as e:
        logger.error(repr(e))
        logger.debug("Image is invalid")
        valid = False
        return valid

def upload_poster(tmp_poster, title, db, r, table, i, banner_file):
    logger = get_logger()
    logger.debug("UPLOAD POSTER")
    logger.debug(tmp_poster)
    logger.debug(banner_file)
    try:
        valid = changed = ''
        if os.path.exists(tmp_poster) == True:
            try:
                valid = validate_image(tmp_poster)
                changed = bannered_poster_compare(banner_file, r, i)
                logger.debug('poster valid / changed: '+str(valid)+' - '+str(changed))
                if (valid == True and changed == 'True'):
                    logger.debug('uploading poster')
                    i.uploadPoster(filepath=tmp_poster)
                    #time.sleep(2)
                    try:
                        row = r[0].id
                        media = table.query.get(row)
                        media.checked = '1'
                        db.session.commit()     
                    except IndexError as e:
                        logger.debug('Updating database to checked: '+repr(e))              
                elif valid == (False or ''):
                    logger.warning(title+": does not have a valid image")
                elif changed == 'False':
                    logger.warning(title+": does not appear to have changed")
            except (IOError, SyntaxError) as e:
              logger.error('Bad file: '+title)                 
        else:
            logger.error('Poster for '+title+" isn't here")
            row = r[0].id
            media = table.query.get(row)
            media.checked = '0'
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise logger.error('Database Roll back error')
            finally:
                db.session.close()
    except Exception as e:
        if 'DetachedInstanceError' in str(e):
            db.session.rollback()
        logger.error("Can't upload the poster: "+repr(e))         

def scan_files(config, i, plex):
    logger = get_logger()
    logger.debug('Scanning '+i.title)
    p = PureWindowsPath(i.media[0].parts[0].file)
    p1 = re.findall('[A-Z]', p.parts[0])
    if p1 != []:
        logger.debug('path is: '+str(p1))
        file = PurePosixPath('/films', *p.parts[1:])
    elif config.manualplexpath == 1:
        file = re.sub(config.manualplexpathfield, '/films', i.media[0].parts[0].file)
    else:
        file = re.sub(config.plexpath, '/films', i.media[0].parts[0].file)
    logger.debug(file)
    try:
        m = MediaInfo.parse(file, output='JSON')
        x = json.loads(m)
        hdr_version = get_plex_hdr(i, plex)
        if hdr_version != 'none':
            try:
                hdr_version = x['media']['track'][1]['HDR_Format_String']
            except (KeyError, IndexError):
                if "dolby" not in str.lower(hdr_version):
                    try:
                        hdr_version = x['media']['track'][1]['HDR_Format_Commercial']
                    except (KeyError, IndexError):
                        try:
                            hdr_version = x['media']['track'][1]['HDR_Format_Commercial_IfAny']
                        except (KeyError, IndexError):
                            try:
                                hdr_version = x['media']['track'][1]['HDR_Format_Compatibillity']
                            except:
                                pass
        elif not hdr_version:
            hdr_version = 'none'
        audio = "unknown"
        try:
            while True:
                for f in range(10):
                    if 'Audio' in x['media']['track'][f]['@type']:
                        if 'Format_Commercial_IfAny' in x['media']['track'][f]:
                            audio = x['media']['track'][f]['Format_Commercial_IfAny']
                            if 'XLL X' in x['media']['track'][f]["Format_AdditionalFeatures"]:
                                audio = 'DTS:X'
                            break
                        elif 'Format' in x['media']['track'][f]:
                            audio = x['media']['track'][f]['Format']
                            break
                if audio != "":
                    break
        except (IndexError, KeyError) as e:
            logger.debug(i.title+' '+repr(e))
    except Exception as e:
        logger.warning('No access to files: '+repr(e))
        audio = 'None'
        hdr_version = get_plex_hdr(i, plex)
    return audio, hdr_version

def backup_poster(tmp_poster, banners, config, r, i, b_dir, g, episode, season, guid):
    logger = get_logger()
    logger.debug("BACKUP")
    logger.debug(banners)
    if 'episode' in guid:
        fname = t = re.sub('plex://episode/', '', guid)
    elif 'movie' in guid:
        fname = re.sub('plex://movie/', '', guid)
    elif 'local' in guid: 
        fname = re.sub('local://', '', guid)
    elif 'season' in guid:
        fname = re.sub('plex://season/', '', guid)
    logger.debug(fname)
    
    if config.manualplexpath == 1:
        newdir = os.path.dirname(re.sub(config.manualplexpathfield, '/films', i.media[0].parts[0].file))+'/'
    else:
        newdir = os.path.dirname(re.sub(config.plexpath, '/films', i.media[0].parts[0].file))+'/'
    try:
        old_backup = os.path.exists(newdir+'poster_bak.png')
        if old_backup == True:
            logger.info('old backup exists')
            b_file = b_dir+fname+'.png'
            if 'static' in b_file:
                b_file = re.sub('static', '/config', b_file)
            logger.debug(b_file)
            shutil.copy(newdir+'poster_bak.png', b_file)
            return b_file
    except:
        pass
    if True not in banners:
        logger.debug("Poster doesn't have any banners")
        logger.debug(i.title+" No banners detected so adding backup file to database")
        try:
            if r[0].poster:
                b_file = r[0].poster
            else:
                b_file = b_dir+fname+'.png'
        except:
            b_file = b_dir+fname+'.png'
        try:
            b_file = re.sub('static', '/config', b_file)
        except:
            print("this didn't work")
        try:
            shutil.copy(tmp_poster, b_file)
        except:
            pass
        return b_file
    elif True in banners:
        logger.debug('Poster has Banners')
        if r:
            logger.debug("File is in database")
            p = os.path.exists(re.sub('static', '/config', r[0].poster))
            logger.debug(p)
            if p == True:
                logger.debug("poster found")
                if 'poster_not_found' not in r[0].poster:
                    b_file = r[0].poster
                    return b_file
            else: #  p == 'False':
                logger.debug("restoring from tmbd")
                g = get_tmdb_guid(g)
                if 'films' in b_dir:
                    tmdb_search = movie.details(movie_id=g)
                    poster = tmdb_search.poster_path
                elif 'tv' in b_dir:
                    season = str(i.parentIndex)
                    episode = str(i.index)
                    tmdb_search = tmdbtv.details(tv_id=g, episode_num=episode, season_num=season)
                    poster = tmdb_search.still_path
                logger.info(i.title)
                b_file = get_tmdb_poster(fname, poster)
                b_file = re.sub('static', '/config', b_file)
                return b_file                        
        else:
            logger.debug('not in database')
            if (config.tmdb_restore == 1 and old_backup == False):
                try:
                    logger.info('Poster has banners, creating a backup from TheMovieDB')
                    g = get_tmdb_guid(str(g))

                    poster = tmdb_poster_path(b_dir, i, g, episode, season)
                    b_file = get_tmdb_poster(fname, poster)
                    b_file = re.sub('static', '/config', b_file)
                    return b_file
                except Exception as e:
                    logger.error(repr(e))
                    b_file = 'static/img/poster_not_found.png'
                    return b_file
            else:
                logger.warning("Creating backup file from TMDb didn't work")

def insert_intoTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season):
    logger = get_logger()
    plex = get_plex_server()
    
    logger.debug(table)
    logger.debug(tmp_poster)
    url = "https://app.plex.tv/desktop#!/server/"+str(plex.machineIdentifier)+'/details?key=%2Flibrary%2Fmetadata%2F'+str(i.ratingKey)
    db.session.close()
    p = PureWindowsPath(i.media[0].parts[0].file)
    p1 = re.findall('[A-Z]', p.parts[0])    
    if p1 != []:
        newdir = PurePosixPath('/films', *p.parts[1:])
    elif config.manualplexpath == 1:
        newdir = re.sub(config.manualplexpathfield, '/films', i.media[0].parts[0].file)
    else:
        newdir = re.sub(config.plexpath, '/films', i.media[0].parts[0].file)           
    logger.debug(title+' '+hdr+' '+audio)
    if blurred == False:  
        b_file = backup_poster(tmp_poster, banners, config, r, i, b_dir, g, episode, season, guid)
    else:
        title = re.sub(r'[\\/*?:"<>| ]', '_', title)
        tmp_poster = re.sub(' ','_', '/tmp/'+title+'_poster.png')
        tmp_poster = get_poster(i, tmp_poster, title)
    try:
        if 'config' in b_file:
            b_file = re.sub('/config', 'static', b_file)
    except:
        pass
    logger.debug('Adding '+i.title+' to database')
    logger.debug(b_file)
    if ('film_table' in str(table) or 'season_table' in str(table)):
        film = table(title=title, guid=guid, guids=guids, size=size, res=res, hdr=hdr, audio=audio, poster=b_file, checked='0', url=url)
    elif 'ep_table' in str(table):
        show_season = i.grandparentTitle+': '+i.parentTitle
        film = table(title=title, guid=guid, guids=guids, size=size, res=res, hdr=hdr, audio=audio, poster=b_file, checked='0', show_season=show_season)
    try:
        db.session.add(film)
        db.session.commit()
    except:
        db.session.rollback()
        raise logger.error(Exception('Database Roll back error'))
    finally:
        db.session.close()

def updateTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season):
    logger = get_logger()
    plex = get_plex_server()
    
    db.session.close()
    url = "https://app.plex.tv/desktop#!/server/"+str(plex.machineIdentifier)+'/details?key=%2Flibrary%2Fmetadata%2F'+str(i.ratingKey)
    logger.debug(title+' final pre-database checks')
    logger.debug(title+' '+hdr+' '+audio)  
    logger.debug(banners) 
    if blurred == False:
        b_file = backup_poster(tmp_poster, banners, config, r, i, b_dir, g, episode, season, guid)
        logger.debug(b_file)
        if 'config' in b_file:
            b_file = re.sub('/config', 'static', b_file)
    else:
        b_file = r[0].poster
    if ('film_table' in str(table) or 'season_table' in str(table)):
        try:
            logger.debug('Updating '+title+' in database')
            row = r[0].id
            film = table.query.get(row)
            film.size = size
            film.res = res
            film.hdr = hdr
            film.audio = audio
            film.poster = b_file
            film.checked = '0'
            film.url = url
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(repr(e))

        finally:
            db.session.close()
    else:
        try:
            logger.debug('Updating '+title+' in database')
            row = r[0].id
            film = table.query.get(row)
            film.show_season = i.grandparentTitle+': '+i.parentTitle
            film.size = size
            film.res = res
            film.hdr = hdr
            film.audio = audio
            film.poster = b_file
            film.checked = '0'
            db.session.commit()
        except:
            db.session.rollback()
            raise logger.error(Exception('Database Roll back error'))

        finally:
            db.session.close()        

def blur(tmp_poster, r, table, db, guid):
    poster = re.sub('.png', '.blurred.png', tmp_poster)
    background = cv2.imread(tmp_poster, cv2.IMREAD_ANYCOLOR)
    background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
    background = Image.fromarray(background)
    blur = background.filter(ImageFilter.GaussianBlur(30))
    blur.save(poster)
    from app.models import ep_table
    r = ep_table.query.filter(ep_table.guid == guid).all()
    row = r[0].id
    film = table.query.get(row)
    film.blurred = '1'
    db.session.commit()
    return poster

def check_tv_banners(i, tmp_poster, img_title):
    logger = get_logger()

    box_4k= (42,45,290,245)
    hdr_box = (32,440,303,559)
    a_box = (32,560,306,685)
    cutoff = 10
    size = (1280,720)
    background = open_poster(tmp_poster, size)


    # 4K banner box
    bannerchk = background.crop(box_4k)
    # Audio Box
    audiochk = background.crop(a_box)
    # HDR Box
    hdrchk = background.crop(hdr_box)

    # POSTER HASHES
    # 4K Banner
    poster_banner_hash = imagehash.average_hash(bannerchk)
    # Audio Banner
    poster_audio_hash = imagehash.average_hash(audiochk)
    # HDR Banner
    poster_hdr_hash = imagehash.average_hash(hdrchk)

    # General Hashes
    chk_4k = Image.open("app/img/tv/chk_4k.png")
    chk_banner_hash = imagehash.average_hash(chk_4k)

    chk_hdr = Image.open("app/img/tv/chk_hdr.png")
    chk_hdr_hash = imagehash.average_hash(chk_hdr)

    chk_dolby_vision = Image.open("app/img/tv/chk_dv.png")
    chk_dolby_vision_hash = imagehash.average_hash(chk_dolby_vision)

    chk_hdr10 = Image.open("app/img/tv/chk_hdr10.png")
    chk_hdr10_hash = imagehash.average_hash(chk_hdr10)

    atmos_box = Image.open("app/img/tv/chk_atmos.png")
    chk_atmos_hash = imagehash.average_hash(atmos_box)

    dtsx_box = Image.open("app/img/tv/chk_dts.png")
    chk_dtsx_hash = imagehash.average_hash(dtsx_box)

    banner_4k = audio_banner = hdr_banner = False

    if poster_banner_hash - chk_banner_hash < cutoff:
        banner_4k = True
    if (
        poster_audio_hash - chk_atmos_hash < cutoff
        or poster_audio_hash - chk_dtsx_hash < cutoff
    ):
        audio_banner = True
    if (
        poster_hdr_hash - chk_hdr_hash < cutoff 
        or poster_hdr_hash - chk_dolby_vision_hash < cutoff 
        or poster_hdr_hash - chk_hdr10_hash < cutoff
    ):
        hdr_banner = True
    #background.save(tmp_poster)
    return banner_4k, audio_banner, hdr_banner

def add_bannered_poster_to_db(tmp_poster, db, title, table, guid, banner_file):
    logger = get_logger()
    logger.debug(banner_file)
    shutil.copy(tmp_poster, banner_file)
    try:    
        logger.debug('Adding bannered poster for: '+title+' in database')
        r = table.query.filter(table.guid == guid).all()
        row = r[0].id
        media = table.query.get(row)       
        media.bannered_poster = re.sub('/config','static', banner_file)
        db.session.commit()   
    finally:
        db.session.close()

def add_season_to_db(db, title, table, pguid, banner_file, poster):
    logger = get_logger()
    try:    
        logger.debug('Updating '+title+' in database')
        r = table.query.filter(table.guid == pguid).all()  
        poster = re.sub('/config', 'static', poster)
        banner_file = re.sub('/config', 'static', banner_file)
        if r:
            logger.debug('r exists')
            row = r[0].id
            media = table.query.get(row)      
            media.bannered_poster = banner_file
            media.poster = poster
            media.checked = '0'
            db.session.commit()          
        else:
            logger.debug(title+' '+pguid+' '+poster+' '+banner_file)
            season = table(title=title, guid=pguid, poster=poster, bannered_poster=banner_file)
            try:
                db.session.add(season)
                db.session.commit()
            except:
                db.session.rollback()
                raise Exception('Database Rollback error')
    except Exception as e:
        db.session.rollback()
        logger.error(repr(e))   
    finally:
        db.session.close() 

def check_for_new_poster(tmp_poster, r, i, table, db):
    logger = get_logger()
    new_poster = 'False'
    if r:
        try:
            try:
                poster_file = r[0].bannered_poster
            except AttributeError:
                poster_file = r[0].bannered_poster
            poster_file = re.sub('static', '/config', poster_file)
            
            try:
                bak_poster = cv2.imread(poster_file, cv2.IMREAD_ANYCOLOR)
                bak_poster = cv2.cvtColor(bak_poster, cv2.COLOR_BGR2RGB)
                bak_poster = Image.fromarray(bak_poster)
                bak_poster_hash = imagehash.average_hash(bak_poster)
                poster = cv2.imread(tmp_poster, cv2.IMREAD_ANYCOLOR)
                poster = cv2.cvtColor(poster, cv2.COLOR_BGR2RGB)
                poster = Image.fromarray(poster)
                poster_hash = imagehash.average_hash(poster)
            except SyntaxError as e:
                    logger.error('Check for new poster Syntax Error: '+repr(e))
            except OSError as e:
                    logger.error('Check for new poster OSError: '+repr(e))
                    if ('FileNotFoundError'  or 'Errno 2 ') in e:
                        logger.debug(i.title+' - Poster Not found')
                        new_poster = 'BLANK'

                    else:
                        logger.debug(i.title)
                        logger.warning('Check for new Poster: '+repr(e))

            if poster_hash - bak_poster_hash > cutoff:
                logger.debug(i.title+' - Poster has changed')
                new_poster = 'True'
                    
            else:
                logger.debug('Poster has not changed')
      
        except Exception as e:
            logger.error('Check for new poster Exception: '+repr(e))
            if '!_src.empty()' in str(e):
                logger.error("poster is blank")
                new_poster = 'BLANK'
            else:
                logger.debug('Film not in database yet')
                new_poster = 'True'
    else:
        new_poster='True'
    if (new_poster == 'True' and r):
        try:
            row = r[0].id
            media = table.query.get(row)
            media.checked = '0'
            db.session.commit()     
        except IndexError as e:
            logger.debug('Updating database for new detected poster: '+repr(e)) 
    return new_poster

def bannered_poster_compare(bannered_poster, r, i):
    logger = get_logger()
    new_poster = 'False'
    cutoff = 10
    clean_poster = ''
    if 'films' in bannered_poster:
        clean_poster = re.sub('bannered_films', 'films', bannered_poster)
    elif 'episodes' in bannered_poster:
        clean_poster = re.sub('bannered_episodes', 'episodes', bannered_poster)
    elif 'seasons' in bannered_poster:
        clean_poster = re.sub('bannered_seasons', 'seasons', bannered_poster) 
    try:       
        logger.debug('poster file paths: '+clean_poster+" "+bannered_poster)
        if r:
            if r[0].checked == 1:
                logger.debug('poster in database')
                try:
                    poster_file = bannered_poster
                    poster_file = re.sub('static', '/config', poster_file)
                    print('Poster file: '+poster_file)
                    try:
                        bak_poster = cv2.imread(poster_file, cv2.IMREAD_ANYCOLOR)
                        bak_poster = Image.fromarray(bak_poster)
                        bak_poster_hash = imagehash.average_hash(bak_poster)
                        poster = cv2.imread(clean_poster, cv2.IMREAD_ANYCOLOR)
                        poster = Image.fromarray(poster)
                        poster_hash = imagehash.average_hash(poster)
                    except SyntaxError as e:
                            logger.error('Check for new poster Syntax Error: '+repr(e))
                    except OSError as e:
                        logger.error('Check for new poster OSError: '+repr(e))
                        if ('FileNotFoundError'  or 'Errno 2 ') in e:
                            logger.debug(i.title+' - Poster Not found')
                            new_poster = 'True'
                        else:
                            logger.debug(i.title)
                            logger.warning('Check for new Poster: '+repr(e))
                    difference = poster_hash - bak_poster_hash
                    logger.debug('difference = '+str(difference))
                    if difference > cutoff:
                        logger.debug(i.title+' - Poster has changed')
                        new_poster = 'True'      
                    else:
                        logger.debug('Poster has not changed')
                        new_poster = 'False'
                except Exception as e:
                    logger.error('Check for new poster Exception: '+repr(e))
                    if '!_src.empty()' in str(e):
                        logger.error("poster is blank")
                        new_poster = 'True'
                    else:
                        logger.debug('Setting new poster to true')
                        new_poster = 'True'
            else:
                new_poster = 'True'
        else:
            logger.debug("can't see the poster in the db")
            new_poster='True'
    except AttributeError as e:
        logger.error('Compare bannered poster: '+repr(e))
        new_poster = 'True'
    return new_poster

def season_decision_tree(config, banners, ep, hdr, res, tmp_poster):
    logger = get_logger()
    load_image_assets()  # Load images when needed
    
    wide_banner = banners[0]
    mini_banner = banners[1]
    hdr_banner = banners[3]

    logger.debug(banners)
    logger.debug("Decision tree")    

    if (hdr != 'none' and config.hdr == 1 and hdr_banner == False):
        logger.info(ep.title+" HDR Banner")
        try:
            size = (2000,3000)
            background = cv2.imread(tmp_poster, cv2.IMREAD_ANYCOLOR)#Image.open(tmp_poster)
            background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
            background = Image.fromarray(background)
            background = background.resize(size,Image.LANCZOS)
            background.paste(banner_new_hdr, (0, 0), banner_new_hdr)
            background.save(tmp_poster)
        except OSError as e:
            logger.error('HDR Poster error: '+repr(e))
    else:
        logger.debug("Not adding hdr season banner")
    if (res == '4k' and config.films4kposters == 1 and wide_banner == mini_banner == False):
        try:
            size = (2000,3000)
            background = cv2.imread(tmp_poster, cv2.IMREAD_ANYCOLOR)#Image.open(tmp_poster)
            background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
            background = Image.fromarray(background)
            background = background.resize(size,Image.LANCZOS)
            if config.mini4k == 1:
                logger.info(ep.title+' Adding Mini 4K Banner')
                background.paste(mini_4k_banner, (0,0), mini_4k_banner)
                background.save(tmp_poster)
            else:
                logger.info(ep.title+' Adding 4k Banner')
                background.paste(banner_4k, (0, 0), banner_4k)
                background.save(tmp_poster)
        except OSError as e:
            logger.error('4K poster error: '+repr(e))
    else:
        logger.debug("Not adding 4k season banner")            

def remove_tmp_files(tmp_poster):
    try:
        os.remove(tmp_poster)
    except FileNotFoundError:
        pass  
    
def final_poster_compare(tmp_poster, plex_poster):
    size = (2000,3000)
    cropped = (1000,1500,2000,3000)
    new_poster = cv2.imread(tmp_poster, cv2.IMREAD_ANYCOLOR)
    new_poster = cv2.cvtColor(new_poster, cv2.COLOR_BGR2RGB)
    new_poster = Image.fromarray(new_poster)
    new_poster = new_poster.resize(size,Image.LANCZOS)
    new_poster = new_poster.crop(cropped)

    plex_poster = cv2.imread(plex_poster, cv2.IMREAD_ANYCOLOR)
    plex_poster = cv2.cvtColor(plex_poster, cv2.COLOR_BGR2RGB)
    plex_poster = Image.fromarray(plex_poster)
    plex_poster = plex_poster.resize(size,Image.LANCZOS)
    plex_poster = plex_poster.crop(cropped)

    new_poster_hash = imagehash.average_hash(new_poster)
    plex_poster_hash = imagehash.average_hash(plex_poster)

    if new_poster_hash == plex_poster_hash:
        logger = get_logger()
        logger.debug('Poster is good to upload')
        return True
    else:
        logger = get_logger()
        logger.debug('poster is fucked')
        return False

def open_poster(tmp_poster, size):
    logger = get_logger()
    try:
        background = cv2.imread(tmp_poster, cv2.IMREAD_ANYCOLOR)
        background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
        background = Image.fromarray(background)
        background = background.resize(size,Image.LANCZOS)
        return background
    except  OSError as e:
        logger.error(repr(e)) 

def add_banner(tmp_poster, banner, size):
    logger = get_logger()
    try:
        background = open_poster(tmp_poster, size)     
        background.paste(banner, (0, 0), banner)
        background.save(tmp_poster)

    except OSError as e:
        logger.error('Poster Background error: '+repr(e))    

def tv_banner_decision(ep, tmp_poster, banners, audio, hdr, resolution, poster_size):
    logger = get_logger()
    config = get_config()
    
    banner_4k_icon = Image.open("app/img/tv/4k.png")
    banner_bg = Image.open("app/img/tv/Background.png")
    banner_dv = Image.open("app/img/tv/dolby_vision.png")
    banner_hdr10 = Image.open("app/img/tv/hdr10.png")
    banner_new_hdr = Image.open("app/img/tv/hdr.png")
    atmos = Image.open("app/img/tv/atmos.png")
    dtsx = Image.open("app/img/tv/dtsx.png")
    banner_4k = banners[0]
    audio_banner = banners[1]
    hdr_banner = banners[2]
    if True not in banners:
        logger.debug('creating backup')
        add_banner(tmp_poster, banner_bg, poster_size)
    if resolution == '4k' and banner_4k == False:
           add_banner(tmp_poster, banner_4k_icon, poster_size)
    elif resolution != '4k' and banner_4k == False:
        logger.debug(ep.title+' does not need 4k banner') 
    elif resolution == '4k' and banner_4k != False:
        logger.debug(ep.title+' has 4k banner')
    if (
       audio_banner == False 
       and config.audio_posters == 1
       ) or (
       hdr_banner == False
       and config.hdr ==1
       ):
        if audio_banner == False:
               if 'Atmos' in audio and config.audio_posters == 1:
                   add_banner(tmp_poster, atmos, poster_size)
               elif audio == 'DTS:X' and config.audio_posters == 1:
                   add_banner(tmp_poster, dtsx, poster_size)
        elif 'Atmos' in audio:
               ep.addLabel('Dolby Atmos', locked=False)
        elif audio == 'DTS:X':
            ep.addLabel('DTS:X', locked=False)
        if hdr_banner == False:
            try:
                logger.debug(hdr)
                if 'dolby vision' in hdr and config.hdr == 1:
                    add_banner(tmp_poster, banner_dv, poster_size)
                elif "hdr10+" in hdr and config.hdr == 1:
                    add_banner(tmp_poster, banner_hdr10, poster_size)
                elif hdr != "" and config.hdr == 1:
                    add_banner(tmp_poster, banner_new_hdr, poster_size)
            except:
                pass
        elif 'dolby vision' in hdr:
            ep.addLabel('Dolby Vision', locked=False)
        elif 'hdr10+' in hdr:
            ep.addLabel('HDR10+', locked=False)
        elif hdr != '':
            ep.addLabel('HDR', locked=False)
    

def film_banner_decision(i, tmp_poster, banners, poster_size, res, audio, hdr):
    logger = get_logger()
    config = get_config()
    load_image_assets()  # Load images when needed
    
    logger.debug("Banner Decision")
    wide_banner = banners[0]
    mini_banner = banners[1]
    audio_banner = banners[2]
    hdr_banner = banners[3]
    if (audio_banner == False and config.audio_posters == 1):
        logger.debug("AUDIO decision: "+audio)         
        if 'atmos' in audio:
            add_banner(tmp_poster, atmos, poster_size)
        elif audio == 'dts:x': 
            add_banner(tmp_poster, atmos, poster_size)
    if (hdr_banner == False and config.hdr == 1):
        logger.debug("HDR: "+hdr) 
        if 'dolby vision' in str.lower(hdr):
            add_banner(tmp_poster, banner_dv, poster_size)
        elif "hdr10+" in str.lower(hdr):
            add_banner(tmp_poster, banner_hdr10, poster_size)
        elif str.lower(hdr) == "none":
            pass
        elif (hdr != "" and str.lower(hdr) != 'none'):
            add_banner(tmp_poster, banner_new_hdr, poster_size)
    if 'dolby vision' in str.lower(hdr):
        i.addLabel('Dolby Vision', locked=False)
    elif 'hdr10+' in str.lower(hdr):
        i.addLabel('HDR10+', locked=False)
    elif hdr != '':
        i.addLabel('HDR', locked=False)
    if 'atmos' in audio:
        i.addLabel('Dolby Atmos', locked=False)
    elif audio == 'dts:x':
        i.addLabel('DTS:X', locked=False) 
    if (res == '4k' and config.films4kposters == 1):
        if wide_banner == mini_banner == False:
            if config.mini4k == 1:
                add_banner(tmp_poster, mini_4k_banner, poster_size)
            else:
                add_banner(tmp_poster, banner_4k, poster_size)
        else:
            logger.debug(i.title+' Has 4k banner')                     


def clear_old_posters():
    dirpath = '/tmp/'
    for files in os.listdir(dirpath):
        if files.endswith(".png"):
            os.remove(dirpath+files)
