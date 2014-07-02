# coding: utf-8

import ui
import os
import sys
import console
import editor


#TEMP = os.path.abspath(os.path.split(sys.argv[0])[0])
TEMP = os.path.relpath(os.path.realpath(os.path.dirname(__file__)),os.path.expanduser('~/Documents'))+'/tmp.txt'

CUR_PATH = os.path.relpath(os.path.realpath(os.path.dirname(sys.argv[0])),os.path.expanduser('~/Documents'))




def edit_file(file_to_edit):
    '''Open file in a temp text page to allow editing'''
    
    cur_path = editor.get_path()
    print cur_path
    #with open('tmp.txt', 'w') as file:
    try:
        file = open(os.path.dirname(__file__)+'/tmp.txt','w')
        file.write(file_to_edit.read())
        file.close()
        editor.reload_files()
        raw_input('*When you are finished editing the file, you must come back to console to confim changes*\n[Press Enter]')
        editor.open_file(TEMP)
        console.hide_output()
        while True:
            input = raw_input('Save Changes? Y,N: ')
            if input=='Y' or input=='y':
                editor.open_file(cur_path)
                return open(os.path.dirname(__file__)+'/tmp.txt','r')
            elif input=='N' or input=='n':
                editor.open_file(cur_path)
                return False

        
    except Exception, e:
        print e
        return False

            
def edit_host():
    '''Edits the host shortcut file.'''
    pass
    
if __name__=='__main__':
    print 'testing'
    f = open('test.py','r')
    fil = edit_file(f)
    if fil:
        with open('test.py','w') as file:
            file.write(fil.read())
    
    

    

