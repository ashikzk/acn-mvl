import xbmc

file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'quit_log.dat')
f = open(file_path, 'w')
f.write('true')
f.close()

xbmc.executebuiltin( "Quit()" )

