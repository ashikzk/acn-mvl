from xbmcswift2 import Plugin, xbmcgui, xbmc, xbmcaddon, xbmcplugin, actions
import time
import urllib2

dialog = xbmcgui.Dialog()

#show dialog message
ret = dialog.ok('Please wait...', 'Press the OK Button to begin the update. Please wait until it finishes.')

#if user has pressed OK, proceed with system update
if ret == 1:

    try:
        response = urllib2.urlopen('http://74.125.228.100', timeout=1)

        xbmc.executebuiltin( "UpdateAddonRepos()" )

        #freeze UI by showing a busy dialog
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )

        #wait for 30 seconds
        time.sleep(30)

        #make everything normal
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        
    except urllib2.URLError as err:
        heading = "INTERNET CONNECTION ISSUE"
        text = "Your internet connection has been lost. Please wait a few minutes and try again. If the error persists you may wish to contact your Internet Service Provider."
        dialog.ok(heading, text)
        
        pass

