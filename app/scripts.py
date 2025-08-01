from PIL import Image, ImageFile
from plexapi.server import PlexServer
import plexapi
import requests
import shutil
import os
import re
import imagehash
import logging
from logging.handlers import RotatingFileHandler
from tmdbv3api import TMDb, Search, Movie, Discover, Season, Episode, TV
from pymediainfo import MediaInfo
import json
from tautulli import RawAPI
import unicodedata
import cv2
import random
import string




def setup_logger(logger_name, log_file):
    import sqlite3
    try:
        from app.models import Plex

        config = Plex.query.filter(Plex.id == '1').first()
        if config.loglevel == 1:
            loglevel = 'DEBUG'
        else:
            loglevel = 'INFO'
        c.close()
    except Exception:
        loglevel = 'INFO'
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s')
    fileHandler = RotatingFileHandler(log_file, mode='w', maxBytes=100000, backupCount=5)
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(loglevel)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)

def logger_start():
    setup_logger('plex-utills', r"/logs/script_log.log")
    logger = logging.getLogger('plex-utills')
    return logger

logger = logger_start()

tmdb = TMDb()
poster_url_base = 'https://www.themoviedb.org/t/p/original'
tmdb.api_key = '758d054ea2656332403b34471f1f2c5a'
search = Search()
movie = Movie()
discover = Discover()
b_dir = '/config/backup/' 



size = (2000,3000)
bannerbox= (0,0,2000,246)
mini_box = (0,0,350,275)
hdr_box = (0,1342,493,1608)
a_box = (0,1608,493,1766)
cutoff = 10


def posters4k(app, webhooktitle, poster_var):
    with app.app_context():
        logger.debug(webhooktitle)
        from app.models import Plex, film_table
        from app import db
        from app import module
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        global b_dir
        tmdb.api_key = config.tmdb_api
        b_dir = 'static/backup/films/'
        banner_4k = cv2.imread("app/img/4K-Template.png", cv2.IMREAD_UNCHANGED)
        banner_4k = Image.fromarray(banner_4k)
        mini_4k_banner = cv2.imread("app/img/4K-mini-Template.png", cv2.IMREAD_UNCHANGED)
        mini_4k_banner = Image.fromarray(mini_4k_banner)
        banner_dv = cv2.imread("app/img/dolby_vision.png", cv2.IMREAD_UNCHANGED)
        banner_dv = Image.fromarray(banner_dv)
        banner_hdr10 = cv2.imread("app/img/hdr10.png", cv2.IMREAD_UNCHANGED)
        banner_hdr10 = cv2.cvtColor(banner_hdr10, cv2.COLOR_BGR2RGBA)
        banner_hdr10 = Image.fromarray(banner_hdr10)
        
        banner_new_hdr = cv2.imread("app/img/hdr.png", cv2.IMREAD_UNCHANGED)
        banner_new_hdr = Image.fromarray(banner_new_hdr)
        atmos = cv2.imread("app/img/atmos.png", cv2.IMREAD_UNCHANGED)
        atmos = Image.fromarray(atmos)
        dtsx = cv2.imread("app/img/dtsx.png", cv2.IMREAD_UNCHANGED)
        dtsx = Image.fromarray(dtsx)
        blurred=False
        episode=''
        season=''
        height = 3000
        width = 2000
        poster_size = (width, height)
        def run_script(): 

            def decision_tree(tmp_poster, banners, guid):

                wide_banner = banners[0]
                mini_banner = banners[1]
                audio_banner = banners[2]
                hdr_banner = banners[3]

                logger.debug(banners)
                logger.debug("Decision tree")
                def database_decision(banners):
                    logger.debug("Database Decision")
                    audio = hdr = ''
                    if config.skip_media_info == 1:
                        if r:
                            hdr = module.get_plex_hdr(i, plex)
                            audio = i.media[0].audioCodec
                            if str(r[0].guid) == guid and str(r[0].size) != str(size):
                                logger.debug(title+" has changed")

                                module.updateTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)
                        else:
                            logger.info(title+" is not in database, skip media info scan is true")
                            hdr = module.get_plex_hdr(i, plex)
                            audio = i.media[0].audioCodec
                            if ('none' not in hdr or ('atmos' or 'dts:x') in audio):
                                module.insert_intoTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)
                    else:
                        if r:
                            if (str(r[0].guid) == guid and str(r[0].size) != str(size)):
                                logger.debug(title+" has changed, rescanning")
                                scan = module.scan_files(config, i, plex)
                                audio = str.lower(scan[0])
                                hdr = str.lower(scan[1])
                                module.updateTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)
                            else:
                                if new_poster == 'True':
                                    audio = r[0].audio
                                    hdr = r[0].hdr
                                    module.updateTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)
                                else:
                                    logger.debug('backing up poster')
                                    audio = r[0].audio
                                    hdr = r[0].hdr
                                    module.backup_poster(tmp_poster, banners, config, r, i, b_dir, g, episode, season, guid)
                        elif not r:
                            logger.info(title+" is not in database, skip media info scan is false")
                            scan = module.scan_files(config, i, plex)
                            audio = str.lower(scan[0])
                            hdr = str.lower(scan[1])
                            if ('none' not in hdr or ('atmos' or 'dts:x') in audio or res == '4k'):
                                module.insert_intoTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)
                        else:
                            logger.debug("error message")
                    return audio, hdr

                def banner_decision(audio, hdr):
                    logger.debug("Banner Decision")
                    if (audio_banner == False and config.audio_posters == 1):
                        logger.debug("AUDIO decision: "+audio)         
                        if 'atmos' in audio:
                            module.add_banner(tmp_poster, atmos, poster_size)
                            #atmos_poster(tmp_poster)
                        elif audio == 'dts:x': 
                            module.add_banner(tmp_poster, atmos, poster_size)
                            #dtsx_poster(tmp_poster)

                    if (hdr_banner == False and config.hdr == 1):
                        logger.debug("HDR: "+hdr) 
                        if 'dolby vision' in str.lower(hdr):
                            module.add_banner(tmp_poster, banner_dv, poster_size)
                            #dolby_vision(tmp_poster)
                        elif "hdr10+" in str.lower(hdr):
                            module.add_banner(tmp_poster, banner_hdr10, poster_size)
                            #hdr10(tmp_poster)
                        elif str.lower(hdr) == "none":
                            pass
                        elif (hdr != "" and str.lower(hdr) != 'none'):
                            module.add_banner(tmp_poster, banner_new_hdr, poster_size)
                            #hdrp(tmp_poster)
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
                                module.add_banner(tmp_poster, mini_4k_banner, poster_size)
                            else:
                                module.add_banner(tmp_poster, banner_4k, poster_size)
                            #add_banner(tmp_poster)
                        else:
                            logger.debug(i.title+' Has 4k banner')                 

                audio_hdr = database_decision(banners)
                audio = audio_hdr[0]
                hdr = audio_hdr[1]
                logger.debug(audio+" "+hdr)
                banner_decision(audio, hdr)
                return(audio, hdr)

            def process(tmp_poster, guid):
                size = (2000, 3000)
                banners = module.check_banners(tmp_poster, size)
                audio_hdr = decision_tree(tmp_poster, banners, guid)
                bname = re.sub('plex://movie/', '', guid)
                banner_file = '/config/backup/bannered_films/'+bname+'.png'
                banners = module.check_banners(tmp_poster, size)
                if (True in banners and config.backup == 1):
                    module.add_bannered_poster_to_db(tmp_poster, db, title, table, guid, banner_file)

                if (
                    'none' not in audio_hdr[1]
                    or 'atmos' in str.lower(audio_hdr[0])
                    or 'dts:x' in str.lower(audio_hdr[0])
                    or res == '4k'
                ):
                    logger.debug(str(audio_hdr)+' - '+res)
                    r = film_table.query.filter(film_table.guid == guid).all()
                    #logger.warning('upload poster would happen now but is disabled')
                    poster_good = module.final_poster_compare(tmp_poster, plex_poster)
                    if poster_good == True:
                        module.upload_poster(tmp_poster, title, db, r, table, i, banner_file)
                    else: 
                        logger.debug('It looks like there may be some corruption, not uploading poster for: '+title) 
                else:
                    logger.debug('Not uploading poster for: '+title)  
            def add_url(i, r, table, plex):
                try:
                    url = "https://app.plex.tv/desktop#!/server/"+str(plex.machineIdentifier)+'/details?key=%2Flibrary%2Fmetadata%2F'+str(i.ratingKey)
                    row = r[0].id
                    film = table.query.get(row)
                    film.url = url
                    db.session.commit()
                except:
                    db.session.rollback()
                    raise logger.error(Exception)

            for i in films.search(title=webhooktitle):
                try:
                    table = film_table
                    i.title = unicodedata.normalize('NFD', i.title).encode('ascii', 'ignore').decode('utf8')
                    i.title = re.sub('#', '', i.title)
                    logger.info(i.title)           
                    title = i.title
                    guid = str(i.guid)
                    guids = str(i.guids)
                    g = guids
                    size = i.media[0].parts[0].size
                    r = table.query.filter(table.guid == guid).all()
                    res = i.media[0].videoResolution    
                    t = re.sub('plex://movie/', '', guid)
                    tmp_poster = re.sub(' ','_', '/tmp/'+t+'_poster.png')
                    plex_poster = re.sub(' ','_', '/tmp/'+t+'_plex_poster.png')
                    if poster_var == '':
                        g_poster = module.get_poster(i, tmp_poster, title, b_dir, height, width, r) 
                        tmp_poster = g_poster[0]
                    else:
                        tmp_poster = module.get_tmdb_poster(tmp_poster, poster_var) 
                    plex_poster = shutil.copy(tmp_poster, plex_poster)
                    new_poster = ''
                    if r:
                        logger.debug(g_poster[1])
                        if g_poster[1] == True:
                            new_poster = module.check_for_new_poster(tmp_poster, r, i, table, db)
                        else: 
                            new_poster = 'True'                       
                        logger.debug('New poster = '+new_poster)
                        try:
                            if (
                                r[0].checked == 0
                                or str(r[0].size) != str(size)
                                or new_poster == 'True'
                            ):
                                logger.debug('Processing '+i.title)
                                process(tmp_poster, guid)
                            elif (new_poster == 'BLANK' and config.tmdb_restore == 1):
                                logger.warning("Poster has returned a blank image, restoring from TMDB and continuing")
                                tmp_poster = re.sub(' ','_', '/tmp/'+t+'_poster.png')
                                g = module.get_tmdb_guid(g)
                                poster = module.tmdb_poster_path(b_dir, i, g, episode, season)
                                tmp_poster = module.get_tmdb_poster(tmp_poster, poster)
                                process(tmp_poster, guid)
                            elif (new_poster == 'BLANK' and config.tmdb_restore == 1):
                                logger.error("Poster has returned a blank image, enable TMDB restore to continue with a poster from TheMovieDB")
                            else:
                                logger.info(title+' has been processed and the file has not changed, skiping')
                        except Exception as e:
                            logger.error(repr(e))
                        add_url(i, r, table, plex)
                    else:
                        logger.debug(title+' not in database')

                        process(tmp_poster, guid)
                except Exception as e:
                    logger.error("script error: "+repr(e))
            module.clear_old_posters()      
            logger.info('4k Poster script has finished')
            
        lib = config.filmslibrary.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                for l in range(n):
                    films = plex.library.section(lib[l])
                    run_script()
            except IndexError:
                pass

def guid_to_title(app, var):
    with app.app_context():
        logger.debug(var)
        from app import models
        config = models.Plex.query.filter(models.Plex.id == '1')
        plex = PlexServer(config.plexurl, config.token)
        if 'movie' in var:
            def run_script():
                for i in films.search(guid=var):
                    title = i.title
                    try:
                        logger.debug('Trying to remove bannered poster')
                        from app import db
                        r = models.film_table.query.filter(models.film_table.guid == var).all()
                        try:
                            os.remove(re.sub('static', '/config', r[0].bannered_poster))
                        except: pass
                        row = r[0].id
                        film = models.film_table.query.get(row)
                        film.bannered_poster = ''
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        logger.error(repr(e))
                    finally:
                       db.session.close()
                    posters4k(app, title, '')
            lib = config.filmslibrary.split(',')
            logger.debug(lib)
            n = len(lib)
            if n <= 2:
                try:
                    for l in range(n):
                        films = plex.library.section(lib[l])
                        run_script()
                except IndexError:
                    pass  
        elif 'episode' in var:
            def run_script():
                tv_episode_poster(app, var, '')

            tvlib = config.tvlibrary


            if not tvlib or not tvlib.strip():


                return []


            lib = tvlib.split(',')
            logger.debug(lib)
            n = len(lib)
            if n <= 2:
                try:
                    #while true:
                        for l in range(n):
                            tv = plex.library.section(lib[l])
                            run_script()
                except IndexError:
                    pass    
        elif 'local' in var:
            def run_script():
                tv_episode_poster(app, var, '')

            tvlib = config.tvlibrary


            if not tvlib or not tvlib.strip():


                return []


            lib = tvlib.split(',')
            logger.debug(lib)
            n = len(lib)
            if n <= 2:
                try:
                    #while true:
                        for l in range(n):
                            tv = plex.library.section(lib[l])
                            run_script()
                except IndexError:
                    pass    
        else:
            logger.warning("not running script for: "+var)
        
def tv_episode_poster(app, epwebhook, poster):
    with app.app_context():    
        from app.models import Plex, ep_table, season_table
        from app import db
        from app import module
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        banner_4k_icon = Image.open("app/img/tv/4k.png")
        banner_bg = Image.open("app/img/tv/Background.png")
        banner_dv = Image.open("app/img/tv/dolby_vision.png")
        banner_hdr10 = Image.open("app/img/tv/hdr10.png")
        banner_new_hdr = Image.open("app/img/tv/hdr.png")
        atmos = Image.open("app/img/tv/atmos.png")
        dtsx = Image.open("app/img/tv/dtsx.png")
        tmdb.api_key = config.tmdb_api    
        b_dir = 'static/backup/tv/episodes/'
        poster_size = (1280, 720)
        logger.info('Starting 4k Tv poster script')
        def run_script():
            def decision_tree(tmp_poster):
                banners = module.check_tv_banners(i, tmp_poster, img_title)
                banner_4k = banners[0]
                audio_banner = banners[1]
                hdr_banner = banners[2]
                season = str(i.parentIndex)
                episode = str(i.index)
                logger.debug(banners)
                def database_decision(r):
                    if r:
                        audio = r[0].audio
                        hdr= r[0].hdr
                        if str(r[0].guid) == guid:
                            logger.debug(title+' GUID match')
                            if str(r[0].size) != size:
                                    logger.debug(title+" has changed, rescanning")
                                    scan = module.scan_files(config, i, plex)
                                    audio = scan[0]
                                    hdr = str.lower(scan[1])                            
                                    module.updateTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)
                            else:
                                module.updateTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)

                            if not r[0].poster and True not in banners:
                                module.updateTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)
                            else:
                                logger.debug(title+' is the same')

                        else:
                            scan = module.scan_files(config, i, plex)
                            audio = scan[0]
                            hdr = str.lower(scan[1])
                            logger.debug(hdr)
                            if hdr == "":
                                hdr = module.get_plex_hdr(i, plex)
                            module.updateTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)
                    else:
                        logger.debug('File not in Database')
                        scan = module.scan_files(config, i, plex)
                        audio = scan[0]
                        hdr = str.lower(scan[1])
                        try:
                            module.insert_intoTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)
                        except Exception as e:
                            logger.warning('Database decision: '+repr(e))

                    def banner_decision(audio, hdr):
                        if True not in banners:
                            logger.debug('creating backup')
                            module.add_banner(tmp_poster, banner_bg, poster_size)

                        if resolution == '4k' and banner_4k == False:
                            module.add_banner(tmp_poster, banner_4k_icon, poster_size)
                        elif resolution != '4k' and banner_4k == False:
                            logger.debug(img_title+' does not need 4k banner') 
                        elif resolution == '4k' and banner_4k != False:
                            logger.debug(img_title+' has 4k banner')

                        if (
                        audio_banner == False 
                        and config.audio_posters == 1
                        ) or (
                        hdr_banner == False
                        and config.hdr ==1
                        ):

                            if audio_banner == False:
                                if 'Atmos' in audio and config.audio_posters == 1:
                                    module.add_banner(tmp_poster, atmos, poster_size)
                                elif audio == 'DTS:X' and config.audio_posters == 1:
                                    module.add_banner(tmp_poster, dtsx, poster_size)

                            elif 'Atmos' in audio:
                                ep.addLabel('Dolby Atmos', locked=False)
                            elif audio == 'DTS:X':
                                ep.addLabel('DTS:X', locked=False)
                            if hdr_banner == False:
                                try:
                                    logger.debug(hdr)
                                    if 'dolby vision' in hdr and config.hdr == 1:
                                        module.add_banner(tmp_poster, banner_dv, poster_size)
                                    elif "hdr10+" in hdr and config.hdr == 1:
                                        module.add_banner(tmp_poster, banner_hdr10, poster_size)
                                    elif hdr != "" and config.hdr == 1:
                                        module.add_banner(tmp_poster, banner_new_hdr, poster_size)
                                except:
                                    pass
                            elif 'dolby vision' in hdr:
                                ep.addLabel('Dolby Vision', locked=False)
                            elif 'hdr10+' in hdr:
                                ep.addLabel('HDR10+', locked=False)
                            elif hdr != '':
                                ep.addLabel('HDR', locked=False)
                    banner_decision(audio, hdr)
                database_decision(r)             

                if res == '4k' and config.films4kposters == 1:
                    if banner_4k == False:
                        module.add_banner(tmp_poster, banner_4k_icon, poster_size)
                    else:
                        logger.debug(ep.title+' Has banner') 


            advanced_filters = {
                'or':[
                    {'resolution':'4k'},
                    {'hdr': True}
                ]
            }
            for ep in tv.search(libtype='episode', guid=epwebhook, filters=advanced_filters):
                try:
                    logger.debug(ep.title)
                    i = ep
                    img_title = ep.grandparentTitle+"_"+ep.parentTitle+"_"+ep.title
                    resolution = ep.media[0].videoResolution
                    title = ep.title
                    logger.info(img_title)
                    guid = str(ep.guid)
                    guids = str(ep.guids)
                    size = ep.media[0].parts[0].size
                    res = ep.media[0].videoResolution 
                    hdr = module.get_plex_hdr(ep, plex)
                    height = 720
                    width = 1280
                    if 'plex://' in guid:
                        tmp_poster = re.sub('plex://episode/', '/tmp/', guid)+'.png'     
                    elif 'local://' in guid:
                        tmp_poster = re.sub('local://', '/tmp/', guid)+'.png'   

                    if (res == '4k' or hdr != 'none'):
                        r = ep_table.query.filter(ep_table.guid == guid).all()
                        if poster == "":
                            tmp_poster = module.get_poster(i, tmp_poster, title, b_dir, height, width, r)
                            tmp_poster = tmp_poster[0]
                            blurred = False
                        else:
                            blurred = True
                            tmp_poster = poster
                        print(tmp_poster)
                        table = ep_table
                        g = [s for s in tv.search(libtype='show', guid=i.grandparentGuid)]
                        g = str(g[0].guids)
                        logger.debug(g)
                        if 'plex://' in guid:
                            bname = re.sub('plex://episode/', '', guid)
                        else:
                            bname = re.sub('local://', '', guid)
                        banner_file = '/config/backup/tv/bannered_episodes/'+bname+'.png'
                        try:
                            if r[0].checked == 1:
                                logger.info(ep.title+' has been checked, checking to see if the file has changed')
                                if str(r[0].size) == str(size):
                                        logger.info(title+' has been processed and the file has not changed, skiping scan')
                                        new_poster = module.check_for_new_poster(tmp_poster, r, ep, table, db)
                                        if new_poster != 'False':
                                            decision_tree(tmp_poster)
                                            r = ep_table.query.filter(ep_table.guid == guid).all()                               
                                            module.upload_poster(tmp_poster, title, db, r, table, i, banner_file)
                                else:
                                    decision_tree(tmp_poster)
                                    r = ep_table.query.filter(ep_table.guid == guid).all()                          
                                    module.upload_poster(tmp_poster, title, db, r, table, i, banner_file)
                            else:
                                new_poster = module.check_for_new_poster(tmp_poster, r, ep, table, db)
                                if new_poster == 'False':
                                    decision_tree(tmp_poster)
                                    r = ep_table.query.filter(ep_table.guid == guid).all()
                                    module.upload_poster(tmp_poster, title, db, r, table, i, banner_file)



                        except IndexError: 
                            new_poster = module.check_for_new_poster(tmp_poster, r, ep, table, db)
                            if new_poster != 'False':
                                decision_tree(tmp_poster)
                                r = ep_table.query.filter(ep_table.guid == guid).all()
                                module.upload_poster(tmp_poster, title, db, r, table, i, banner_file)
                        logger.debug(tmp_poster)
                        rechk_banners = module.check_tv_banners(i, tmp_poster, img_title)
                        logger.debug('Rechecked banners: '+str(rechk_banners))
                        if (True in rechk_banners and config.backup == 1):
                            module.add_bannered_poster_to_db(tmp_poster, db, title, table, guid, banner_file)
                        try:
                            os.remove(tmp_poster)
                        except:
                            pass
                        try:
                            logger.info("Season Poster")
                            pguid = ep.parentGuid
                            rs = season_table.query.filter(season_table.guid == pguid).all()
                            if 'plex://' in guid:
                                st = re.sub('plex://season/', '', pguid)
                            else:
                                st = re.sub('local://', '', pguid)
                            season_poster = re.sub(' ','_', '/tmp/'+st+'_poster.png')
                            logger.debug(season_poster)
                            season_poster = module.get_season_poster(ep, season_poster, config)    
                            new_poster = module.check_for_new_poster(season_poster, rs, i, table, db)
                            size = (2000, 3000)
                            s_banners = module.check_banners(season_poster, size)
                            logger.debug('Season poster banners: '+str(s_banners))
                            logger.debug('Season poster: '+str(new_poster))
                            if ('True' in s_banners or new_poster != 'True'):
                                logger.info('Skipping season poster')
                            else:
                                s_bak = '/config/backup/tv/seasons/'+st+'.png'
                                for b in str(s_banners):
                                    banner_index = b.find('True')
                                if (banner_index < 0):
                                    shutil.copy(season_poster, s_bak)
                                    if os.path.exists(s_bak) != True:
                                        raise Exception("Season poster has not copied")
                                module.season_decision_tree(config, s_banners, ep, hdr, res, season_poster)
                                banner_file = '/config/backup/tv/bannered_seasons/'+st+'.png'
                                s_banners = module.check_banners(season_poster, size)
                                shutil.copy(season_poster, banner_file)
                                if os.path.exists(banner_file) != True:
                                    raise Exception("Season poster has not copied")
                                title = ep.grandparentTitle
                                table = season_table
                                module.add_season_to_db(db, title, table, pguid, banner_file, s_bak) 
                                #db.session.close()                       
                                for s in tv.search(guid=pguid, libtype='season'):
                                    #r = season_table.query.filter(season_table.guid == pguid).all()
                                    s.uploadPoster(filepath=season_poster)
                                    #module.upload_poster(season_poster, title, db, rs, table, s, banner_file)
                            #module.remove_tmp_files(season_poster)
                        except Exception as e:
                            logger.error("Season poster Error: "+repr(e))
                            pass
                except Exception as e:
                    logger.error(i.title+ ' '+repr(e))
            #module.clear_old_posters()  
            logger.info("tv Poster Script has finished")
            
        tvlib = config.tvlibrary

            
        if not tvlib or not tvlib.strip():

            
            return []

            
        lib = tvlib.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                for l in range(n):
                    tv = plex.library.section(lib[l])
                    run_script()
            except IndexError:
                pass        
    
def restore_episodes_from_database(app, b_dir):
    with app.app_context():    
        from app.models import Plex, ep_table
        from app import db, module
        from tmdbv3api import TMDb, Search, Movie, Discover, TV, Episode
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        tv = plex.library.section(config.tvlibrary)
        tmdb = TMDb()
        poster_url_base = 'https://www.themoviedb.org/t/p/original'
        search = Search()
        movie = Movie()
        tmdbtv = Episode()
        discover = Discover()
        tmdb.api_key = config.tmdb_api
        b_dir = b_dir
        height = 720
        width = 1280
        def run_script():
            def get_poster(poster):
                req = requests.get(poster_url_base+poster, stream=True)
                if req.status_code == 200:
                    logger.debug(b_file)
                    with open(b_file, 'wb') as f:
                        for chunk in req:
                            f.write(chunk)
                        #shutil.copyfileobj(req.raw, f)
                        i.uploadPoster(filepath=b_file)
            def restore_tmdb(g):
                logger.info("RESTORE: restoring posters from TheMovieDb")
                tmdb_search = ''
                if g == '':
                    if i.grandparentTitle == '':
                        tmdb_search = tmdbtv.details(name=i.parentTitle, episode_num=episode, season_num=season)
                    else:
                        tmdb_search = tmdbtv.details(name=i.grandparentTitle, episode_num=episode, season_num=season)
                else:
                    tmdb_search = tmdbtv.details(tv_id=g, episode_num=episode, season_num=season)
                #return tmdb_search
                try:
                    #tmdb_poster = restore_tmdb(g)
                    poster = tmdb_search.still_path
                    get_poster(poster) 
                except TypeError:
                    logger.info("RESTORE: "+i.title+" This poster could not be found on TheMoviedb")
                pass
            logger.info('Restoring TV Posters')
            advanced_filters = {
                'or': [
                    {'hdr':'True'},
                    {'resolution':'4k'}
                ]
            }
            for i in tv.search(libtype='episode', filters=advanced_filters, sort="titleSort:desc"):
                img_title = i.grandparentTitle+"_"+i.parentTitle+"_"+i.title
                g = [s for s in tv.search(libtype='show', guid=i.grandparentGuid)]
                g = str(g[0].guids)
                title = i.title
                guid = str(i.guid)

                season = str(i.parentIndex)
                episode = str(i.index)
                r = ep_table.query.filter(ep_table.guid == guid).all()
                resolution = i.media[0].videoResolution
                hdr = module.get_plex_hdr(i, plex)
                if r:
                    if 'bannered_episodes' in b_dir:
                        logger.info('restoring '+i.title+"'s bannered poster")
                        b_file = r[0].bannered_poster 
                        b_file = re.sub('static', '/config', b_file)
                        if b_file:
                            i.uploadPoster(filepath=b_file)
                    else:
                        if (resolution == '4k' or hdr != 'None'):
                            try:
                                b_file = r[0].poster 
                                b_file = re.sub('static', '/config', b_file)
                                if b_file:
                                    logger.debug(b_file)
                                    banners = module.check_tv_banners(i, b_file, img_title)
                                    logger.debug(banners)
                                    if True not in banners:
                                        logger.debug('No banners detected')
                                        i.uploadPoster(filepath=b_file)
                                    else:
                                        logger.debug('Banners detected')
                                        g = module.get_tmdb_guid(g)
                                        logger.debug(g)
                                        restore_tmdb(g)
                                else:
                                    b_file = b_dir+''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))+'.png'
                                    g = module.get_tmdb_guid(g)
                                    restore_tmdb(g)
                                row = r[0].id
                                film = ep_table.query.get(row)
                                film.checked = '0'
                                film.blurred = '0'
                                db.session.commit()
                            except (TypeError, IndexError, FileNotFoundError) as e:
                                logger.error('Restore from db: '+repr(e))  
                else:
                    logger.debug('file not in database')
                    b_file = b_dir+''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))+'.png'
                    logger.debug('filename = '+str(b_file))
                    if 'tmdb' in g:
                        g = module.get_tmdb_guid(g)
                        restore_tmdb(g)
                    else:
                        restore_tmdb('')

            logger.info('Finished restoring TV Posters')
            
        tvlib = config.tvlibrary

            
        if not tvlib or not tvlib.strip():

            
            return []

            
        lib = tvlib.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(10):
                        films = plex.library.section(lib[l])
                        run_script()
            except IndexError:
                pass            

def restore_episode_from_database(app, var):
    with app.app_context():    
        from app.models import Plex, ep_table
        from app import db, module
        from tmdbv3api import TMDb, Search, Movie, Discover, TV, Episode
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        tmdb = TMDb()
        poster_url_base = 'https://www.themoviedb.org/t/p/original'
        search = Search()
        movie = Movie()
        tmdbtv = Episode()
        discover = Discover()
        tmdb.api_key = config.tmdb_api
        b_dir = '/config/backup/tv/episodes/'
        def run_script():

            def restore_tmdb(g, b_file):
                logger.info("RESTORE: restoring posters from TheMovieDb")
                if g == '':
                    tmdb_show= TV()
                    show = tmdb_show.search(i.grandparentTitle)
                    for s in show:
                        tmdb_search = tmdbtv.details(tv_id=s.id, episode_num=episode, season_num=season)
                logger.debug(tmdb_search.still_path)
                def get_poster(poster):
                    req = requests.get(poster_url_base+poster, stream=True)
                    if req.status_code == 200:
                        logger.debug(b_file)
                        with open(b_file, 'wb') as f:
                            for chunk in req:
                                f.write(chunk)                        
                            #shutil.copyfileobj(req.raw, f)
                            i.uploadPoster(filepath=b_file)
                try:
                    poster = tmdb_search.still_path
                    get_poster(poster) 
                except TypeError:
                    logger.info("RESTORE: "+i.title+" This poster could not be found on TheMoviedb")
                    pass
            logger.info('Restoring TV Posters')
            advanced_filters = {
                'or': [
                    {'hdr':'True'},
                    {'resolution':'4k'}, 
                    #{'guid': var}
                ]
            }
            for i in tv.search(libtype='episode', filters=advanced_filters, guid=var):
                img_title = i.grandparentTitle+"_"+i.parentTitle+"_"+i.title
                g = [s for s in tv.search(libtype='show', guid=i.grandparentGuid)]
                g = str(g[0].guids)
                title = i.title
                guid = str(i.guid)
                logger.info('restoring '+title)
                logger.debug("guid= "+str(guid))
                season = str(i.parentIndex)
                episode = str(i.index)
                logger.debug(i.grandparentTitle+' '+season+' '+episode)
                r = ep_table.query.filter(ep_table.guid == guid).all()
                if r:
                    logger.debug('episode exists in database')
                    resolution = i.media[0].videoResolution
                    hdr = r[0].hdr
                    if (resolution == '4k' or hdr != 'None'):
                        try:
                            b_file = r[0].poster 
                            b_file = re.sub('static', '/config', b_file)
                            if b_file:
                                logger.debug(b_file)
                                banners = module.check_tv_banners(i, b_file, img_title)
                                logger.debug(banners)
                                if True not in banners:
                                    logger.debug('No banners detected')
                                    i.uploadPoster(filepath=b_file)
                                else:
                                    logger.debug('Banners detected')
                                    g = module.get_tmdb_guid(g)
                                    logger.debug(g)
                                    restore_tmdb(g)
                            else:
                                b_file = b_dir+''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))+'.png'
                                g = module.get_tmdb_guid(g)
                                restore_tmdb(g)
                            row = r[0].id
                            film = ep_table.query.get(row)
                            film.checked = '0'
                            film.blurred = '0'
                            db.session.commit()
                        except (TypeError, IndexError, FileNotFoundError) as e:
                            logger.error('Restore from db: '+repr(e))  
                else:
                    logger.debug('file not in database')
                    b_file = b_dir+''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))+'.png'
                    logger.debug('filename = '+str(b_file))
                    if 'tmdb' in g:
                        g = module.get_tmdb_guid(g)
                        restore_tmdb(g, b_file)
                    else:
                        restore_tmdb('', b_file)
            logger.info('Finished restoring TV Posters')
            
        tvlib = config.tvlibrary

            
        if not tvlib or not tvlib.strip():

            
            return []

            
        lib = tvlib.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(n):
                        tv = plex.library.section(lib[l])
                        run_script()
            except IndexError:
                pass    

def posters3d(app): 
    with app.app_context():
        from app.models import Plex
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        tmdb.api_key = config.tmdb_api

        plex = PlexServer(config.plexurl, config.token)
        films = plex.library.section(config.library3d)
        if config.posters3d == 1:


            banner_3d = Image.open("app/img/3D-Template.png")
            mini_3d_banner = Image.open("app/img/3D-mini-Template.png")

            chk_banner = Image.open("app/img/chk_3d_wide.png")
            chk_mini_banner = Image.open("app/img/chk-3D-mini.png")

            size = (911,1367)
            box= (0,0,911,100)
            mini_box = (0,0,301,268)

            logger.info("3D Posters: 3D poster script starting now.")  

            def check_for_mini():
                background = Image.open('/tmp/poster.png')
                background = background.resize(size,Image.ANTIALIAS)
                backgroundchk = background.crop(mini_box)
                hash0 = imagehash.average_hash(backgroundchk)
                hash1 = imagehash.average_hash(chk_mini_banner)
                cutoff= 15
                if hash0 - hash1 < cutoff:
                    logger.info('3D Posters: Mini 3D banner exists, moving on...')
                elif config.mini3d == 1:
                    add_mini_banner()
                else:
                    add_banner()       

            def check_for_banner():
                background = Image.open('/tmp/poster.png')
                background = background.resize(size,Image.ANTIALIAS)
                backgroundchk = background.crop(box)
                hash0 = imagehash.average_hash(backgroundchk)
                hash1 = imagehash.average_hash(chk_banner)
                cutoff= 5
                if hash0 - hash1 < cutoff:
                    logger.info('3D Posters: 3D banner exists, moving on...')
                else:
                    check_for_mini()  

            def add_banner():
                background = Image.open('/tmp/poster.png')
                background = background.resize(size,Image.ANTIALIAS)
                background.paste(banner_3d, (0, 0), banner_3d)
                background.save('/tmp/poster.png')
                i.uploadPoster(filepath='/tmp/poster.png')

            def add_mini_banner():
                background = Image.open('/tmp/poster.png')
                background = background.resize(size,Image.ANTIALIAS)
                background.paste(mini_3d_banner, (0, 0), mini_3d_banner)
                background.save('/tmp/poster.png')
                i.uploadPoster(filepath='/tmp/poster.png')        

            def get_poster():
                newdir = os.path.dirname(re.sub(config.plexpath, '/films', i.media[0].parts[0].file))+'/'
                backup = os.path.exists(newdir+'poster_bak.png')
                imgurl = i.posterUrl
                img = requests.get(imgurl, stream=True)
                if img.status_code == 200:
                    img.raw.decode_content = True
                    filename = "/tmp/poster.png"

                    with open(filename, 'wb') as f:
                        for chunk in img:
                            f.write(chunk)                    
                        #shutil.copyfileobj(img.raw, f)
                    if config.backup == 1: 
                        if backup == True: 
                            #open backup poster to compare it to the current poster. If it is similar enough it will skip, if it's changed then create a new backup and add the banner. 
                            poster = os.path.join(newdir, 'poster_bak.png')
                            b_check1 = Image.open(filename)
                            b_check = Image.open(poster)
                            b_hash = imagehash.average_hash(b_check)
                            b_hash1 = imagehash.average_hash(b_check1)
                            cutoff = 5
                            if b_hash - b_hash1 < cutoff:    
                                logger.info('3D Posters: Backup File Exists, Skipping')
                            else:
                                os.remove(poster)
                                logger.info('3D Posters: Creating a backup file')
                                shutil.copyfile(filename, newdir+'poster_bak.png')
                        else:        
                            logger.info('3D Posters: Creating a backup file')
                            shutil.copyfile(filename, newdir+'poster_bak.png')
                else:
                    logger.warning("3D Posters: "+films.title+" cannot find the poster for this film")   

            for i in films.search():
                i.title = unicodedata.normalize('NFD', i.title).encode('ascii', 'ignore').decode('utf8')
                logger.info(i.title)
                try:
                    get_poster()
                    check_for_banner()
                except FileNotFoundError:
                    logger.error("3D Posters: "+films.title+" The 3D poster for this film could not be created.")
                    continue
            logger.info("3D Posters: 3D Poster Script has finished.")
        else:
            logger.warning('3D Posters script is not enabled in the config so will not run')

def restore_from_database(app):
    with app.app_context():    
        from app.models import Plex, film_table
        from app import db
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        films = plex.library.section('Films')
        def convert_data(data, file_name):
            with open(file_name, 'wb') as file:
                file.write(data)

        def run_script():   
            for i in films.search():
                title = i.title
                guid = str(i.guid)
                logger.info('restoring '+title)
                logger.debug(guid)
                newdir = os.path.dirname(re.sub(config.plexpath, '/films', i.media[0].parts[0].file))+'/poster_bak.png'
                r = film_table.query.filter(film_table.guid == guid).all()
                try:
                    b_file = re.sub('static', '/config', r[0].poster)
                    i.uploadPoster(filepath=b_file)
                    row = r[0].id
                    film = film_table.query.get(row)
                    film.checked = '0'
                    db.session.commit()
                except (TypeError, IndexError, FileNotFoundError) as e:
                    logger.error(repr(e))  
            
        lib = config.filmslibrary.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(n):
                        films = plex.library.section(lib[l])
                        run_script()
            except IndexError:
                pass    

def restore_single(var):
        from app.models import Plex, film_table
        from app import db
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        def run_script():
            for i in films.search(guid=var):
                title = i.title
                guid = var
                logger.info('restoring '+title)
                logger.debug(guid)
                r = film_table.query.filter(film_table.guid == guid).all()
                try:
                    b_file = re.sub('static', '/config', r[0].poster)
                    print(b_file)
                    i.uploadPoster(filepath=b_file)
                    row = r[0].id
                    film = film_table.query.get(row)
                    film.checked = '0'
                    film.bannered_poster = ''
                    db.session.commit()
                    db.session.close()
                except (TypeError, IndexError, FileNotFoundError) as e:
                    logger.error(repr(e)) 
            
        lib = config.filmslibrary.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(n):
                        films = plex.library.section(lib[l])
                        run_script()
            except IndexError:
                pass

def restore_single_bannered(app, var):
        from app.models import Plex, film_table
        from app import db
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        msg = 'no message'
        def run_script():
            for i in films.search(guid=var):
                title = i.title
                guid = var
                logger.info('restoring '+title)
                logger.debug(guid)

                r = film_table.query.filter(film_table.guid == guid).all()
                try:
                    b_file = re.sub('static', '/config', r[0].bannered_poster)
                    print(b_file)
                    i.uploadPoster(filepath=b_file)
                    row = r[0].id
                    film = film_table.query.get(row)
                    film.checked = '1'
                    db.session.commit()
                    msg = 'Re-uploading bannered poster.'
                    return msg
                except Exception as e:
                    msg = repr(e)
                    logger.error(repr(e)) 
                    return msg
            
        lib = config.filmslibrary.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(n):
                        films = plex.library.section(lib[l])
                        msg = run_script()
            except IndexError:
                pass
        return msg

def restore_seasons(app):
    with app.app_context(): 
        from app.models import Plex, season_table
        from app import db, module
        tmdbtvs = Season()
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        def run_script():
            advanced_filters = {
                'or':[
                    {'resolution':'4k'},
                    {'hdr': True}
                ]
            }
            for i in tv.search(libtype='season'): #, filters=advanced_filters):
                title = i.title
                guid = i.guid
                logger.info('restoring '+i.parentTitle+' - '+title)
                r = season_table.query.filter(season_table.guid == guid).all()
                if r:
                    try:
                        b_file = re.sub('static', '/config', r[0].poster)
                        i.uploadPoster(filepath=b_file)
                        row = r[0].id
                        film = season_table.query.get(row)
                        film.checked = '0'
                        db.session.commit()
                    except (TypeError, IndexError, FileNotFoundError, plexapi.exceptions.BadRequest) as e:
                        logger.error(repr(e)) 
                else:
                    if config.tmdb_restore == 1:
                        try:
                            for show in tv.search(libtype='show', guid=i.parentGuid):
                                g = str(show.guids)
                                g = g[1:-1]
                                g = re.sub(r'[*?:"<>| ]',"",g)
                                g = re.sub("Guid","",g)
                                g = g.split(",")
                                f = filter(lambda a: "tmdb" in a, g)
                                g = list(f)
                                g = str(g[0])
                                gv = [v for v in g if v.isnumeric()]
                                g = "".join(gv)
                                tmdb_search = tmdbtvs.images(tv_id=g, season_num=i.index, include_image_language='en')
                                poster = tmdb_search.posters[0].file_path
                            fname = 'tmdb_poster_restore.png'
                            module.get_tmdb_poster(fname, poster)
                            i.uploadPoster(filepath=fname)
                        except Exception as e:
                            logger.error(repr(e))
                            pass
        tvlib = config.tvlibrary

        if not tvlib or not tvlib.strip():

            return []

        lib = tvlib.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(n):
                        tv = plex.library.section(lib[l])
                        run_script()
            except IndexError:
                pass

def restore_single_season(app, var):
        from app.models import Plex, season_table
        from app import db
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        def run_script():
            for i in tv.search(guid=var, libtype='season', limit=1):
                title = i.title
                guid = var
                logger.info('restoring '+title)
                logger.debug(guid)
                r = season_table.query.filter(season_table.guid == guid).all()

                try:
                    b_file = re.sub('static', '/config', r[0].poster)
                    print('poster file = '+b_file)                    
                    i.uploadPoster(filepath=b_file)
                    row = r[0].id
                    film = season_table.query.get(row)
                    film.checked = '0'
                    db.session.commit()
                except (TypeError, IndexError, FileNotFoundError) as e:
                    logger.error(repr(e)) 
        tvlib = config.tvlibrary
 
        if not tvlib or not tvlib.strip():
 
            return []
 
        lib = tvlib.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(n):
                        tv = plex.library.section(lib[l])
                        run_script()
            except IndexError:
                pass

def restore_single_bannered_season(app, var):
        from app.models import Plex, season_table
        from app import db
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        msg = 'no message'
        def run_script():
            for season in tv.search(guid=var, libtype='season'):
                title = season.title
                guid = var
                logger.info('restoring '+title)
                logger.debug(guid)
                r = season_table.query.filter(season_table.guid == guid).all()
                try:
                    b_file = re.sub('static', '/config', r[0].bannered_poster)
                    season.uploadPoster(filepath=b_file)
                    row = r[0].id
                    film = season_table.query.get(row)
                    film.checked = '1'
                    db.session.commit()
                    msg = 'Re-uploading bannered poster.'
                    return msg
                except Exception as e:
                    msg = repr(e)
                    logger.error(repr(e)) 
                    return msg
            
        tvlib = config.tvlibrary

            
        if not tvlib or not tvlib.strip():

            
            return []

            
        lib = tvlib.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                for l in range(n):
                    tv = plex.library.section(lib[l])
                    msg = run_script()
            except IndexError:
                pass
        return msg

def restore_single_bannered_episode(app, var):
        from app.models import Plex, ep_table
        from app import db
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        msg = 'no message'
        def run_script():
            for i in tv.search(guid=var, libtype='episode'):
                title = i.title
                guid = var
                logger.info('restoring '+title)
                logger.debug(guid)

                r = ep_table.query.filter(ep_table.guid == guid).all()
                try:
                    b_file = re.sub('static', '/config', r[0].bannered_poster)
                    i.uploadPoster(filepath=b_file)
                    row = r[0].id
                    film = ep_table.query.get(row)
                    film.checked = '1'
                    db.session.commit()
                    msg = 'Re-uploading bannered poster.'
                    return msg
                except Exception as e:
                    msg = repr(e)
                    logger.error(repr(e)) 
                    return msg
            
        tvlib = config.tvlibrary

            
        if not tvlib or not tvlib.strip():

            
            return []

            
        lib = tvlib.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                for l in range(n):
                    tv = plex.library.section(lib[l])
                    msg = run_script()
            except IndexError:
                pass
        return msg

def hide4k(app):
    with app.app_context(): 
        from app.models import Plex
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        tmdb.api_key = config.tmdb_api
        def run_script():

            if config.hide4k == 1:


                logger.info("Hide-4K: Hide 4k films script starting now")


                added = films.search(resolution='4k', sort='addedAt')
                b = films.search('untranscodable', sort='addedAt')
                def add_untranscodable():
                    for movie in added:
                        resolutions = {m.videoResolution for m in movie.media}
                        if len(resolutions) < 2 and '4k' in resolutions:
                            if config.transcode == 0:
                                movie.addLabel('Untranscodable')   
                                logger.info("Hide-4K: "+movie.title+' has only 4k avaialble, setting untranscodable' )
                            elif config.transcode == 1:
                                logger.info('Hide-4K: Sending '+ movie.title+ ' to be transcoded')
                                movie.optimize(deviceProfile="Android", videoQuality=10)
                def remove_untranscodable():
                    for movie in b:
                        resolutions = {m.videoResolution for m in movie.media}
                        if len(resolutions) > 1 and '4k' in resolutions:
                            movie.removeLabel('Untranscodable')
                            logger.info("Hide-4K: "+movie.title+ ' removing untranscodable label')
                add_untranscodable()
                remove_untranscodable()
                logger.info("Hide-4K: Hide 4K Script has finished.")
            else:
                logger.warning('Hide 4K films is not enabled in the config so will not run')  
            

        lib = config.filmslibrary.split(',')
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(n):
                        films = plex.library.section(lib[l])
                        run_script()
            except IndexError:
                pass               

def fresh_hdr_posters(app):
    with app.app_context(): 
        from app.models import Plex
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        tmdb.api_key = config.tmdb_api

        plex = PlexServer(config.plexurl, config.token)
        films = plex.library.section(config.filmslibrary)
        def continue_fresh_posters():
            logger.info("Restore-posters: Restore backup posters starting now") 
            for i in films.search(hdr='true'):
                i.title = unicodedata.normalize('NFD', i.title).encode('ascii', 'ignore').decode('utf8')  
                def restore_tmdb():
                    g = str(i.guids[1])
                    g = re.sub(">", "", g.split("//")[1])
                    tmdb_search = movie.details(movie_id=g)
                    tmdb_search = search.movies({"query": i.title, "year": i.year})
                    logger.info(i.title)
                    def get_poster(poster):
                        r = requests.get(poster_url_base+poster, stream=True)
                        if r.status_code == 200:
                            #r.raw.decode_content = True
                            with open('tmdb_poster_restore.png', 'wb') as f:
                                for chunk in r:
                                    f.write(chunk)                            
                                #shutil.copyfileobj(r.raw, f)
                                i.uploadPoster(filepath='tmdb_poster_restore.png')
                                os.remove('tmdb_poster_restore.png')
                                logger.info(i.title+' Restored from TheMovieDb')
                    try:
                        poster = tmdb_search.poster_path
                        get_poster(poster) 
                    except TypeError:
                        logger.warning("RESTORE: "+i.title+" This poster could not be found on TheMoviedb")
                        pass                        
                    
                newdir = os.path.dirname(re.sub(config.plexpath, '/films', i.media[0].parts[0].file))+'/'
                backup = os.path.exists(newdir+'poster_bak.png') 
                if backup == True:
                    poster = newdir+'poster_bak.png'
                    logger.info(i.title+ ' Restored from Local files')
                    i.uploadPoster(filepath=poster)
                    os.remove(poster)
                elif config.tmdb_restore == 1 and backup == False:
                    restore_tmdb()
            posters4k(app, '')
        def check_connection():
            try:
                plex = PlexServer(config.plexurl, config.token)
            except requests.exceptions.ConnectionError as e:
                logger.error(e)
                logger.error('Cannot connect to your plex server. Please double check your config is correct.')
            else:
                continue_fresh_posters()
        check_connection()

def autocollections(app):
    with app.app_context(): 
        logger.info('Autocollections has started')
        from app.models import Plex
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        tmdb.api_key = config.tmdb_api

        plex = PlexServer(config.plexurl, config.token)

        def run_script():
            def popular():
                p_collection = []
                for i in range(3):
                    i += 1
                    popular = discover.discover_movies({
                        "page": i,
                        "with_original_language": "en"
                    })
                    for p in popular:
                        for p in popular:
                            title= p.title
                            y = p.release_date.split("-")
                            p_collection.append((p.title, y[0]))
                            in_library = films.search(title=title, year=y[0])
                            for i in in_library:
                                if len(in_library) != 0:
                                    i.addCollection('Popular')
                m_collection = [(m.title, m.year) for m in films.search(collection='Popular')]
                not_in_collection = list(set(m_collection) - set(p_collection))
                for m in films.search(collection='Popular'):
                    if m.title in not_in_collection:
                        m.removeCollection('Popular')
                logger.info("Popular Collection has finished")        
            def top_rated():
                tr_collection = []
                for i in range(3):
                    i += 1
                    top_rated = movie.top_rated({
                        "page": i,
                    })

                    for x in top_rated:
                        title= x.title
                        y = x.release_date.split("-")
                        tr_collection.append(x.title)
                        in_library = films.search(title=title, year=y[0])
                        for i in in_library:
                            if len(in_library) != 0:
                                i.addCollection('Top Rated')
                trm_collection = [m.title for m in films.search(collection='Top Rated')]
                not_in_collection = list(set(trm_collection) - set(tr_collection))
                for m in films.search(collection='Top Rated'):
                    if m.title in not_in_collection:
                        m.removeCollection('Top Rated')
                logger.info("Top Rated Collection has finished")
            def recommended():
                if config.tautulli_api != '':
                    try:
                        tautulli_api = RawAPI(base_url=config.tautulli_server, api_key=config.tautulli_api)
                        i=tautulli_api.get_home_stats(stats_type='plays', stat_id='top_movies')
                        x = json.dumps(tautulli_api.get_home_stats(stats_type='plays', stat_id='top_movies'))
                        i=json.loads(x)
                        top_watched=i["rows"][0]["title"]
                        tw_year=i["rows"][0]["year"]
                        logger.debug('Top watched film is: '+top_watched)
                        a = search.movies({ "query": top_watched, "year": tw_year })
                        def get_id():
                            for b in a:
                                i = b.id
                                return i
                        i = get_id()
                        rec = movie.recommendations(movie_id=i)
                        for r in rec:
                            title = r.title
                            logger.debug(title)
                            y = r.release_date.split("-")
                            in_library = films.search(title=title, year=y[0])
                            for i in in_library:
                                if len(in_library) != 0:
                                    i.addCollection('Recommended')
                        rm_collection = [m.title for m in films.search(collection='Recommended')]
                        r_collection = [r.title for r in rec]
                        not_in_collection = list(set(rm_collection) - set(r_collection))
                        for m in films.search(collection='Recommended'):
                            if m.title in not_in_collection:
                                m.removeCollection('Recommended')
                    except requests.exceptions.ConnectionError as e:
                        pass
                logger.info("Reccomended Collection has finished")
            def MCU():
                try:
                    collection = 'Marvel Cinematic Universe'
                    c = films.collection(title=collection)
                    if c.smart == False:
                        imgurl = c.posterUrl
                        img = requests.get(imgurl, stream=True)
                        filename = "/tmp/poster.png"
                        if img.status_code == 200:
                            img.raw.decode_content = True
                            with open(filename, 'wb') as f:
                                for chunk in img:
                                    f.write(chunk)                            
                                #shutil.copyfileobj(img.raw, f)
                        c.delete()
                        plex.createCollection(section=config.filmslibrary, title=collection, smart=True, filters={'studio': 'Marvel Studios'})
                        d = films.collection(collection)
                        d.uploadPoster(filepath='/tmp/poster.png')
                    if config.default_poster == 1:
                        c.uploadPoster(filepath='app/img/collections/mcu_poster.png')
                except plexapi.exceptions.NotFound:
                    plex.createCollection(section=config.filmslibrary, title=collection, smart=True, filters={'studio': 'Marvel Studios'})
                    d = films.collection(collection)
                    if config.default_poster == 1:
                        d.uploadPoster(filepath='app/img/collections/mcu_poster.png') 
                logger.info("MCU Collection has finished")
            def pixar():
                try:
                    collection = 'Pixar'
                    c = films.collection(title=collection)
                    if c.smart == False:
                        imgurl = c.posterUrl
                        img = requests.get(imgurl, stream=True)
                        filename = "/tmp/poster.png"
                        if img.status_code == 200:
                            img.raw.decode_content = True
                            with open(filename, 'wb') as f:
                                for chunk in img:
                                    f.write(chunk)                            
                                #shutil.copyfileobj(img.raw, f)
                        c.delete()
                        plex.createCollection(section=config.filmslibrary, title=collection, smart=True, filters={'studio': collection})
                        d = films.collection(collection)
                        d.uploadPoster(filepath='/tmp/poster.png')
                    if config.default_poster == 1:
                        c.uploadPoster(filepath='app/img/collections/pixar_poster.jpeg')                    
                except plexapi.exceptions.NotFound:
                    plex.createCollection(section=config.filmslibrary, title=collection, smart=True, filters={'studio': collection})
                    d = films.collection(collection)
                    if config.default_poster == 1:
                        d.uploadPoster(filepath='app/img/collections/pixar_poster.jpeg')
                logger.info("Pixar Collection has finished")
            def disney():
                try:
                    collection = 'Disney'
                    c = films.collection(title=collection)
                    if c.smart == False:
                        imgurl = c.posterUrl
                        img = requests.get(imgurl, stream=True)
                        filename = "/tmp/poster.png"
                        if img.status_code == 200:
                            img.raw.decode_content = True
                            with open(filename, 'wb') as f:
                                for chunk in img:
                                    f.write(chunk)                             
                                #shutil.copyfileobj(img.raw, f)
                        c.delete()
                        plex.createCollection(section=config.filmslibrary, title=collection, smart=True, filters={'studio': collection})
                        d = films.collection(collection)
                        d.uploadPoster(filepath='/tmp/poster.png')
                    if config.default_poster == 1:
                        c.uploadPoster(filepath='app/img/collections/disney_poster.jpeg') 
                except plexapi.exceptions.NotFound:
                    plex.createCollection(section=config.filmslibrary, title=collection, smart=True, filters={'studio': collection})
                    d = films.collection(collection)
                    if config.default_poster == 1:
                        d.uploadPoster(filepath='app/img/collections/disney_poster.jpeg')
                logger.info("Disney Collection has finished")
            def audio_collections():
                def atmos():
                    collection = 'Dolby Atmos'
                    try:
                        c = films.collection(title=collection)
                    except plexapi.exceptions.NotFound:
                        plex.createCollection(section=config.filmslibrary, title=collection, smart=True, filters={'label': collection})
                        d = films.collection(collection)
                        if config.default_poster == 1:
                            d.uploadPoster(filepath='app/img/collections/Atmos_Poster.png') 
                    logger.info("Dolby Atmos Collection has finished") 
                def dtsx():
                    collection = 'DTS:X'
                    try:
                        c = films.collection(title=collection)
                    except plexapi.exceptions.NotFound:
                        plex.createCollection(section=config.filmslibrary, title=collection, smart=True, filters={'label': collection})
                        d = films.collection(collection)
                        if config.default_poster == 1:
                            d.uploadPoster(filepath='app/img/collections/DTSX_Poster.png') 
                    logger.info("DTS:X Collection has finished")
                atmos()
                dtsx()
            def HDR_collections():
                def dolby_vision():
                    collection = 'Dolby Vision'
                    try:
                        c = films.collection(title=collection)
                    except plexapi.exceptions.NotFound:
                        plex.createCollection(section=config.filmslibrary, title=collection, smart=True, filters={'label': collection})
                        d = films.collection(collection)
                        if config.default_poster == 1:
                            d.uploadPoster(filepath='app/img/collections/dolby_vision_Poster.png') 
                    logger.info("Dolby Vision Collection has finished")
                dolby_vision() 
            if config.autocollections == 1:
                audio_collections()
                HDR_collections()
            if config.disney == 1:
                disney()
            if config.pixar == 1:
                pixar()
            if config.mcu_collection == 1:
                MCU()                
            if config.tr_r_p_collection == 1:
                popular()
                top_rated()
                recommended() 
            logger.info("Auto Collections has finished")
        lib = config.filmslibrary.split(',')
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(n):
                        films = plex.library.section(lib[l])
                        run_script()
            except IndexError:
                pass        

def test_script(app):
    with app.app_context(): 
        from app.models import Plex, film_table
        from app import db
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        films = plex.library.section('films')

        for i in films.search(resolution='4k', hdr=False):
            guid = str(i.guid)
            r = film_table.query.filter(film_table.guid == guid).all()
            if 'DTS:X' not in r[0].audio and 'Atmos' not in r[0].audio:
                print(i.title)
                row = r[0].id
                film = film_table.query.get(row)
                film.checked = '0'
                db.session.commit()

def fill_database(app):
    with app.app_context(): 
        from app.models import Plex, film_table
        from app import db
        from app import module
        config = Plex.query.filter()
        plex = PlexServer(config.plexurl, config.token)
        tmdb.api_key = config.tmdb_api
        def run_script():
            def main():
                def restore_tmdb():
                    logger.info("RESTORE: restoring posters from TheMovieDb")
                    def get_tmdb_guid():
                        g = str(i.guids)
                        g = g[1:-1]
                        g = re.sub(r'[*?:"<>| ]',"",g)
                        g = re.sub("Guid","",g)
                        g = g.split(",")
                        f = filter(lambda a: "tmdb" in a, g)
                        g = list(f)
                        g = str(g[0])
                        gv = [v for v in g if v.isnumeric()]
                        g = "".join(gv)
                        return g
                    g = get_tmdb_guid()
                    tmdb_search = movie.details(movie_id=g)
                    logger.info(i.title)
                    def get_poster(poster):
                        r = requests.get(poster_url_base+poster, stream=True)
                        if r.status_code == 200:
                            #r.raw.decode_content = True
                            with open('tmdb_poster_restore.png', 'wb') as f:
                                for chunk in r:
                                    f.write(chunk)                             
                                #shutil.copyfileobj(r.raw, f)
                                tmdb_poster = 'tmdb_poster_restore.png'
                                return tmdb_poster
                    try:
                        poster = tmdb_search.poster_path
                        tmdb_poster = get_poster(poster) 
                        return tmdb_poster
                    except TypeError:
                        logger.info("RESTORE: "+i.title+" This poster could not be found on TheMoviedb")
                        pass                            
                def scan_files(config, i, plex):
                        try:
                            logger.debug('Scanning '+i.title)
                            file = re.sub(config.plexpath, '/films', i.media[0].parts[0].file)
                            m = MediaInfo.parse(file, output='JSON')
                            x = json.loads(m)
                            hdr_version = module.get_plex_hdr(i, plex)
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
                                                pass
                            audio = ""
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
                            return audio, hdr_version
                        except FileNotFoundError as e:
                            logger.error(repr(e))

                def insert_intoTable(hdr, audio, tmp_poster):
                    logger.debug('Adding '+i.title+' to database') 
                    logger.debug(i.title+' '+hdr+' '+audio)  
                    b_file = backup_poster(tmp_poster)
                    b_file = re.sub('/config', 'static', b_file)
                    logger.debug(tmp_poster)
                    if True in banners:
                        b_poster = '/config/backup/bannered_films/'+t+'.png'
                        shutil.copy(tmp_poster, b_poster)
                        bannered_poster = re.sub('/config', 'static', b_poster)
                    else:
                        bannered_poster = ''
                    if not r:
                        film = film_table(title=title, guid=guid, guids=guids, size=size, res=res, hdr=hdr, audio=audio, poster=b_file, bannered_poster=bannered_poster)
                        db.session.add(film)   
                        db.session.commit()
                    elif r[0].size != size:
                        updateTable(hdr, audio, tmp_poster)

                def updateTable(hdr, audio, tmp_poster):
                    if config.manualplexpath == 1:
                        newdir = os.path.dirname(re.sub(config.manualplexpathfield, '/films', i.media[0].parts[0].file))+'/'
                    else:
                        newdir = os.path.dirname(re.sub(config.plexpath, '/films', i.media[0].parts[0].file))+'/'
                    backup = os.path.exists(newdir+'poster_bak.png')
                    logger.debug('Updating '+i.title+' in database')
                    logger.debug(i.title+' '+hdr+' '+audio)   
                    b_file = backup_poster(tmp_poster)
                    #b_file = re.sub('/config', 'static', pblob)
                    if backup == True or True not in banners:
                        row = r[0].id
                        film = film_table.query.get(row)
                        film.size = size
                        film.res = res
                        film.hdr = hdr
                        film.audio = audio
                        film.poster = b_file
                        db.session.commit()

                def backup_poster(tmp_poster):
                    if config.manualplexpath == 1:
                        newdir = os.path.dirname(re.sub(config.manualplexpathfield, '/films', i.media[0].parts[0].file))+'/'
                    else:
                        newdir = os.path.dirname(re.sub(config.plexpath, '/films', i.media[0].parts[0].file))+'/'
                    old_backup = os.path.exists(newdir+'poster_bak.png')
                    b_file = ''
                    if old_backup == True:
                        logger.debug('Backup file found')
                        bak_file = newdir+'poster_bak.png'
                        logger.debug(bak_file)
                        b_file = b_dir+'films/'+t+'.png'
                        logger.debug(b_file)
                        shutil.copy(bak_file, b_file)

                    elif True not in banners:
                        logger.debug(i.title+" No banners detected so adding backup file to database")
                        b_file = b_dir+'films/'+t+'.png'
                        shutil.copy(tmp_poster, b_file)
                    elif (True in banners and old_backup == False and config.tmdb_restore == 1):
                        b_file = b_dir+'films/'+t+'.png'
                        tmdb_poster = restore_tmdb()
                        shutil.copy(tmdb_poster, b_file)
                    return b_file

                def check_banners(tmp_poster):

                    banner_4k = Image.open("app/img/4K-Template.png")
                    mini_4k_banner = Image.open("app/img/4K-mini-Template.png")
                    banner_dv = Image.open("app/img/dolby_vision.png")
                    banner_hdr10 = Image.open("app/img/hdr10.png")

                    banner_new_hdr = Image.open("app/img/hdr.png")
                    atmos = Image.open("app/img/atmos.png")
                    dtsx = Image.open("app/img/dtsx.png")

                    size = (2000,3000)
                    bannerbox= (0,0,2000,246)
                    mini_box = (0,0,350,275)
                    hdr_box = (0,1342,493,1608)
                    a_box = (0,1608,493,1766)

                    cutoff = 10 

                    logger.debug(i.title+' Checking for Banners')
                    try:
                        background = Image.open(tmp_poster)
                        background = background.resize(size,Image.ANTIALIAS)
                    except OSError as e:
                        logger.error(e)
                        ImageFile.LOAD_TRUNCATED_IMAGES = True
                        background = background.resize(size,Image.ANTIALIAS)
                        ImageFile.LOAD_TRUNCATED_IMAGES = False

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

                    if poster_banner_hash - chk_banner_hash < cutoff:
                        wide_banner = True
                    if poster_mini_hash - chk_mini_banner_hash < cutoff:
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
                    background.save(tmp_poster)
                    return wide_banner, mini_banner, audio_banner, hdr_banner, old_hdr

                def get_plex_hdr(i, plex):
                    ekey = i.key
                    m = plex.fetchItems(ekey)
                    for m in m:
                        try:
                            if m.media[0].parts[0].streams[0].DOVIPresent == True:
                                hdr_version='Dolby Vision'
                                i.addLabel('Dolby Vision', locked=False)
                            elif 'HDR' in m.media[0].parts[0].streams[0].displayTitle:
                                hdr_version='HDR'
                                i.addLabel('HDR', locked=False)
                            else:
                                hdr_version = 'None'
                            return hdr_version
                        except IndexError:
                            pass

                def get_poster():
                    logger.debug(i.title+' Getting poster')
                    imgurl = plex.transcodeImage(
                        i.thumbUrl,
                        height=3000,
                        width=2000,
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
                                #shutil.copyfileobj(img.raw, f)
                            return tmp_poster 
                        else:
                            logger.info("4k Posters: "+films.title+ 'cannot find the poster for this film')
                    except OSError as e:
                        logger.error(e)

                t = re.sub('plex://movie/', '', guid)
                tmp_poster = re.sub(' ','_', '/tmp/'+t+'.png')
                tmp_poster = get_poster()
                poster_size = (2000,3000)
                banners = module.check_banners(tmp_poster, poster_size)
                logger.debug(banners)
                if True in banners:
                    logger.info('Migrating: '+i.title)
                    if config.skip_media_info == 1:
                        hdr = module.get_plex_hdr(i, plex)
                        audio = ''
                        insert_intoTable(hdr, audio, tmp_poster)
                    else:
                        try:
                            scan = module.scan_files(config, i, plex)
                            audio = scan[0]
                            hdr = str.lower(scan[1])
                        except Exception as e:
                            logger.error(repr(e))
                            logger.error('Can not scan '+title+': Please check your permissions. Using Plex Metadata')
                            hdr = module.get_plex_hdr(i, plex)
                            audio = ''
                        insert_intoTable(hdr, audio, tmp_poster)  
                
            for i in films.search():
                logger.debug(i.title)
                title = i.title
                guid = str(i.guid)
                guids = str(i.guids)
                size = i.media[0].parts[0].size
                res = i.media[0].videoResolution
                r = film_table.query.filter(film_table.guid == guid).all()
                if not r:
                    main()
                else:
                    if r[0].size != size:
                        logger.info(title+' is already in the database')
                    else:
                        main()
            try:
                row = config.id
                plex_utills = Plex.query.get(row)
                plex_utills.migrated = '1'
                db.session.commit()
            except Exception as e:
                logger.error(repr(e))
                db.session.rollback()
            finally:
                db.session.close()
            logger.debug('Database has been seeded')
            try:
                os.remove('tmdb_poster_restore.png')
            except:
                pass
        lib = config.filmslibrary.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                for l in range(n):
                    films = plex.library.section(lib[l])
                    run_script()
            except IndexError:
                pass 

def add_labels(app):
    with app.app_context(): 

        from app.models import Plex, film_table
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        def run_script():
            logger.info('Adding Film Labels')
            for i in films.search(sort='random'):
                guid = str(i.guid)
                r = film_table.query.filter(film_table.guid == guid)
                logger.debug(i.title+" "+r[0].audio+" "+r[0].hdr)
                if 'Dolby Atmos' in r[0].audio:
                    i.addLabel('Dolby Atmos', locked=False)  
                elif 'DTS:X' in r[0].audio:
                    i.addLabel('DTS:X', locked=False)                
                if 'Dolby Vision' in r[0].hdr:
                    i.addLabel('Dolby Vision', locked=False) 
                elif 'HDR10+' in r[0].hdr:
                    i.addLabel('HDR10+', locked=False)
                elif 'HDR' in r[0].hdr:
                    i.addLabel('HDR', locked=False)
            logger.info('Labels Added')
        lib = config.filmslibrary.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(n):
                        films = plex.library.section(lib[l])
                        run_script()
            except IndexError:
                pass 

def maintenance(app):
    with app.app_context():
        from app.models import Plex, film_table, ep_table, season_table
        from app import db, module
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        try:

            plex.runButlerTask('CleanOldCacheFiles')

            logger.info("Butler task 'CleanOldCacheFiles' queued successfully")

        except Exception as e:

            if "202" in str(e) or "accepted" in str(e).lower():

                logger.info("Butler task 'CleanOldCacheFiles' accepted by Plex (HTTP 202)")

            else:

                logger.warning(f"Butler task 'CleanOldCacheFiles' failed: {e}")
        try:

            plex.runButlerTask('CleanOldBundles')

            logger.info("Butler task 'CleanOldBundles' queued successfully")

        except Exception as e:

            if "202" in str(e) or "accepted" in str(e).lower():

                logger.info("Butler task 'CleanOldBundles' accepted by Plex (HTTP 202)")

            else:

                logger.warning(f"Butler task 'CleanOldBundles' failed: {e}")
        
        def clean_database(table, library):
            r = table.query.all()
            for i in r:
                f = library.search(guid=i.guid)
                if f:
                    pass
                    #print(f.title+" exists")
                else:
                    logger.info("Removing "+i.title+" from database")
                    poster = re.sub("static", "/config", i.poster)
                    b_poster = re.sub("static", "/config", i.bannered_poster)
                    try:
                        os.remove(poster)
                    except: pass
                    try:
                        os.remove(b_poster)
                    except: pass
                    try:
                        row = table.query.get(i.id)
                        db.session.delete(row)
                        db.session.commit()
                    except: 
                        db.session.rollback()
        
        # Clean film database
        lib = config.filmslibrary.split(',')
        n = len(lib)
        if n <= 2:
            try:
                for l in range(n):
                    films = plex.library.section(lib[l])
                    clean_database(film_table, films)
            except IndexError:
                pass
        
        # Clean TV database ONLY if TV features are enabled
        tvlib = config.tvlibrary
        if tvlib and tvlib.strip():  # Check if TV library is configured
            tvlib_list = tvlib.split(',')
            tv_n = len(tvlib_list)
            
            # Only scan TV if any TV-related features are enabled
            tv_features_enabled = (
                config.tv4kposters == 1 or
                getattr(config[0], 'spoilers', 0) == 1
            )
            
            if tv_features_enabled and tv_n <= 2:
                try:
                    for l in range(tv_n):  # Use actual number of TV libraries
                        tv = plex.library.section(tvlib_list[l])  # Use correct TV library variable
                        clean_database(ep_table, tv)
                        clean_database(season_table, tv)
                except IndexError:
                    pass
            else:
                logger.info("TV features disabled, skipping TV database cleanup")
        else:
            logger.info("No TV library configured, skipping TV database cleanup")

        module.clear_old_posters()

def collective4k(app):
    with app.app_context(): 
        posters4k(app, '')
        from time import sleep
        sleep(5)
        from app.models import Plex
        config = Plex.query.filter(Plex.id == '1').first()
        if config.tv4kposters == 1:
            logger.info('Starting 4k Tv poster script')
            tv_episode_poster(app, '', '')

def restore_posters(app):
    with app.app_context(): 
        from app.models import Plex, film_table
        from app import db, module
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        tmdb.api_key = config.tmdb_api   

        plex = PlexServer(config.plexurl, config.token)
        size = (2000,3000)
        bannerbox= (0,0,2000,246)
        mini_box = (0,0,350,275)
        hdr_box = (0,1342,493,1608)
        a_box = (0,1608,493,1766)
        cutoff = 10
        def run_script():


            def continue_restore():
                logger.info("Restore-posters: Restore backup posters starting now")
                def restore_tmdb():
                    logger.info("RESTORE: restoring posters from TheMovieDb")
                    g = str(i.guids)
                    g = module.get_tmdb_guid(g)
                    tmdb_search = movie.details(movie_id=g)
                    logger.info(i.title)
                    try:
                        poster = tmdb_search.poster_path
                        fname = 'tmdb_poster_restore.png'
                        module.get_tmdb_poster(fname, poster)
                        i.uploadPoster(filepath=fname)
                        if r:
                            shutil.copy('tmdb_poster_restore.png', re.sub('static', '/config', r[0].poster))
                        os.remove
                    except TypeError:
                        logger.info("RESTORE: "+i.title+" This poster could not be found on TheMoviedb")
                        pass
                def restore(poster):
                        logger.info("RESTORE: restoring posters from Local Backups")

                        logger.info(i.title+ ' Restored')
                        i.uploadPoster(filepath=poster)


                for i in films.search(sort='titleSort', title=''):
                    try:
                        i.title = unicodedata.normalize('NFD', i.title).encode('ascii', 'ignore').decode('utf8')
                        newdir = os.path.dirname(re.sub(config.plexpath, '/films', i.media[0].parts[0].file))+'/'
                        backup = os.path.exists(newdir+'poster_bak.png')
                        guid = str(i.guid)
                        r = film_table.query.filter(film_table.guid == guid).all()
                        if backup == True:
                            try:
                                poster = newdir+'poster_bak.png'
                                restore(poster)
                            except OSError as e:
                                if e.errno == 2:
                                    logger.debug(e)
                        elif r:
                            try:
                                poster = re.sub('static', '/config', r[0].poster)
                                banners = module.check_banners(poster, size)
                                if True not in banners:
                                    restore(poster)

                                elif True in banners and config.tmdb_restore == 1:
                                    restore_tmdb()
                                row = r[0].id
                                film = film_table.query.get(row)
                                film.checked = '0'
                                db.session.commit()                                
                            except Exception as e:
                                logger.error("Can't restore poster from database: "+repr(e))
                                if config.tmdb_restore == 1:
                                    restore_tmdb()
                                else: 
                                    pass
                        elif config.tmdb_restore == 1 and backup == False:
                            try:
                                t = re.sub('plex://movie/', '', guid)
                                tmp_poster = re.sub(' ','_', '/tmp/'+t+'_poster.png')
                                tmp_poster = module.get_poster(i, tmp_poster, i.title, b_dir, 3000, 2000)
                                banners = module.check_banners(tmp_poster, size)
                                hdr = module.get_plex_hdr(i, plex)
                                if (True in banners and (i.media[0].videoResolution  == '4k' or hdr != 'None')):
                                    restore_tmdb()
                                try:
                                    os.remove(tmp_poster)
                                except:
                                    pass
                            except AttributeError as e:
                                logger.warning("Can't get the poster from Plex, restoring from TMDB: "+repr(e))
                                restore_tmdb()
                    except Exception as e:
                        logger.warning(repr(e))
                        pass

            def check_connection():
                try:
                    plex = PlexServer(config.plexurl, config.token)
                except requests.exceptions.ConnectionError as e:
                    logger.error(e)
                    logger.error('Cannot connect to your plex server. Please double check your config is correct.')
                else:
                    continue_restore()                
            check_connection()

            for i in films.search():
                i.title = unicodedata.normalize('NFD', i.title).encode('ascii', 'ignore').decode('utf8')
                newdir = os.path.dirname(re.sub(config.plexpath, '/films', i.media[0].parts[0].file))+'/'
                backup = os.path.join(newdir+'poster_bak.png')            
                try:
                    os.remove(backup)
                except PermissionError as e:
                    logger.error(e)
                except FileNotFoundError as e:
                    logger.error(e)

        lib = config.filmslibrary.split(',')
        n = len(lib)
        if n <= 2:
            try:
                ##while true:
                    for l in range(n):
                        films = plex.library.section(lib[l])
                        run_script()
            except IndexError:
                pass        
        logger.info('Restore Completed.')    

def spoilers(app, guid):
    with app.app_context(): 
        from app.models import Plex, ep_table
        from app import db
        from app import module
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        tv = plex.library.section(config.tvlibrary)
        size = (1280,720)
        cutoff = 10
        tmdb.api_key = config.tmdb_api    
        b_dir = 'static/backup/tv/episodes/'
        logger.info('Starting TV Spolier script')    
        height = 720
        width = 1280
        for ep in tv.search(libtype='episode', guid=guid):
            i = ep
            title = ep.title
            guid = str(ep.guid)
            g = guids = str(ep.guids)
            img_title = ep.grandparentTitle+"_"+ep.parentTitle+"_"+ep.title
            logger.info(img_title)
            size = ep.media[0].parts[0].size
            res = ep.media[0].videoResolution    
            img_title = re.sub(r'[\\/*?:"<>| ]', '_', img_title)
            tmp_poster = re.sub('plex://episode/', '', guid)
            table = ep_table
            hdr = ""
            audio = ""
            banners = ""
            r = ep_table.query.filter(ep_table.guid == guid).all()
            viewcount = int(ep.viewCount)
            try:
                if ep.viewCount == 0:
                    if r:
                        if r[0].blurred != 1:
                            logger.debug("database: "+r[0].title)
                            tmp_poster = re.sub('static', '/config', r[0].poster)
                            i.uploadPoster(filepath=tmp_poster)
                            poster = module.blur(tmp_poster, r, table, db)

                            row = r[0].id
                            film = table.query.get(row)
                            film.checked = '0'
                            db.session.commit()
                            if res == '4k' or hdr != 'None':
                                tv_episode_poster(app, guid, poster)
                            else:
                                i.uploadPoster(filepath=poster)
                    else:
                        module.get_poster(i, tmp_poster, title, b_dir, height, width)
                        banners = module.check_tv_banners(i, tmp_poster, img_title)
                        blurred = 0
                        season = str(i.parentIndex)
                        episode = str(i.index)
                        module.insert_intoTable(guid, guids, size, res, hdr, audio, tmp_poster, banners, title, config, table, db, r, i, b_dir, g, blurred, episode, season)
                        module.blur(tmp_poster, r, table, db, guid)
                else:
                    logger.info(img_title+" is watched")
                    if r:
                        if r[0].blurred == 1:
                            tmp_poster = re.sub('static', '/config', r[0].poster)
                            poster = ""
                            i.uploadPoster(filepath=tmp_poster)
                            row = r[0].id
                            film = table.query.get(row)
                            film.blurred = '0'
                            film.checked = '0'
                            db.session.commit()
                            tv_episode_poster(app, guid, poster)
                    else:
                        logger.info("not adding to database as title is watched.")
            except:
                pass
        logger.info('Spoiler script has finished')

def get_tv_guid(tv_show, season, episode):
        from app.models import Plex, ep_table
        from app import db
        from app import module
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        tv = plex.library.section(config.tvlibrary)
        for ep in tv.search(filters={"show.title":tv_show, "episode.index":episode, "season.index":season}):
            return ep.guid

def delete_row(app, var):
    with app.app_context():    
        print(var)
        from app.models import film_table, ep_table, season_table
        from app import db
        table = ''
        guid = ''
        if 'film' in var:
            table = film_table
            guid = re.sub('film/p', 'p', str(var))

        elif 'episode' in var:
            table = ep_table
            if 'plex://' in var:
                guid = re.sub('episode/p', 'p', str(var))
            else:
                guid = re.sub('episode/l', 'l', str(var))

        elif 'season' in var:
            table = season_table
            if 'plex://' in var:
                guid = re.sub('season/p', 'p', str(var))
            else:
                guid = re.sub('season/l', 'l', str(var))

        print(str(table)+" - "+str(guid))
        r = table.query.filter(table.guid == guid).all()
        row = r[0].id
        d = table.query.get(row)
        db.session.delete(d)
        db.session.commit()
        db.session.close()
        dirpath = '/config/backup/'
        for root, dirs, files in os.walk(dirpath):
            for filename in files:
                f = filename
                if f == guid+'.png':
                    os.remove(dirpath+f)    

def sync_ratings(app):
    with app.app_context():        
        from app.models import Plex
        from app import module
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        tmdb.api_key = config.tmdb_api
        films = plex.library.section('Films')
        for i in films.search():
            try:
                i.title = unicodedata.normalize('NFD', i.title).encode('ascii', 'ignore').decode('utf8')
                i.title = re.sub('#', '', i.title)
                guids = str(i.guids)
                g = guids
                g = module.get_tmdb_guid(g)
                tmdb_search = movie.details(movie_id=g)
                tmdb_rating = tmdb_search.vote_average
                r= round(tmdb_rating,1)
                logger.info(i.title+" - "+str(r)) 
                i.rate(r)
            except Exception as e:
                logger.error('passing: '+i.title)
                logger.error(repr(e))
                pass    

def backup_poster_check(app):
    with app.app_context():
        from app.models import Plex, season_table, film_table, ep_table
        from app import db
        size = (2000,3000)
        errors = []
        def season_backup_check():
                r =db.session.execute(db.select(season_table).order_by(season_table.title)).scalars()
                try:
                    for i in r:
                        poster = re.sub('static', '/config', i.poster)
                        from app import module
                        banners = module.check_banners(poster, size)
                        if True in banners:
                            errors.append(i.title+ ' - '+str(banners))
                except: pass
        def episode_backup_check():
                r =db.session.execute(db.select(ep_table).order_by(ep_table.title)).scalars()
                try:
                    for i in r:
                        poster = re.sub('static', '/config', i.poster)
                        img_title = i.show_season+' - '+i.title
                        from app import module
                        banners = module.check_tv_banners(i, poster, img_title)
                        if True in banners:
                            errors.append(i.title+ ' - '+str(banners))
                except: pass
        def film_backup_check():
                r =db.session.execute(db.select(film_table).order_by(film_table.title)).scalars()
                try:
                    for i in r:
                        poster = re.sub('static', '/config', i.poster)
                        from app import module
                        banners = module.check_banners(poster, size)
                        if True in banners:
                            errors.append(i.title+ ' - '+str(banners))
                except: pass

        logger.info('Checking Films...')
        film_backup_check()
        logger.info('checking TV Seasons...')
        season_backup_check()
        logger.info('Checking TV episodes...')
        episode_backup_check()
        logger.info('Finished checking backup posters')
        if len(errors) >= 1:
            for e in errors:
                logger.error(e)
            return errors
        else: logger.info('Backup posters appear fine')

def get_tmdb_show_posters(var):
    from app.models import Plex
    config = Plex.query.filter(Plex.id == '1').first()
    plex = PlexServer(config.plexurl, config.token)
    tmdbtvs = TV()
    def run_script():
        posters = []
        for show in tv.search(libtype='show', guid=var):
                g = str(show.guids)
                g = g[1:-1]
                g = re.sub(r'[*?:"<>| ]',"",g)
                g = re.sub("Guid","",g)
                g = g.split(",")
                f = filter(lambda a: "tmdb" in a, g)
                g = list(f)
                g = str(g[0])
                gv = [v for v in g if v.isnumeric()]
                g = "".join(gv)
                tmdb_search = tmdbtvs.images(tv_id=g, include_image_language='en')
                for poster in tmdb_search.posters:
                    posters.append(poster.file_path)
        #print(posters)
        return posters
    tvlib = config.tvlibrary

    if not tvlib or not tvlib.strip():

        return []

    lib = tvlib.split(',')
    logger.debug(lib)
    n = len(lib)
    if n <= 2:
        try:
            ##while true:
                for l in range(n):
                    tv = plex.library.section(lib[l])
                    posters = run_script()
                    return posters
        except IndexError:
            pass  

def get_tmdb_season_posters(var):
    from app.models import Plex
    config = Plex.query.filter(Plex.id == '1').first()
    plex = PlexServer(config.plexurl, config.token)
    
    # Check if TV library is configured
    tvlib = config.tvlibrary
    if not tvlib or not tvlib.strip():
        logger.warning("No TV library configured for get_tmdb_season_posters")
        return []
    tmdbtvs = Season()
    def run_script():
        posters = []
        for season in tv.search(libtype='season', guid=var):
            for show in tv.search(libtype='show', guid=season.parentGuid):
                g = str(show.guids)
                g = g[1:-1]
                g = re.sub(r'[*?:"<>| ]',"",g)
                g = re.sub("Guid","",g)
                g = g.split(",")
                f = filter(lambda a: "tmdb" in a, g)
                g = list(f)
                g = str(g[0])
                gv = [v for v in g if v.isnumeric()]
                g = "".join(gv)
                tmdb_search = tmdbtvs.images(tv_id=g, season_num=season.index, include_image_language='en')
                for poster in tmdb_search:
                    posters.append(poster.file_path)
        #print(posters)
        return posters
    tvlib = config.tvlibrary

    if not tvlib or not tvlib.strip():

        return []

    lib = tvlib.split(',')
    logger.debug(lib)
    n = len(lib)
    if n <= 2:
        try:
            ##while true:
                for l in range(n):
                    tv = plex.library.section(lib[l])
                    posters = run_script()
                    return posters
        except IndexError:
            pass  

def get_tmdb_episode_posters(var):
    from app.models import Plex
    config = Plex.query.filter(Plex.id == '1').first()
    plex = PlexServer(config.plexurl, config.token)
    
    # Check if TV library is configured
    tvlib = config.tvlibrary
    if not tvlib or not tvlib.strip():
        logger.warning("No TV library configured for get_tmdb_episode_posters")
        return []
    tmdbtv = Episode()
    def run_script():
        posters = []
        for episode in tv.search(libtype='episode', guid=var):
            for show in tv.search(libtype='show', guid=episode.grandparentGuid):
                g = str(show.guids)
                print(g)
                g = g[1:-1]
                g = re.sub(r'[*?:"<>| ]',"",g)
                g = re.sub("Guid","",g)
                g = g.split(",")
                f = filter(lambda a: "tmdb" in a, g)
                g = list(f)
                g = str(g[0])
                gv = [v for v in g if v.isnumeric()]
                g = "".join(gv)
                tmdb_search = tmdbtv.images(tv_id=g,  season_num=episode.parentIndex, episode_num=episode.index)
                print(tmdb_search)
                for poster in tmdb_search:
                    posters.append(poster.file_path)
        #print(posters)
        return posters
    tvlib = config.tvlibrary

    if not tvlib or not tvlib.strip():

        return []

    lib = tvlib.split(',')
    logger.debug(lib)
    n = len(lib)
    if n <= 2:
        try:
            ##while true:
                for l in range(n):
                    tv = plex.library.section(lib[l])
                    posters = run_script()
                    return posters
        except IndexError:
            pass  

def get_tmdb_film_posters(var):
    from app.models import Plex
    config = Plex.query.filter(Plex.id == '1').first()
    plex = PlexServer(config.plexurl, config.token)
    tmdb = Movie()
    def run_script():
        posters = []
        for film in films.search(guid=var):
            g = str(film.guids)
            print(g)
            g = g[1:-1]
            g = re.sub(r'[*?:"<>| ]',"",g)
            g = re.sub("Guid","",g)
            g = g.split(",")
            f = filter(lambda a: "tmdb" in a, g)
            g = list(f)
            g = str(g[0])
            gv = [v for v in g if v.isnumeric()]
            g = "".join(gv)
            tmdb_search = tmdb.images(movie_id=g, include_image_language='en')
            for poster in tmdb_search.posters:
                posters.append(poster.file_path)
        return posters
    lib = config.filmslibrary.split(',')
    logger.debug(lib)
    n = len(lib)
    if n <= 2:
        try:
            ##while true:
                for l in range(n):
                    films = plex.library.section(lib[l])
                    posters = run_script()
                    return posters
        except IndexError:
            pass          

def upload_tmdb_season(app, var):

        from app import db, module
        from app.models import season_table, ep_table, Plex
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        size = (2000,3000)
        parts = var.split('&')
        guid = parts[1]
        poster = str(parts[3])

        def run_script():
            try:
                for e in tv.search(libtype='episode', filters={"season.guid":guid}):
                    hdr = 'None'
                    ekey = e.key
                    title = e.grandparentTitle
                    for m in plex.fetchItems(ekey):
                        if m.media[0].parts[0].streams[0].DOVIPresent == True:
                            hdr='Dolby Vision'
                        elif 'HDR' in m.media[0].parts[0].streams[0].displayTitle:
                            hdr='HDR'
                    res = e.media[0].videoResolution
                    t = re.sub('plex://season/', '', guid)
                    tmp_poster = re.sub(' ','_', '/tmp/'+t+'_poster.png')
                    print('poster= '+poster)
                    season_poster = module.get_tmdb_poster(tmp_poster, poster)    

                    if (hdr != 'None' or res == '4k'):
                        s_bak = '/config/backup/tv/seasons/'+t+'.png'
                        shutil.copy(season_poster, s_bak)
                        s_banners = module.check_banners(season_poster, size)
                        module.season_decision_tree(config, s_banners, e, hdr, res, season_poster)
                        banner_file = '/config/backup/tv/bannered_seasons/'+t+'.png'
                        shutil.copy(season_poster, banner_file)
                        if os.path.exists(banner_file) != True:
                            raise Exception("Season poster has not copied")
                        table = season_table
                        module.add_season_to_db(db, title, table, guid, banner_file, s_bak) 
                        db.session.close()                       
                        for s in tv.search(guid=guid, libtype='season'):
                            r = season_table.query.filter(season_table.guid == guid).all()
                            module.upload_poster(season_poster, title, db, r, table, s, banner_file)
                    else:
                        for season in tv.search(libtype='season', guid=guid):
                            print(season.parentTitle+': '+season.title)
                            season.uploadPoster(filepath=season_poster)
                    module.remove_tmp_files(season_poster)
                    break
            except Exception as e:
                logger.error("Season poster Error: "+repr(e))
                pass
        tvlib = config.tvlibrary

        if not tvlib or not tvlib.strip():

            return []

        lib = tvlib.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                    for l in range(n):
                        tv = plex.library.section(lib[l])
                        run_script()

            except IndexError:
                pass       

def upload_tmdb_film(app, var):
        from app import db, module
        from app.models import film_table, Plex
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        size = (2000,3000)
        parts = var.split('&')
        guid = parts[1]
        poster = str(parts[3])
        b_dir = 'static/backup/films/'

        def run_script():
            try:
                for film in films.search(guid=guid):
                    print(film.title)
                    r = film_table.query.filter(film_table.guid == guid).all()
                    if r:
                        row = r[0].id
                        f = film_table.query.get(row)
                        hdr = f.hdr
                        audio = f.audio
                        resolution = f.res
                        title = f.title
                        db.session.close()
                        t = re.sub('plex://movie/', '', guid)
                        tmp_poster = re.sub(' ','_', '/tmp/'+t+'_poster.png')
                        film_poster = module.get_tmdb_poster(tmp_poster, poster)
                        film_bak = '/config/backup/films/'+t+'.png'
                        shutil.copy(film_poster, film_bak)
                        if os.path.exists(film_bak) != True:
                            raise Exception("Film poster has not copied")
                        film_banners = module.check_banners(film_poster, size)
                        module.film_banner_decision(film, tmp_poster, film_banners, size, resolution, audio, hdr)
                        banner_file = '/config/backup/bannered_films/'+t+'.png'


                        module.upload_poster(film_poster, title, db, r, film_table, film, banner_file)
                        shutil.copy(film_poster, banner_file)
                        module.remove_tmp_files(film_poster)
                        break
                    else: posters4k(app, film.title, poster)
            except Exception as e:
                logger.error("Film poster Error: "+repr(e))
                pass
        lib = config.filmslibrary.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                for l in range(n):
                    films = plex.library.section(lib[l])
                    run_script()

            except IndexError:
                pass    

def upload_tmdb_episode(app, var):
        from app import db, module
        from app.models import season_table, ep_table, Plex
        config = Plex.query.filter(Plex.id == '1').first()
        plex = PlexServer(config.plexurl, config.token)
        size = (1280,720)
        parts = var.split('&')
        guid = parts[1]
        poster = str(parts[3])
        print(guid+' / '+poster)
        def run_script():
            try:
                for e in tv.search(libtype='episode', guid=guid):
                    print(e.title)
                    r = ep_table.query.filter(ep_table.guid == guid).all()
                    if r:
                        row = r[0].id
                        ep = ep_table.query.get(row)
                        hdr = ep.hdr
                        audio = ep.audio
                        resolution = ep.res
                        db.session.close()
                        print(hdr+' - '+audio+' - '+resolution)
                    else:
                        hdr = module.get_plex_hdr(e, plex)
                        audio = ''
                        resolution = e.media[0].videoResolution
                        ep_banners = ''
                        ep = e
                    
                    t = re.sub('plex://episode/', '', guid)
                    tmp_poster = re.sub(' ','_', '/tmp/'+t+'_poster.png')
                    print('poster= '+poster)
                    episode_poster = module.get_tmdb_poster(tmp_poster, poster)
                    if (hdr != 'none' or resolution == '4k' or audio != ''):
                        ep_bak = '/config/backup/tv/episodes/'+t+'.png'
                        shutil.copy(episode_poster, ep_bak)
                        if os.path.exists(ep_bak) != True:
                            raise Exception("Season poster has not copied")
                        ep_banners = module.check_banners(episode_poster, size)
                        module.tv_banner_decision(e, tmp_poster, ep_banners, audio, hdr, resolution, size)
                        banner_file = '/config/backup/tv/bannered_episodes/'+t+'.png'
                        shutil.copy(episode_poster, banner_file)
                        title = e.grandparentTitle
                        table = ep_table
                        episode = e.index
                        season = e.parentIndex 
                        guids = e.guids
                        g = [s for s in tv.search(libtype='show', guid=e.grandparentGuid)]
                        g = str(g[0].guids) 
                        if r:
                            module.updateTable(guid, guids, size, resolution, hdr, audio, tmp_poster, ep_banners, title, config, table, db, r, e, b_dir, g, False, episode, season)
                        else:                    
                            module.insert_intoTable(guid, guids, size, resolution, hdr, audio, tmp_poster, ep_banners, title, config, table, db, r, e, b_dir, g, False, episode, season) 
                        module.upload_poster(episode_poster, title, db, r, table, e, banner_file)
                    else:
                        e.uploadPoster(filepath=episode_poster)
                    module.remove_tmp_files(episode_poster)
                    break
            except Exception as e:
                logger.error("Episode poster Error: "+repr(e))
                pass
        tvlib = config.tvlibrary

        if not tvlib or not tvlib.strip():

            return []

        lib = tvlib.split(',')
        logger.debug(lib)
        n = len(lib)
        if n <= 2:
            try:
                    for l in range(n):
                        tv = plex.library.section(lib[l])
                        run_script()

            except IndexError:
                pass            

def get_film_posters():

    from app.models import Plex
    config = Plex.query.filter(Plex.id == '1').first()
    plex = PlexServer(config.plexurl, config.token)
    from app.items import Film
    films = []
    def run_script():
        
        for i in film_lib.search():
            films.append(Film(i.title, i.guid, i.thumbUrl, ''))
        return films 
    lib = config.filmslibrary.split(',')
    logger.debug(lib)
    n = len(lib)
    if n <= 2:
        try:
            for l in range(n):
                film_lib = plex.library.section(lib[l]) if lib[l].strip() else None
                films = run_script()
            return films
        except IndexError:
            pass  

def get_shows():
    from app.models import Plex
    config = Plex.query.filter(Plex.id == '1').first()
    plex = PlexServer(config.plexurl, config.token)
    from app.items import Shows
    shows = []
    
    # Check if TV library is configured
    tvlib = config.tvlibrary
    if not tvlib or not tvlib.strip():
        logger.warning("No TV library configured for get_shows")
        return []
    
    def run_script():
        if lib is None:

            return []

        for i in lib.search(libtype='show'):
            shows.append(Shows(i.title, i.guid, i.thumbUrl, ''))
        return shows   
    tvlib = config.tvlibrary
   
    if not tvlib or not tvlib.strip():
   
        return []
   
    lib = tvlib.split(',')
    logger.debug(lib)
    n = len(lib)
    if n <= 2:
        try:
            for l in range(n):
                if lib[l] and lib[l].strip():

                    lib = plex.library.section(lib[l])

                else:

                    return [] if lib[l].strip() else None
                shows = run_script()
            return shows
        except IndexError:
            pass 

def get_tv_seasons(var):
    from app.models import Plex
    config = Plex.query.filter(Plex.id == '1').first()
    plex = PlexServer(config.plexurl, config.token)
    
    # Check if TV library is configured
    tvlib = config.tvlibrary
    if not tvlib or not tvlib.strip():
        logger.warning("No TV library configured for get_tv_seasons")
        return []
    from app.items import Season
    seasons = []
    def run_script():
        if lib is None:

            return []

        for i in lib.search(libtype='season', filters={"show.guid":var}):
            show_poster = config.plexurl+i.parentThumb+'?X-Plex-Token='+config.token
            seasons.append(Season(i.title, i.parentTitle, i.guid, i.thumbUrl, '', show_poster, i.parentGuid))
        return seasons   
    tvlib = config.tvlibrary
   
    if not tvlib or not tvlib.strip():
   
        return []
   
    lib = tvlib.split(',')
    logger.debug(lib)
    n = len(lib)
    if n <= 2:
        try:
            for l in range(n):
                if lib[l] and lib[l].strip():

                    lib = plex.library.section(lib[l])

                else:

                    return [] if lib[l].strip() else None
                seasons = run_script()
            return seasons
        except IndexError:
            pass 
  
def get_tv_episodes(var):
    from app.models import Plex
    config = Plex.query.filter(Plex.id == '1').first()
    plex = PlexServer(config.plexurl, config.token)
    
    # Check if TV library is configured
    tvlib = config.tvlibrary
    if not tvlib or not tvlib.strip():
        logger.warning("No TV library configured for get_tv_episodes")
        return []
    from app.items import Episode
    episodes = []
    def run_script():
        if lib is None:

            return []

        for i in lib.search(libtype='episode', filters={"season.guid":var}):
            season_poster = config.plexurl+i.parentThumb+'?X-Plex-Token='+config.token
            episodes.append(Episode(i.title, i.parentTitle, i.grandparentTitle, i.guid, i.thumbUrl, '', season_poster, i.parentGuid))
        return episodes   
    tvlib = config.tvlibrary
   
    if not tvlib or not tvlib.strip():
   
        return []
   
    lib = tvlib.split(',')
    logger.debug(lib)
    n = len(lib)
    if n <= 2:
        try:
            for l in range(n):
                if lib[l] and lib[l].strip():

                    lib = plex.library.section(lib[l])

                else:

                    return [] if lib[l].strip() else None
                episodes = run_script()
            return episodes
        except IndexError:
            pass   

def get_season_posters(var):
    from app.models import Plex
    config = Plex.query.filter(Plex.id == '1').first()
    plex = PlexServer(config.plexurl, config.token)
    
    # Check if TV library is configured
    tvlib = config.tvlibrary
    if not tvlib or not tvlib.strip():
        logger.warning("No TV library configured for get_season_posters")
        return []
    from app.items import Season
    seasons = []    
    def run_script():
        if lib is None:

            return []

        for i in lib.search(libtype='season', guid=var):
            show_poster = config.plexurl+i.parentThumb+'?X-Plex-Token='+config.token
            seasons.append(Season(i.title, i.parentTitle, i.guid, i.thumbUrl, '', show_poster, i.parentGuid))
        return seasons   
    tvlib = config.tvlibrary
   
    if not tvlib or not tvlib.strip():
   
        return []
   
    lib = tvlib.split(',')
    logger.debug(lib)
    n = len(lib)
    if n <= 2:
        try:
            for l in range(n):
                if lib[l] and lib[l].strip():

                    lib = plex.library.section(lib[l])

                else:

                    return [] if lib[l].strip() else None
                seasons = run_script()
            return seasons
        except IndexError:
            pass     

def get_episode_posters(var):
    from app.models import Plex
    config = Plex.query.filter(Plex.id == '1').first()
    plex = PlexServer(config.plexurl, config.token)
    
    # Check if TV library is configured
    tvlib = config.tvlibrary
    if not tvlib or not tvlib.strip():
        logger.warning("No TV library configured for get_episode_posters")
        return []
    from app.items import Episode
    episodes = []
    def run_script():
        if lib is None:

            return []

        for i in lib.search(libtype='episode', guid=var):
            season_poster = config.plexurl+i.parentThumb+'?X-Plex-Token='+config.token
            episodes.append(Episode(i.title, i.parentTitle, i.grandparentTitle, i.guid, i.thumbUrl, '', season_poster, i.parentGuid))
        return episodes   
    tvlib = config.tvlibrary
   
    if not tvlib or not tvlib.strip():
   
        return []
   
    lib = tvlib.split(',')
    logger.debug(lib)
    n = len(lib)
    if n <= 2:
        try:
            for l in range(n):
                if lib[l] and lib[l].strip():

                    lib = plex.library.section(lib[l])

                else:

                    return [] if lib[l].strip() else None
                episodes = run_script()
            return episodes
        except IndexError:
            pass  