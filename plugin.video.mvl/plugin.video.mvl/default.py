import sys
if 'do_nothing' in sys.argv[0]:
    #no need to do anything!
    exit()

#hide any existing loading and show system busy dialog to freeze the screen
xbmc.executebuiltin( "Dialog.Close(busydialog)" )
xbmc.executebuiltin( "ActivateWindow(busydialog)" )
#save lockdown state to a file for future reference
import os
file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'screen_lock.dat')
f = open(file_path, 'w')
f.write('true')
f.close()
####

from xbmcswift2 import Plugin, xbmcgui, xbmc, xbmcaddon, xbmcplugin, actions
import urllib2
import time
import calendar
import simplejson as json
import urllib
import urllib2
import xbmcvfs
import xbmcaddon
import xbmcplugin
from t0mm0.common.addon import Addon
import re
import traceback

from metahandler import metahandlers
from metahandler import metacontainers

from operator import itemgetter
from threading import Thread

#Patch Locale for android devices
def getlocale(*args, **kwargs):
    return (None, None)
import locale
locale.getlocale=getlocale
from datetime import datetime


_MVL = Addon('plugin.video.mvl', sys.argv)
plugin = Plugin()
pluginhandle = int(sys.argv[1])
usrsettings = xbmcaddon.Addon(id='plugin.video.mvl')
page_limit = usrsettings.getSetting('page_limit_xbmc')
authentication = plugin.get_storage('authentication', TTL=1)
authentication['logged_in'] = 'false'
username = usrsettings.getSetting('username_xbmc')
activation_key = usrsettings.getSetting('activationkey_xbmc')
usrsettings.setSetting(id='mac_address', value=usrsettings.getSetting('mac_address'))
THEME_PATH = os.path.join(_MVL.get_path(), 'art')
# server_url = 'http://staging.redbuffer.net/xbmc'
# server_url = 'http://localhost/xbmc'
server_url = 'http://config.myvideolibrary.com'
PREPARE_ZIP = False

__metaget__ = metahandlers.MetaData(preparezip=PREPARE_ZIP)


# try:
# import StorageServer
# except:
# import storageserverdummy as StorageServer
# #cache = StorageServer.StorageServer("mvl_storage_data", 24) # (Your plugin name, Cache time in hours)
# cache = StorageServer.StorageServer("plugin://plugin.video.mvl/", 24)
# cache.delete("%")

try:
    from sqlite3 import dbapi2 as orm

    plugin.log.info('Loading sqlite3 as DB engine')
except:
    from pysqlite2 import dbapi2 as orm

    plugin.log.info('pysqlite2 as DB engine')
DB = 'sqlite'
__translated__ = xbmc.translatePath("special://database")
DB_DIR = os.path.join(__translated__, 'myvideolibrary.db')
plugin.log.info('DB_DIR: ' + DB_DIR)
mvl_view_mode = 58
mvl_tvshow_title = ''
isAgree = False


@plugin.route('/')
def index():
    global Main_cat
    
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'quit_log.dat')
    f = open(file_path, 'w')
    f.close()
    
    try:
        #set view mode first so that whatever happens, it doesn't change
        mvl_view_mode = 58
    
        
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'userdata', 'advancedsettings.xml')
        found = False
        if os.path.exists(file_path):
            file = open(file_path, 'r')
            for line in file:
                if '<showparentdiritems>false</showparentdiritems>' in line:
                    found = True
            file.close()

        file_path_keymap = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'userdata', 'keymaps', 'Keyboard.xml')
        found_keymap = False
        if os.path.exists(file_path_keymap):
            file = open(file_path_keymap, 'r')
            for line in file:
                if "<F2>Skin.ToggleSetting('test')</F2>" in line:
                    found_keymap = True
            file.close()

            
        if not found or not found_keymap:
            file = open(file_path, 'w')
            file.write('<advancedsettings>\n')
            file.write('<filelists>\n')
            file.write('<showparentdiritems>false</showparentdiritems>\n')
            file.write('</filelists>\n')
            file.write('<lookandfeel>\n')
            file.write('<skin>skin.mvl</skin>\n')
            file.write('</lookandfeel>\n')
            file.write('</advancedsettings>\n')
            file.close()
            
            #now create keymap file
            file = open(file_path_keymap, 'w')
            file.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
            file.write('<keymap>\n')
            file.write('<global>\n')
            file.write('<keyboard>\n')
            file.write("<F2>Skin.ToggleSetting('test')</F2>\n")
            file.write("<F3>Skin.ToggleSetting('test')</F3>\n")
            file.write("<F4>Skin.ToggleSetting('test')</F4>\n")
            file.write("<F5>Skin.ToggleSetting('test')</F5>\n")
            file.write("<F6>Skin.ToggleSetting('test')</F6>\n")
            file.write("<backslash>Skin.ToggleSetting('test')</backslash>\n")
            file.write("<backspace>XBMC.RunScript(special://home\\addons\plugin.video.mvl\script_backhandler.py)</backspace>\n")
            file.write('</keyboard>\n')
            file.write('</global>\n')
            file.write('</keymap>')
                        
            hide_busy_dialog()
            
            showMessage('Restart Required', 'Some settings have been changed. You need to restart MyVideoLibrary for the changes to take effect. MyVideoLibrary will now close.')
            
            xbmc.executebuiltin('RestartApp()')
            
            return None
        else:
        
            #if we have found the settings, then this is not the first run
            #we are good to go
            #run thread to check for internet connection in the background
            #setup_internet_check()
        
            # Create a window instance.
            #global isAgree
            check_condition()
            #creating the database if not exists
            init_database()
            #creating a context menu
            #url used to get main categories from server
            url = server_url + "/api/index.php/api/categories_api/getCategories?parent_id=0&limit={0}&page=1".format(page_limit)
            plugin.log.info(url)
            req = urllib2.Request(url)
            opener = urllib2.build_opener()
            f = opener.open(req)
            #reading content fetched from the url
            content = f.read()
            
            hide_busy_dialog()
            
            #converting to json object
            jsonObj = json.loads(content)
            items = []

            if isAgree == True:
                show_notification()
            
                plugin.log.info("here is dialog")
                #creating items from json object
                for categories in jsonObj:
                    items += [{
                                  'label': '{0}'.format(categories['title']),
                                  'path': plugin.url_for('get_categories', id=categories['id'], page=0),
                                  'is_playable': False,
                                  'thumbnail': art('{0}.png'.format(categories['title'].lower())),
                              }]
                              
                # hide_busy_dialog()
                return items

    except IOError:
        # xbmc.executebuiltin('Notification(Unreachable Host,Could not connect to server,5000,/error.png)')
        dialog_msg()
        hide_busy_dialog()
        sys_exit()

        
def setup_internet_check():
    t = Thread(target=check_internet_connection)
    t.daemon = True
    t.start()
     
def check_quit_log():
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'quit_log.dat')
    f = open(file_path, 'r')
    r = f.read()
    f.close()
    
    # print "check quit log = " + str(r)
    
    if r:
        return True
    else:
        return False

     
# called by each thread
def check_internet_connection():
    sleep_time = 20
    
    try:
        while(True):
            print 'Starting outbound call to test internet connection'
            url = 'http://www.google.com'
            response = urllib2.urlopen(url, timeout=1)
            count = sleep_time
            while count:
                count = count - 1
                time.sleep(1)
                
                if check_quit_log():
                    return
                    
    except Exception, e:        
        print e
        # showMessage('No Connection', 'No internet connection can be found')
        dialog_msg()
        #now setup another thread to continue checking internet connection
        count = sleep_time
        while count:
            count = count - 1
            time.sleep(1)
            
            if check_quit_log():
                return
        
        setup_internet_check()

        
def show_notification():

    try:
        url = server_url + "/api/index.php/api/notification_api/getNotification"
        plugin.log.info(url)
        req = urllib2.Request(url)
        opener = urllib2.build_opener()
        f = opener.open(req)
        #reading content fetched from the url
        content = f.read()
        #converting to json object
        jsonObj = json.loads(content)

        message = jsonObj['message']
        
        if message != '':
            showMessage('Notification', message)
            sys_exit()
            return True
    except:
        #do nothing
        message = ''
        
    return False

def onClick_disAgree():
    # window.close()
    sys_exit()


def onClick_agree():
    global isAgree
    macAddress = usrsettings.getSetting('mac_address')
    plugin.log.info("I Agree func calls")
    url = server_url + "/api/index.php/api/authentication_api/set_flag_status?username={0}&mac={1}".format(username, macAddress)
    req = urllib2.Request(url)
    opener = urllib2.build_opener()
    f = opener.open(req)
    
    isAgree = True

    
def showMessage(heading, message):
    dialog = xbmcgui.Dialog()
    dialog.ok(heading, message)
    
def check_condition():
    macAddress = usrsettings.getSetting('mac_address')
    global curr_page
    curr_page = 1
    url = server_url + "/api/index.php/api/authentication_api/get_flag_status?username={0}&mac={1}".format(username,
                                                                                                           macAddress)
    req = urllib2.Request(url)
    opener = urllib2.build_opener()
    # f = opener.open(req)
    #reading content fetched from the url
    # content = f.read()
    content = 'false'
    #converting to json object
    plugin.log.info(url)
    plugin.log.info(content)
    if content == 'false':
        #Show Terms & Condition window
        heading = "Terms & Conditions"
        tc_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 't&c.info')
        f = open(tc_path)
        text = f.read()
        
        dialog = xbmcgui.Dialog()
        agree_ret = dialog.yesno(heading, text, yeslabel='Agree', nolabel='Disagree')
        
        if agree_ret:
            onClick_agree()
        else:
            onClick_disAgree()
        
    elif content == 'true':
        global isAgree
        isAgree = True
    else:
        plugin.log.info('Closing')
        #sys_exit()


def art(name):
    plugin.log.info('plugin-name')
    plugin.log.info(name)
    art_img = os.path.join(THEME_PATH, name)
    return art_img


def get_mac_address():
    try:
        local_mac_address = xbmc.getInfoLabel('Network.MacAddress')
        if local_mac_address == 'Busy':
            time.sleep(1)
            get_mac_address()
        else:
            return local_mac_address
    except IOError:
        # xbmc.executebuiltin('Notification(Mac Address Not Available,MVL Could not get the MAC Address,5000,/script.hellow.world.png)')
        showMessage('Error','Mac Address Not Available, MVL Could not get the MAC Address')

    # xbmc.executebuiltin('Notification(MAC_Flag Check1,{0},2000)'.format(cache.get("mac_address_flag")))
    # xbmc.executebuiltin('Notification(MAC_Address Check1,{0},2000)'.format(usrsettings.getSetting('mac_address')))

    # if cache.get("mac_address_flag") == 'None' or cache.get("mac_address_flag") == '':
    # cache.set("mac_address_flag", "false")


if usrsettings.getSetting('mac_address') == 'None' or usrsettings.getSetting('mac_address') == '':
    #xbmc.executebuiltin('Notification(MAC_Address Check2,{0},2000)'.format(usrsettings.getSetting('mac_address')))
    plugin.log.info(get_mac_address())
    usrsettings.setSetting(id='mac_address', value='{0}'.format(get_mac_address()))


def check_internet():
    try:
        response = urllib2.urlopen('http://74.125.228.100', timeout=1)
        return True
    except urllib2.URLError as err:
        pass
    return False


def dialog_msg():

    heading = "INTERNET CONNECTION ISSUE"
    # text = "An error has occured communicating with MyVideoLibrary server. Please check that you are connected to internet through wi-fi"
    text = "Your internet connection has been lost. Please wait a few minutes and try again. If the error persists you may wish to contact your Internet Service Provider."
        
    #show message is a dialog window
    showMessage(heading, text)

def hide_busy_dialog():
    #hide loadign screen
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    #clear file content to release lock
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'screen_lock.dat')
    f = open(file_path, 'w')
    f.close()
    
    
def show_root():
    global internet_info
    internet_info.close()
    sys_exit()

    
@plugin.route('/do_nothing/<view_mode>')
def do_nothing(view_mode):
    global mvl_view_mode
    
    if view_mode != 0:
        mvl_view_mode = view_mode
    
    hide_busy_dialog()

    return None

    
@plugin.route('/categories/<id>/<page>')
def get_categories(id, page):
    #import resources.htmlcleaner
    #import re
    global mvl_view_mode

    # showMessage('he he', str(mvl_view_mode))
    
    mvl_view_mode = 58
    # hide_busy_dialog()
    # return None

    if check_internet():
        global mvl_tvshow_title
        
        show_notification()
        
        #save current view mode in case any error occurs and we need to remain on the same page
        prev_view_mode = mvl_view_mode
        
        try:

            parent_id = id
            main_category_check = False
            is_search_category = False
            top_level_parent = 0
            page_limit_cat = 30
            xbmcplugin.setContent(pluginhandle, 'Movies')
            plugin.log.info(id)
            plugin.log.info(page)
            plugin.log.info(page_limit_cat)
            
            
            #freeze UI by showing a busy dialog
            # xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            # xbmc.executebuiltin( "ActivateWindow(busydialog)" )

            # #wait for 30 seconds
            # time.sleep(10)

            # #make everything normal
            # xbmc.executebuiltin( "Dialog.Close(busydialog)" )
            
            url = server_url + "/api/index.php/api/categories_api/getCategories?parent_id={0}&page={1}&limit={2}".format(id, 
                                                                                                                         page,
                                                                                                                         page_limit_cat)
            plugin.log.info(url)
            req = urllib2.Request(url)
            opener = urllib2.build_opener()
            f = opener.open(req)
            content = f.read()
            items = []
            image_on_off = ''
            
            if content:
                jsonObj = json.loads(content)
                totalCats = len(jsonObj)
                plugin.log.info('total categories-->%s' % totalCats)
                # plugin.log.info(jsonObj)
                if jsonObj[0]['top_level_parent'] == jsonObj[0]['parent_id']:
                    is_search_category = True
                    image_on_off = '_off'
                    
                ###########
                #if the items are season episodes, we need ot sort them naturally i.e. use Natural Sort for sorting
                if jsonObj[0]['top_level_parent'] == '3' and jsonObj[0]['parent_id'] not in ('32', '3'):
                    is_playable = False
                    for categories in jsonObj:
                        if 'title' not in categories:
                            #for the "next" entry
                            categories['title'] = '9999999999999999999999999'
                        
                        categories['sort_key'] = categories['title'].strip().split(' ')[0]
                        categories['sort_key_len'] = len(categories['title'].strip().split(' ')[0])
                        categories['title_len'] = len(categories['title'].strip())
                        
                        if categories['id'] != -1 and categories['is_playable'] == 'True':
                            is_playable = True
                    
                    if jsonObj[0]['title'].split(' ')[0].lower() == 'Season'.lower():   
                        #if items are seasons, then sort them by title length to get correct ordering                        
                        jsonObj.sort(key=lambda x: (x['title_len'], x['title']))
                    elif is_playable:
                        #otherwise, sort by the first string of the title which should like this: 1x1, 1x2, 1x10, 1x15.....
                        jsonObj.sort(key=lambda x: (x['sort_key_len'], x['sort_key']))
                
                    
                ###########

                item_count = len(jsonObj)
                done_count = 0
                
                dp = xbmcgui.DialogProgress()
                dp_created = False
                dp_type = 'show'
                
                #sort categories according to release_date except for <Featured> group and TV shows
                if jsonObj[0]['parent_id'] not in ('372395', '372396') and jsonObj[0]['top_level_parent'] != '3':
                    release_date_count = 0
                    for categories in jsonObj:
                        if 'release_date' not in categories:
                            categories['release_date'] = '-1'
                        elif categories['release_date'] is not None and len(categories['release_date']) == 10:
                            #we seem to have got a proper date string
                            #make sure we have a valid date format
                            try:
                                mydate = datetime.strptime(categories['release_date'], '%Y-%m-%d')
                            except TypeError:
                                mydate = datetime(*(time.strptime(categories['release_date'], '%Y-%m-%d')[0:6]))
                            except Exception,e:
                                print e

                            #put the release_group title in <Month, Year> format
                            categories['release_group'] = '[COLOR FF2261B4]'+calendar.month_name[mydate.month] + ', ' + str(mydate.year)+'[/COLOR]'
                            release_date_count = 1

                    if release_date_count == 0:
                        #release_date_count is still 0, meaning we haven't got any release_date in proper date format
                        #let's see if we can find any release_date with only year string
                        for categories in jsonObj:
                            if 'release_date' not in categories:
                                categories['release_date'] = '-1'
                            elif categories['release_date'] is not None and len(categories['release_date']) == 4:
                                #we seem to have got a year string
                                #put the release_group title in <Year> format
                                categories['release_group'] = '[COLOR FF2261B4]'+categories['release_date']+'[/COLOR]'
                                release_date_count = 1

                    if release_date_count == 0:
                        for categories in jsonObj:
                            if 'release_date' not in categories:
                                categories['release_date'] = '-1'
                            elif categories['release_date'] is not None and len(categories['release_date']) == 4:
                                #make sure we have valid date format
                                categories['release_group'] = '[COLOR FF2261B4]'+categories['release_date']+'[/COLOR]'
                                release_date_count = 1

                    #if release_date_count is still 0, it means no entry has a release date
                    #no need to sort then
                    #otherwise sort in Desc order by release date
                    if release_date_count == 1:
                        jsonObj.sort(key=lambda x: x['release_date'], reverse=True)

                    # print jsonObj
                
                last_release_group = ''

                for categories in jsonObj:
                    try:    # The last item of Json only contains the one element in array with key as "ID" so causing the issue

                        plugin.log.info('{0}'.format(categories['is_playable']))
                        if categories['top_level_parent'] == categories['parent_id']:
                            main_category_check = True

                    except:
                        pass

                    if is_search_category == True:
                        is_search_category = False
                        #adding search option
                        items += [{
                                  'label': 'Search',
                                  'path': plugin.url_for('search', category=parent_id),
                                  'thumbnail': art('search'+image_on_off+'.png'),
                                  'is_playable': False,
                                  }]

                    ####
                    #add an extra item for the release month + year combo
                    if 'release_group' in categories:
                        if categories['release_group'] != last_release_group:
                            last_release_group = categories['release_group']
                            
                            items += [{
                                          'label': categories['release_group'],
                                          'path': plugin.url_for('do_nothing', view_mode=0),
                                          'is_playable': True
                                      }]

                    ####
                    
                    #categories['id'] is -1 when more categories are present and next page option should be displayed
                    if categories['id'] == -1:
                        items += [{
                                      'label': 'Next >>',
                                      'path': plugin.url_for('get_categories', id=parent_id, page=(int(page) + 1)),
                                      'is_playable': False,
                                      'thumbnail': art('next.png')
                                  }]
                    #categories['is_playable'] is False for all categories and True for all video Items
                    elif categories['is_playable'] == 'False':

                        if categories['top_level_parent'] == '3' and categories['parent_id'] not in ('32', '3'):  # Parsing the TV Shows Titles & Seasons only
                            tmpTitle = categories['title'].encode('utf-8')

                            mvl_meta = ''
                            if tmpTitle == "Season 1":
                                tmpSeasons = []
                                mvl_view_mode = 50
                                # for i in range(totalCats):
                                # tmpSeasons.append( i )
                                #plugin.log.info('season found')
                                #mvl_meta = __metaget__.get_seasons(mvl_tvshow_title, '', tmpSeasons)
                            else:
                                mvl_meta = create_meta('tvshow', categories['title'].encode('utf-8'), '', '')
                                mvl_tvshow_title = categories['title'].encode('utf-8')

                            dp_type = 'show'
                            
                            plugin.log.info('meta data-> %s' % mvl_meta)
                            thumbnail_url = ''
                            try:
                                if mvl_meta['cover_url']:
                                    thumbnail_url = mvl_meta['cover_url']
                            except:
                                thumbnail_url = ''

                            fanart_url = ''
                            try:
                                if mvl_meta['backdrop_url']:
                                    fanart_url = mvl_meta['backdrop_url']
                            except:
                                fanart_url = ''

                            mvl_plot = ''
                            try:
                                if mvl_meta['plot']:
                                    mvl_plot = mvl_meta['plot']
                            except:
                                mvl_plot = ''

                            items += [{
                                          'label': '{0}'.format(categories['title']),
                                          'path': plugin.url_for('get_categories', id=categories['id'], page=0),
                                          'is_playable': False,
                                          'thumbnail': thumbnail_url,
                                          'properties': {
                                              'fanart_image': fanart_url,
                                          },
                                          'context_menu': [(
                                                               'Add to Favourites',
                                                               'XBMC.RunPlugin(%s)' % plugin.url_for('save_favourite',
                                                                                                     id=categories['id'],
                                                                                                     title=categories[
                                                                                                         'title'],
                                                                                                     thumbnail="None",
                                                                                                     isplayable="False",
                                                                                                     category=categories[
                                                                                                         'top_level_parent'])
                                                           )],
                                          'replace_context_menu': True
                                      }]

                        else:

                            items += [{
                                          'label': '{0}'.format(categories['title']),
                                          'path': plugin.url_for('get_categories', id=categories['id'], page=0),
                                          'is_playable': False,
                                          'thumbnail': art('{0}{1}.png'.format(categories['title'].lower(), image_on_off)),
                                          'context_menu': [(
                                                               'Add to Favourites',
                                                               'XBMC.RunPlugin(%s)' % plugin.url_for('save_favourite',
                                                                                                     id=categories['id'],
                                                                                                     title=categories[
                                                                                                         'title'],
                                                                                                     thumbnail="None",
                                                                                                     isplayable="False",
                                                                                                     category=categories[
                                                                                                         'top_level_parent'])
                                                           )],
                                          'replace_context_menu': True
                                      }]

                            #plugin.log.info(art('{0}.png'.format(categories['title'].lower())))

                    #inorder for the information to be displayed properly, corresponding labels should be added in skin
                    elif categories['is_playable'] == 'True':

                        if categories['video_id'] == '0':
                            #there is something wrong with this playable item. just ignore
                            continue
                            
                        if categories['source'] == '1':
                            thumbnail_url = categories['image_name']
                        else:
                            thumbnail_url = server_url + '/wp-content/themes/twentytwelve/images/{0}'.format(categories['video_id'] + categories['image_name'])

                        mvl_img = thumbnail_url
                        mvl_meta = create_meta('movie', categories['title'].encode('utf-8'), categories['release_date'], mvl_img)
                        plugin.log.info('>> meta data-> %s' % mvl_meta)
                        thumbnail_url = ''
                        
                        dp_type = 'movie'
                        
                        try:
                            if mvl_meta['cover_url']:
                                thumbnail_url = mvl_meta['cover_url']
                        except:
                            thumbnail_url = mvl_img
                        # New condition added
                        if thumbnail_url == '':
                            thumbnail_url = art('image-not-available.png')
                        fanart_url = ''
                        try:
                            if mvl_meta['backdrop_url']:
                                fanart_url = mvl_meta['backdrop_url']
                        except:
                            fanart_url = ''

                        mvl_plot = ''
                        try:
                            if mvl_meta['plot']:
                                mvl_plot = mvl_meta['plot']
                        except:
                            mvl_plot = categories['synopsis'].encode('utf-8')
                            
                        
                        items += [{
                                      'thumbnail': thumbnail_url,
                                      'properties': {
                                          'fanart_image': fanart_url,
                                      },
                                      'label': '{0}'.format(categories['title'].encode('utf-8')),
                                      'info': {
                                          'title': categories['title'].encode('utf-8'),
                                          'rating': categories['rating'],
                                          'comment': categories['synopsis'].encode('utf-8'),
                                          'Director': categories['director'].encode('utf-8'),
                                          'Producer': categories['producer'],
                                          'Writer': categories['writer'],
                                          'plot': mvl_plot,
                                          'genre': categories['sub_categories_names'],
                                          'cast': categories['actors'].encode('utf-8'),
                                          'year': categories['release_date']
                                      },
                                      'path': plugin.url_for('get_videos', id=categories['video_id'],
                                                             thumbnail=thumbnail_url),
                                      'is_playable': False,
                                      'context_menu': [(
                                                           'Add to Favourites',
                                                           'XBMC.RunPlugin(%s)' % plugin.url_for('save_favourite',
                                                                                                 id=categories['video_id'],
                                                                                                 title=categories[
                                                                                                     'title'].encode(
                                                                                                     'utf-8'),
                                                                                                 thumbnail=thumbnail_url,
                                                                                                 isplayable="True",
                                                                                                 category=categories[
                                                                                                     'top_level_parent'])
                                                       )],
                                      'replace_context_menu': True
                                  }]
                                  
                    if categories['id'] != -1:
                        if categories['top_level_parent'] == '1':
                            dp_type = 'movie'
                        elif categories['top_level_parent'] == '3':
                            dp_type = 'show'
                        
                    if dp_created == False:
                        dp.create("Please wait while "+dp_type+" list is loaded","","")
                        dp_created = True
                                  
                    done_count = done_count + 1
                    dp.update((done_count*100/item_count), "This wont happen next time you visit.",  str(done_count)+" of "+str(item_count)+" "+dp_type+"s loaded so far.")

                    if dp.iscanceled():
                        break
                    


                if main_category_check == True:
                    #adding A-Z listing option
                    items += [{
                                  'label': 'A-Z Listings',
                                  'path': plugin.url_for('azlisting', category=parent_id),
                                  'thumbnail': art('A-Z'+image_on_off+'.png'),
                                  'is_playable': False,
                              }]
                    #Most Popular & Favortite are commented out on Client's request for now
                    #adding Most Popular option
                    # items += [{
                    # 'label': 'Most Popular',
                    # 'path': plugin.url_for('mostpopular', page=0, category=parent_id),
                    # 'thumbnail' : art('pop.png'),
                    # 'is_playable': False,
                    # }]
                    # #adding Favourites option
                    # items += [{
                    # 'label': 'Favourites',
                    # 'path': plugin.url_for('get_favourites', category=parent_id),
                    # 'thumbnail' : art('fav.png'),
                    # 'is_playable': False,
                    # }]
                #plugin.log.info(items)
                
                dp.close()

                
            #we should set the view_mode as last thing in this method
            #because if user cancels his action and goes back before the api response
            #the view_mode will still be changed otherwise
            if id in ('23', '32'): # if the Parent ID is Genres for TV or Movies then view should be set as "List" mode
                mvl_view_mode = 50
            elif id in ('1', '3'):  # if these are immediate childs of Top Level parents then view should be set as Fan Art
                mvl_view_mode = 59
            # else:
                # mvl_view_mode = 59
                
            hide_busy_dialog()
            
            plugin.log.info("View mode = " + str(mvl_view_mode))

            return items
        # except IOError:
            # xbmc.executebuiltin('Notification(Unreachable Host,Could not connect to server,5000,/script.hellow.world.png)')
        except Exception, e:
            if id in ('1', '3'):  # if we were on 1st page, then the viewmode should remain to 58 as an error has occured and we haven't got any data for next screen
                mvl_view_mode = 58
            elif id in ('23', '104916', '112504', '32', '104917', '366042', '372395', '372396'):
                mvl_view_mode = 59
                
            # xbmc.executebuiltin('Notification(Unreachable Host,Could not connect to server,5000,/script.hellow.world.png)')
            dialog_msg()
            hide_busy_dialog()
            # plugin.log.info(e)
            # traceback.print_exc()
    else:
        if id in ('1', '3'):  # if we were on 1st page, then the viewmode should remain to 58 as an error has occured and we haven't got any data for next screen
            mvl_view_mode = 58
        elif id in ('23', '104916', '112504', '32', '104917', '366042', '372395', '372396'):
            mvl_view_mode = 59
                
        #show error message
        dialog_msg()
        hide_busy_dialog()


@plugin.route('/get_videos/<id>/<thumbnail>/')
def get_videos(id, thumbnail):
    if check_internet():
        show_notification()    
        
        global mvl_view_mode
        mvl_view_mode = 50
        try:
            url = server_url + "/api/index.php/api/categories_api/getVideoUrls?video_id={0}".format(id)
            req = urllib2.Request(url)
            opener = urllib2.build_opener()
            f = opener.open(req)
            content = f.read()
            jsonObj = json.loads(content)

            url = server_url + "/api/index.php/api/categories_api/getVideoTitle?video_id={0}".format(id)
            req = urllib2.Request(url)
            opener = urllib2.build_opener()
            f = opener.open(req)
            content = f.read()
            count = 0
            items = []
            plugin.log.info(jsonObj)

            # instruction text    
            items += [{
                          'label': '[COLOR FF834DCC]Please click on a link below to begin viewing[/COLOR]',
                          'path': plugin.url_for('do_nothing', view_mode=mvl_view_mode),
                          'is_playable': True
                      }]

            hd_count = 0
            sd_count = 0
            for urls in jsonObj:
                source_quality = ''
                if urls['is_hd']:
                    source_quality = '*HD'
                    source_color = 'FFFF0000'
                    hd_count += 1
                else:
                    source_quality = ''
                    source_color = 'FF834DCC'
                    sd_count += 1

                if (source_quality != '' and hd_count < 5) or (source_quality == '' and sd_count < 5):
                    count += 1

                    items += [{
                                  'label': '{0} [COLOR FF235B9E]Source {1}[/COLOR] [COLOR {2}]{3}[/COLOR]'.format(content, count, source_color, source_quality),
                                  'thumbnail': thumbnail,
                                  'path': plugin.url_for('play_video', url=urls['URL'], title='{0}'.format(content)),
                                  'is_playable': False,
                              }]

            hide_busy_dialog()
            return items
        except IOError:
            # xbmc.executebuiltin('Notification(Unreachable Host,Could not connect to server,5000,/error.png)')
            dialog_msg()
            hide_busy_dialog()
    else:
        dialog_msg()
        hide_busy_dialog()



@plugin.route('/play_video/<url>/<title>')
def play_video(url, title):
    global mvl_view_mode
    
    if check_internet():
        show_notification()    
        
        mvl_view_mode = 50
        #if login is successful then selected item will be resolved using urlresolver and played
        if login_check():
            unplayable = False
            try:
                #first import urlresolver
                #as this takes a while, we'll be importing it only when required
                import urlresolver
                
                # print 'Resolving.....'
                hostedurl = urlresolver.HostedMediaFile(url).resolve()
                plugin.log.info(url)
                plugin.log.info(hostedurl)
                
                if str(hostedurl)[0] == 'h':
                    hide_busy_dialog()
                    #plugin.set_resolved_url(hostedurl)
                    #play the resolved url manually, since we aren't using playable link
                    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
                    playlist.clear()
                    listitem = xbmcgui.ListItem(title)
                    playlist.add(url=hostedurl, listitem=listitem)
                    xbmc.Player().play(playlist)
                    #return None
                else:
                    unplayable = True
            except Exception, e:
                unplayable = True

            if unplayable:
                #video not playable
                #show error message
                mvl_view_mode = 50
                hide_busy_dialog()
                showMessage('Error loading video', 'This source will not play. Please pick another.')
                return None

        else:
            hide_busy_dialog()
            pass
    else:
        mvl_view_mode = 50
        dialog_msg()
        hide_busy_dialog()

def create_meta(video_type, title, year, thumb):
    try:
        year = int(year)
    except:
        year = 0
    year = str(year)
    meta = {'title': title, 'year': year, 'imdb_id': '', 'overlay': ''}
    try:
        if video_type == 'tvshow':
            meta = __metaget__.get_meta(video_type, title)
            if not (meta['imdb_id'] or meta['tvdb_id']):
                meta = __metaget__.get_meta(video_type, title, year=year)

        else:  # movie
            meta = __metaget__.get_meta(video_type, title, year=year)
            alt_id = meta['tmdb_id']

        if video_type == 'tvshow':
            meta['cover_url'] = meta['banner_url']
        if meta['cover_url'] in ('/images/noposter.jpg', ''):
            meta['cover_url'] = thumb
            
        # print 'Done TV'
        # print meta
        
    except Exception, e:
        plugin.log.info('Error assigning meta data for %s %s %s' % (video_type, title, year))
        plugin.log.info(e)
        traceback.print_exc()

    return meta


def login_check():
    try:
        url = server_url + "/api/index.php/api/authentication_api/authenticate_user"
        #urlencode is used to create a json object which will be sent to server in POST
        data = urllib.urlencode({'username': '{0}'.format(username), 'activation_key': '{0}'.format(activation_key),
                                 'mac_address_flag': 'false',
                                 'mac_address': '{0}'.format(usrsettings.getSetting('mac_address'))})
        req = urllib2.Request(url, data)
        plugin.log.info(url)
        plugin.log.info(data)
        opener = urllib2.build_opener()
        f = opener.open(req)
        #reading content fetched from the url
        content = f.read()

        #converting to json object
        plugin.log.info("Debug_Content: " + content)
        myObj = json.loads(content)
        plugin.log.info(myObj)

        #creating items from json object
        for row in myObj:
            if row['status'] == 1:
                return True
            else:
                # xbmc.executebuiltin('Notification(License Limit Reached,' + row['message'] + ')')
                showMessage('Error', 'License Limit Reached, '+ row['message'])
                return False
    except IOError:
        # xbmc.executebuiltin('Notification(Unreachable Host,Could not connect to server,5000,/error.png)')
        dialog_msg()
    pass


@plugin.route('/search/<category>/')
def search(category):
    global mvl_view_mode

    if check_internet():
        
        if not show_notification():
        
            try:
                search_string = plugin.keyboard(heading=('search'))
                
                #if nothing was typed, return without doing anything
                if search_string is None or search_string == '' :
                    mvl_view_mode = 59
                    hide_busy_dialog()
                    return None

                url = server_url + "/api/index.php/api/categories_api/searchVideos"

                plugin.log.info(url)
                data = urllib.urlencode({'keywords': '{0}'.format(search_string), 'category': '{0}'.format(category)})
                req = urllib2.Request(url, data)
                plugin.log.info("search url")
                plugin.log.info(data)
                plugin.log.info(url)

                dp = xbmcgui.DialogProgress()

                f = urllib2.urlopen(req)
                response = f.read()
                if response == '0':
                    # xbmc.executebuiltin('Notification(Sorry,No Videos Found Matching Your Query,5000,/error.png)')
                    showMessage('No result found', 'Sorry, No Videos Found Matching Your Query')
                    mvl_view_mode = 59
                    hide_busy_dialog()

                else:
                    mvl_view_mode = 58
                    xbmcplugin.setContent(pluginhandle, 'Movies')

                    jsonObj = json.loads(response)
                    plugin.log.info(jsonObj)
                    items = []
                    item_count = len(jsonObj)
                    done_count = 0
                    dp_created = False
                    dp_type = 'show'
                    
                    for categories in jsonObj:
                        if categories['is_playable'] == 'False':
                            if categories['top_level_parent'] == '3' and categories['parent_id'] not in ('32', '3'):  # Parsing the TV Shows Titles & Seasons only:      # if TV Series fetch there fan art
                                tmpTitle = categories['title'].encode('utf-8')
                                mvl_meta = ''
                                if tmpTitle == "Season 1":
                                    tmpSeasons = []
                                    mvl_view_mode = 50
                                    # for i in range(totalCats):
                                    # tmpSeasons.append( i )
                                    #plugin.log.info('season found')
                                    #mvl_meta = __metaget__.get_seasons(mvl_tvshow_title, '', tmpSeasons)
                                else:
                                    mvl_meta = create_meta('tvshow', categories['title'].encode('utf-8'), '', '')
                                    mvl_tvshow_title = categories['title'].encode('utf-8')

                                dp_type = 'show'

                                plugin.log.info('meta data-> %s' % mvl_meta)
                                thumbnail_url = ''
                                try:
                                    if mvl_meta['cover_url']:
                                        thumbnail_url = mvl_meta['cover_url']
                                except:
                                    thumbnail_url = ''

                                fanart_url = ''
                                try:
                                    if mvl_meta['backdrop_url']:
                                        fanart_url = mvl_meta['backdrop_url']
                                except:
                                    fanart_url = ''

                                mvl_plot = ''
                                try:
                                    if mvl_meta['plot']:
                                        mvl_plot = mvl_meta['plot']
                                except:
                                    mvl_plot = ''

                                items += [{
                                              'label': '{0}'.format(categories['title'].encode('utf-8')),
                                              'path': plugin.url_for('get_categories', id=categories['id'], page=0),
                                              'is_playable': False,
                                              'thumbnail': thumbnail_url,
                                              'properties': {
                                                  'fanart_image': fanart_url,
                                              },
                                              'context_menu': [(
                                                                   'Add to Favourites',
                                                                   'XBMC.RunPlugin(%s)' % plugin.url_for('save_favourite',
                                                                                                         id=categories['id'],
                                                                                                         title=categories['title'].encode('utf-8'),
                                                                                                         thumbnail="None",
                                                                                                         isplayable="False",
                                                                                                         category=categories['top_level_parent'])
                                                               )],
                                              'replace_context_menu': True
                                          }]

                            else:                    
                                items += [{
                                              'label': '{0}'.format(categories['title'].encode('utf-8')),
                                              'path': plugin.url_for('get_categories', id=categories['id'], page=0),
                                              'is_playable': False,
                                              'thumbnail': art('{0}.png'.format(categories['title'].lower())),
                                              'context_menu': [(
                                                                   'Add to Favourites',
                                                                   'XBMC.RunPlugin(%s)' % plugin.url_for('save_favourite',
                                                                                                         id=categories['id'],
                                                                                                         title=categories['title'],
                                                                                                         thumbnail="None",
                                                                                                         isplayable="False",
                                                                                                         category=category)
                                                               )],
                                              'replace_context_menu': True
                                          }]
                        elif categories['is_playable'] == 'True':
                            categories['title'] = categories['title'].encode('utf-8')
                            thumbnail_url = categories['thumbnail']

                            dp_type = 'movie'
                            
                            mvl_img = thumbnail_url
                            mvl_meta = create_meta('movie', categories['title'], '', thumbnail_url)
                            plugin.log.info('meta data-> %s' % mvl_meta)
                            thumbnail_url = ''
                            try:
                                if mvl_meta['cover_url']:
                                    thumbnail_url = mvl_meta['cover_url']
                            except:
                                thumbnail_url = thumbnail_url
                            if thumbnail_url == '':
                                thumbnail_url = art('image-not-available.png')

                            fanart_url = ''
                            try:
                                if mvl_meta['backdrop_url']:
                                    fanart_url = mvl_meta['backdrop_url']
                            except:
                                fanart_url = ''

                            mvl_plot = ''
                            try:
                                if mvl_meta['plot']:
                                    mvl_plot = mvl_meta['plot']
                            except:
                                mvl_plot = categories['synopsis'].encode('utf-8')

                            items += [{
                                          'thumbnail': thumbnail_url,
                                          'properties': {
                                              'fanart_image': fanart_url,
                                          },
                                          'label': '{0}'.format(categories['title']),
                                          'info': {
                                              'title': categories['title'],
                                              'rating': categories['rating'],
                                              'comment': categories['synopsis'].encode('utf-8'),
                                              'Director': categories['director'].encode('utf-8'),
                                              'Producer': categories['producer'],
                                              'Writer': categories['writer'],
                                              'plot': mvl_plot,
                                              'genre': categories['sub_categories_names'],
                                              'cast': categories['actors'].encode('utf-8'),
                                              'year': categories['release_date']
                                          },
                                          'path': plugin.url_for('get_videos', id=categories['video_id'], thumbnail=thumbnail_url),
                                          'is_playable': False,
                                          'context_menu': [(
                                                               'Add to Favourites',
                                                               'XBMC.RunPlugin(%s)' % plugin.url_for('save_favourite',
                                                                                                     id=categories['video_id'],
                                                                                                     title=categories['title'],
                                                                                                     thumbnail=thumbnail_url,
                                                                                                     isplayable="True",
                                                                                                     category=categories['top_level_parent'])
                                                           )],
                                          'replace_context_menu': True
                                      }]
                                      

                        if categories['id'] != -1:
                            if categories['top_level_parent'] == '1':
                                dp_type = 'movie'
                            elif categories['top_level_parent'] == '3':
                                dp_type = 'show'
                                      
                        if dp_created == False:
                            dp.create("Please wait while "+dp_type+" list is loaded","","")
                            dp_created = True
                                  
                        done_count = done_count + 1
                        dp.update((done_count*100/item_count), "This wont happen next time you visit.",  str(done_count)+" of "+str(item_count)+" "+dp_type+"s loaded so far.")

                        if dp.iscanceled():
                            break                                 
                            
                    dp.close()

                    hide_busy_dialog()
                    return items
            except IOError:
                # xbmc.executebuiltin('Notification(Unreachable Host,Could not connect to server,5000,/script.hellow.world.png)')
                dialog_msg()
                hide_busy_dialog()
                
            except Exception,e:
                mvl_view_mode = 59
                hide_busy_dialog()
                return None
            
    else:
        mvl_view_mode = 59
        dialog_msg()
        hide_busy_dialog()




@plugin.route('/azlisting/<category>/')
def azlisting(category):
    global mvl_view_mode
    
    if check_internet():
    
        show_notification()    
        
        mvl_view_mode = 50
        Indices = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                   'V', 'W', 'X', 'Y', 'Z']
        items = [{
                     'label': '#',
                     'thumbnail': art('hash.png'),
                     'path': plugin.url_for('get_azlist', key='%23', page=0, category=category),
                     'is_playable': False,
                 }]
        for index in Indices:
            items += [{
                          'label': '{0}'.format(index),
                          'thumbnail': art('{0}.png'.format(index)),
                          'path': plugin.url_for('get_azlist', key=index, page=0, category=category),
                          'is_playable': False,
                      }]
                      
        hide_busy_dialog()
        return items
    else:
        mvl_view_mode = 59
        dialog_msg()
        hide_busy_dialog()


@plugin.route('/get_azlist/<key>/<page>/<category>/')
def get_azlist(key, page, category):
    global mvl_view_mode
    mvl_view_mode = 50
    page_limit_az = 200
    
    if check_internet():
    
        show_notification()    
    
        try:

            dp = xbmcgui.DialogProgress()
        
            url = server_url + "/api/index.php/api/categories_api/getAZList?key={0}&limit={1}&page={2}&category={3}".format(key, page_limit_az, page, category)
            plugin.log.info("here is the url")
            plugin.log.info(url)
            req = urllib2.Request(url)
            opener = urllib2.build_opener()
            f = opener.open(req)
            content = f.read()
            if content != '0':
                jsonObj = json.loads(content)
                items = []
                item_count = len(jsonObj)
                done_count = 0
                dp_created = False
                dp_type = 'show'
                
                ###########
                #if the items are season episodes, we need ot sort them naturally i.e. use Natural Sort for sorting
                if key == '%23':               
                    for results in jsonObj:
                        if 'title' not in results:
                            results['title'] = '999999999'
                        
                        title = results['title'].split(' ')[0]
                        title_token = ''
                        for c in title:
                            if c >= '0' and c <= '9':
                                title_token += c
                            elif c == ',':
                                continue
                            else:
                                break
                                
                        if title_token == '':
                            title_token = '999999999'
                        
                        if title_token[0] == '0':
                            title_token = '0'
                        
                        results['sort_key'] = title_token
                        results['sort_key_len'] = len(title_token)
                    
                    jsonObj.sort(key=lambda x: (x['sort_key_len'], x['sort_key']))
                
                    
                ###########

                xbmcplugin.setContent(pluginhandle, 'Movies')

                for results in jsonObj:
                    if results['id'] == -1:
                        items += [{
                                      'label': 'Next >>',
                                      'path': plugin.url_for('get_azlist', key=key, page=(int(page) + 1),
                                                             category=category),
                                      'thumbnail': art('next.png'),
                                      'is_playable': False,
                                  }]
                    elif results['is_playable'] == 'False':
                        if results['parent_id'] not in ('32', '23'):  # if not Genres then show them
                            if results['top_level_parent'] == '3':      # if TV Series fetch there fan art
                                tmpTitle = results['title'].encode('utf-8')

                                mvl_meta = ''
                                if tmpTitle == "Season 1":
                                    tmpSeasons = []
                                    mvl_view_mode = 50
                                    # for i in range(totalCats):
                                    # tmpSeasons.append( i )
                                    #plugin.log.info('season found')
                                    #mvl_meta = __metaget__.get_seasons(mvl_tvshow_title, '', tmpSeasons)
                                else:
                                    mvl_meta = create_meta('tvshow', results['title'].encode('utf-8'), '', '')
                                    mvl_tvshow_title = results['title'].encode('utf-8')

                                dp_type = 'show'

                                plugin.log.info('meta data-> %s' % mvl_meta)
                                thumbnail_url = ''
                                try:
                                    if mvl_meta['cover_url']:
                                        thumbnail_url = mvl_meta['cover_url']
                                except:
                                    thumbnail_url = ''

                                fanart_url = ''
                                try:
                                    if mvl_meta['backdrop_url']:
                                        fanart_url = mvl_meta['backdrop_url']
                                except:
                                    fanart_url = ''

                                mvl_plot = ''
                                try:
                                    if mvl_meta['plot']:
                                        mvl_plot = mvl_meta['plot']
                                except:
                                    mvl_plot = ''

                                items += [{
                                              'label': '{0}'.format(results['title'].encode('utf-8')),
                                              'path': plugin.url_for('get_categories', id=results['id'], page=0),
                                              'is_playable': False,
                                              'thumbnail': thumbnail_url,
                                              'properties': {
                                                  'fanart_image': fanart_url,
                                              },
                                              'context_menu': [(
                                                                   'Add to Favourites',
                                                                   'XBMC.RunPlugin(%s)' % plugin.url_for('save_favourite',
                                                                                                         id=results['id'],
                                                                                                         title=results['title'].encode('utf-8'),
                                                                                                         thumbnail="None",
                                                                                                         isplayable="False",
                                                                                                         category=results[
                                                                                                             'top_level_parent'])
                                                               )],
                                              'replace_context_menu': True
                                          }]

                            else:
                                items += [{
                                              'label': '{0}'.format(results['title'].encode('utf-8')),
                                              'path': plugin.url_for('get_categories', id=results['id'], page=0),
                                              'is_playable': False,
                                              'thumbnail': art('{0}.png'.format(results['title'].lower())),
                                              'context_menu': [(
                                                                   'Add to Favourites',
                                                                   'XBMC.RunPlugin(%s)' % plugin.url_for('save_favourite',
                                                                                                         id=results['id'],
                                                                                                         title=results['title'].encode('utf-8'),
                                                                                                         thumbnail="None",
                                                                                                         isplayable="False",
                                                                                                         category=category)
                                                               )],
                                              'replace_context_menu': True
                                          }]

                    elif results['is_playable'] == 'True':
                        results['title'] = results['title'].encode('utf-8')
                        thumbnail_url = results['thumbnail']

                        dp_type = 'movie'

                        mvl_img = thumbnail_url
                        #print "TITLE = " + results['title']
                        mvl_meta = create_meta('movie', results['title'], '', thumbnail_url)
                        plugin.log.info('meta data-> %s' % mvl_meta)
                        thumbnail_url = ''
                        try:
                            if mvl_meta['cover_url']:
                                thumbnail_url = mvl_meta['cover_url']
                        except:
                            thumbnail_url = thumbnail_url

                        fanart_url = ''
                        try:
                            if mvl_meta['backdrop_url']:
                                fanart_url = mvl_meta['backdrop_url']
                        except:
                            fanart_url = ''

                        mvl_plot = ''
                        try:
                            if mvl_meta['plot']:
                                mvl_plot = mvl_meta['plot']
                        except:
                            mvl_plot = results['synopsis'].encode('utf-8')

                        items += [{
                                      'thumbnail': thumbnail_url,
                                      'properties': {
                                          'fanart_image': fanart_url,
                                      },
                                      'label': '{0}'.format(results['title']),
                                      'info': {
                                          'title': results['title'],
                                          'rating': results['rating'],
                                          'comment': results['synopsis'].encode('utf-8'),
                                          'Director': results['director'].encode('utf-8'),
                                          'Producer': results['producer'],
                                          'Writer': results['writer'],
                                          'plot': mvl_plot,
                                          'genre': results['sub_categories_names'],
                                          'cast': results['actors'].encode('utf-8'),
                                          'year': results['release_date']
                                      },
                                      'path': plugin.url_for('get_videos', id=results['video_id'],
                                                             thumbnail=results['thumbnail']),
                                      'is_playable': False,
                                      'context_menu': [(
                                                           'Add to Favourites',
                                                           'XBMC.RunPlugin(%s)' % plugin.url_for('save_favourite',
                                                                                                 id=results['video_id'],
                                                                                                 title=results['title'],
                                                                                                 thumbnail=thumbnail_url,
                                                                                                 isplayable="True",
                                                                                                 category=results['top_level_parent'])
                                                       )],
                                      'replace_context_menu': True
                                  }]

                    if results['id'] != -1:
                        if results['top_level_parent'] == '1':
                            dp_type = 'movie'
                        elif results['top_level_parent'] == '3':
                            dp_type = 'show'
                        
                    if dp_created == False:
                        dp.create("Please wait while "+dp_type+" list is loaded","","")
                        dp_created = True
                                  
                    done_count = done_count + 1
                    dp.update((done_count*100/item_count), "This wont happen next time you visit.",  str(done_count)+" of "+str(item_count)+" "+dp_type+"s loaded so far.")

                    if dp.iscanceled():
                        break
                    
                # plugin.log.info('itemcheck')
                # plugin.log.info(items)
                
                dp.close()
                
                hide_busy_dialog()
                return items
            else:
                # xbmc.executebuiltin('Notification(Sorry,No Videos Available In this Category,5000,/error.png)')
                showMessage('No result found', 'Sorry, No Videos Available In this Category')
                hide_busy_dialog()
        except IOError:
            # xbmc.executebuiltin('Notification(Unreachable Host,Could not connect to server,5000,/script.hellow.world.png)')
            dialog_msg()
            hide_busy_dialog()
            
    else:
        mvl_view_mode = 59
        dialog_msg()
        hide_busy_dialog()


@plugin.route('/mostpopular/<page>/<category>/')
def mostpopular(page, category):
    global mvl_view_mode
    mvl_view_mode = 50
    try:

        dp = xbmcgui.DialogProgress()
        
        page_limit_mp = 30
    
        url = server_url + "/api/index.php/api/categories_api/getMostPopular?limit={0}&page={1}&category={2}".format(page_limit_mp, page, category)
        plugin.log.info(url)
        req = urllib2.Request(url)
        opener = urllib2.build_opener()
        f = opener.open(req)
        content = f.read()
        if content != '0':
            jsonObj = json.loads(content)
            items = []
            item_count = len(jsonObj)
            done_count = 0
            dp_created = False
            dp_type = 'show'

            for results in jsonObj:
                if results['id'] == -1:
                    items += [{
                                  'label': 'Next >>',
                                  'path': plugin.url_for('mostpopular', page=(int(page) + 1)),
                                  'is_playable': False,
                              }]
                else:
                    if results['source'] == '1':
                        thumbnail_url = results['image_name']
                    else:
                        thumbnail_url = server_url + '/wp-content/themes/twentytwelve/images/{0}'.format(
                            results['id'] + results['image_name'])

                    results['title'] = results['title'].encode('utf-8')

                    dp_type = 'movie'

                    mvl_meta = create_meta('movie', results['title'], results['release_date'], thumbnail_url)
                    plugin.log.info('meta data-> %s' % mvl_meta)
                    thumbnail_url = ''
                    try:
                        if mvl_meta['cover_url']:
                            thumbnail_url = mvl_meta['cover_url']
                    except:
                        thumbnail_url = thumbnail_url

                    fanart_url = ''
                    try:
                        if mvl_meta['backdrop_url']:
                            fanart_url = mvl_meta['backdrop_url']
                    except:
                        fanart_url = ''
                    items += [{
                                  'label': '{0}'.format(results['title']),
                                  'thumbnail': thumbnail_url,
                                  'properties': {
                                      'fanart_image': fanart_url,
                                  },
                                  'path': plugin.url_for('get_videos', id=results['id'], thumbnail=thumbnail_url),
                                  'is_playable': False,
                                  'context_menu': [(
                                                       'Add to Favourites',
                                                       'XBMC.RunPlugin(%s)' % plugin.url_for('save_favourite',
                                                                                             id=results['id'],
                                                                                             title=results['title'],
                                                                                             thumbnail=thumbnail_url,
                                                                                             isplayable="True",
                                                                                             category=category)
                                                   )],
                                  'replace_context_menu': True
                              }]

                if results['id'] != -1:
                    if results['top_level_parent'] == '1':
                        dp_type = 'movie'
                    elif results['top_level_parent'] == '3':
                        dp_type = 'show'
                    
                if dp_created == False:
                    dp.create("Please wait while "+dp_type+" list is loaded","","")
                    dp_created = True
                              
                done_count = done_count + 1
                dp.update((done_count*100/item_count), "This wont happen next time you visit.",  str(done_count)+" of "+str(item_count)+" "+dp_type+"s loaded so far.")

                if dp.iscanceled():
                    break
            
            dp.close()
            
            hide_busy_dialog()
            return items
        else:
            # xbmc.executebuiltin('Notification(Sorry,No Videos Available In this Category,5000,/error.png)')
            showMessage('No result found', 'Sorry, No Videos Available In this Category')
            hide_busy_dialog()
    except IOError:
        # xbmc.executebuiltin('Notification(Unreachable Host,Could not connect to server,5000,/script.hellow.world.png)')
        dialog_msg()
        hide_busy_dialog()


def init_database():
    plugin.log.info('Building My Video Library Database')
    if not xbmcvfs.exists(os.path.dirname(DB_DIR)):
        xbmcvfs.mkdirs(os.path.dirname(DB_DIR))
    db = orm.connect(DB_DIR)
    db.execute(
        'CREATE TABLE IF NOT EXISTS favourites (id, title, thumbnail, isplayable, category, PRIMARY KEY (id, title, category))')
    db.commit()
    db.close()


@plugin.route('/save_favourite/<id>/<title>/<thumbnail>/<isplayable>/<category>')
def save_favourite(id, title, thumbnail, isplayable, category):
    plugin.log.info(id)
    plugin.log.info(title)
    plugin.log.info(thumbnail)
    plugin.log.info(isplayable)
    plugin.log.info(category)
    try:
        statement = 'INSERT OR IGNORE INTO favourites (id, title, thumbnail, isplayable, category) VALUES (%s,%s,%s,%s,%s)'
        db = orm.connect(DB_DIR)
        statement = statement.replace("%s", "?")
        cursor = db.cursor()
        cursor.execute(statement, (id, title, thumbnail, isplayable, category))
        db.commit()
        db.close()
    except:
        # xbmc.executebuiltin('Notification(Database Error, Please contact software provider,5000,/script.hellow.world.png)')
        showMessage('Database Error', 'Please contact software provider') 


@plugin.route('/remove_favourite/<id>/<title>/<category>')
def remove_favourite(id, title, category):
    statement = 'DELETE FROM favourites WHERE id=%s AND title=%s AND category=%s'
    db = orm.connect(DB_DIR)
    statement = statement.replace("%s", "?")
    cursor = db.cursor()
    cursor.execute(statement, (id, title, category))
    db.commit()
    db.close()
    return xbmc.executebuiltin("XBMC.Container.Refresh()")


def sys_exit():
    hide_busy_dialog()
    plugin.finish(succeeded=True)
    xbmc.executebuiltin("XBMC.ActivateWindow(Home)")


@plugin.route('/get_favourites/<category>/')
def get_favourites(category):
    global mvl_view_mode
    mvl_view_mode = 50
    statement = 'SELECT * FROM favourites WHERE category = "%s"' % category
    plugin.log.info(statement)
    db = orm.connect(DB_DIR)
    cur = db.cursor()
    cur.execute(statement)
    favs = cur.fetchall()
    items = []
    plugin.log.info(favs)
    for row in favs:
        plugin.log.info(row[0])
        if row[3] == 'False':
            items += [{
                          'label': '{0}'.format(row[1]),
                          'thumbnail': row[2],
                          'path': plugin.url_for('get_categories', id=row[0], page=0),
                          'is_playable': False,
                          'context_menu': [(
                                               'Remove from Favourites',
                                               'XBMC.RunPlugin(%s)' % plugin.url_for('remove_favourite', id=row[0],
                                                                                     title=row[1], category=row[4])
                                           )],
                          'replace_context_menu': True
                      }]
        elif row[3] == 'True':
            items += [{
                          'label': '{0}'.format(row[1]),
                          'thumbnail': row[2],
                          'path': plugin.url_for('get_videos', id=row[0], thumbnail=row[2]),
                          'is_playable': False,
                          'context_menu': [(
                                               'Remove from Favourites',
                                               'XBMC.RunPlugin(%s)' % plugin.url_for('remove_favourite', id=row[0],
                                                                                     title=row[1], category=row[4])
                                           )],
                          'replace_context_menu': True
                      }]
    db.close()
    hide_busy_dialog()
    return items


if __name__ == '__main__':
    plugin.run()
    xbmc.executebuiltin("Container.SetViewMode(%s)" % mvl_view_mode)

