import os

try:
    #read screen_lock files content
    file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'screen_lock.dat')
    f = open(file_path, 'r')
    content = f.read()
    f.close()
    
    if len(content) == 0:    
        #if screen_lock doesn't have any content, that means we are good to go
        xbmc.executebuiltin( "Action(back)" )

        path = xbmc.getInfoLabel('Container.FolderPath')

        if len(path.split('/')) >= 6:
            selection = path.split('/')[3]
            selection_id = path.split('/')[4]
            # xbmc.executebuiltin('Notification(Item, ' + selection + ' - ' + selection_id + ', 1)')
            
            if selection == 'categories' and (selection_id == '1' or selection_id == '3'):
                #we are in screen 1, set view mode to 58
                xbmc.executebuiltin( "Container.SetViewmode(58)" )
            elif (
                    selection == 'categories' and (selection_id == '23' or selection_id == '104916' or selection_id == '112504' or 
                    selection_id == '32' or selection_id == '104917' or selection_id == '366042' or selection_id == '372395' or selection_id == '372396')
                 ) or selection == 'azlisting' or selection == 'search':
                #we are in screen 2, set view mode to 59
                xbmc.executebuiltin( "Container.SetViewmode(59)" )


        # xbmc.executebuiltin('Notification(Item, ' + path + ', 1)')

except Exception, e:
    pass


