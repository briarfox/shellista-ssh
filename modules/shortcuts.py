from ConfigParser import SafeConfigParser
import os
from edit import edit_file

PATH = os.path.expanduser('~/Documents')
FILE = '.ssh_shortcuts.cfg' 

CONFIG_TEMPLATE = '''
########################################################################################
##                            Config for shellista-ssh                                ##
########################################################################################

# '$' should preceed all shortcuts

#format: $shortcut = some string of commands

# $LOCAL - shortcut for pythonista's documents
# $REMOTE - shortcut for host's user

[shortcuts]
#The shortcut can be any string, including commands

#Examples:
#This will log into the server with ssh>@me
# $me = connect me@myhost.com  

#This will transfer a project from pythonista to remote host
# $putProjects = scp $LOCAL/projects/myproject host:$REMOTE/projects/my project 


'''
#parser = SafeConfigParser()
#parser.read('simple.ini')

#print parser.get('bug_tracker', 'url')

def edit_shortcuts():
    result = edit_file(open(PATH+'/'+FILE,'r'))
    if result:
        open(PATH+'/'+FILE,'w').write(result.read())
        
def list_shortcuts():
    parser = SafeConfigParser()
    parser.read(PATH+'/'+FILE)
    for option,value in parser.items('shortcuts'):
        print option+' - '+value

def parse_shortcuts(line):
    output = ''
    args = line.split(' ')
    parser = SafeConfigParser()
    parser.read(PATH+'/'+FILE)
    
    for arg in args:
        if '$' in arg and '$LOCAL' not in arg and '$REMOTE' not in arg:
            if parser.has_option('shortcuts',arg):
                output = output + parser.get('shortcuts',arg)+' '
        else:
            output = output+arg+' '
            
    return output
    

    
def _check_config():
    
    parser = SafeConfigParser()
    if not os.path.isfile(PATH+'/'+FILE):
        print 'Creating '+FILE
        f = open(PATH+'/'+FILE,'w')
        f.write(CONFIG_TEMPLATE)
        f.close()
        
_check_config()
