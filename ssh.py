import modules.pysftp as pysftp
import cmd
import getpass
import os
import sys
import ui
import modules.Keys as Keys
import traceback
import StringIO
import modules.shortcuts as shortcuts
from tempfile import TemporaryFile
#import modules.patchparamiko
from modules.edit import edit_file
import re

HOME = os.path.expanduser('~/Documents')
DIR = os.path.expanduser('~/Documents/.ssh')
KEY = 'id_ssh_key'
key_mode = {'RSA': 'rsa',
            'DSA': 'dss'}

def _parse_host(host):
    result = re.match(r'(.*)@(.*)',host)
    return result.group(1),result.group(2)

class SSH(cmd.Cmd):
    "SSH class for sshlista"
    def __init__(self):
        check_key()
        cmd.Cmd.__init__(self)
        self.sshlista_path = os.path.dirname(os.path.realpath(__file__))
        self.connected = False
        self.local_home = os.path.expanduser('~/Documents')
        self.remote_home = ''
        self.os_sign = {'WINDOWS': ' & ','LINUX': ' ; '}
        self.user = ''
        self.host = ''
        self.port = '22'
        self.passwd = ''
        self.mode = 'None'
        self.prompt = 'ssh >'
        
        
        
########cmd module overrides#######
    def emptyline(self):
        return
        
    def _parse_home(self,line):
        if '$LOCAL' in line:
            line = line.replace('$LOCAL',self.local_home)
        if '$REMOTE' in line:
            line = line.replace('$REMOTE',self.remote_home)
        return line
 
#catch help cmd when used in ssh       
    def precmd(self,line):
        line = shortcuts.parse_shortcuts(line)
        line = self._parse_home(line)
        args = line.split(' ')
        if args[0] == 'help':
            if self.connected:
                path = self.client.pwd[2:0]
                result = self.client.execute(line)
                for line in result:
                    print line
        return line

#handle ssh commands        
    def default(self,line):
        '''
        Sends unrecognised command line to server.
        '''
        if self.connected:
            if self.operating_system == 'WINDOWS':
                path =  self.client.pwd[2:]
            else:
                path = self.client.pwd
        
            result = self.client.execute('cd '+path+self.os_sign[self.operating_system] +line)
            for line in result:
                print line
        else:
            print '***Invalid Command***'
            
######################################

#Edit shortcuts
    def do_shortcut(self,line):
        '''
Creates shortcuts that can be used to store commands and paths
To use a shortcut call $your_shortcut
    usage:
shortcut list|edit
        '''
        if line=='edit':
            shortcuts.edit_shortcuts()
        if line=='list':
            shortcuts.list_shortcuts()
        return


#handle editing from remote
    def do_edit(self, line):
        '''
        edit:
            Opens a remote file in pythonista's editor. When the console is reopened, save confimation will be requested.
            usage:
                edit path/on/remote
        '''
        if self.connected:
            try:
                args = line.split(' ')
                if len(args) > 1:
                    return
                buff = TemporaryFile()
                self.client.getfo(args[0], buff)
                buff.seek(0)
                result = edit_file(buff)
                if result:
                    self.client.putfo(result,args[0])
            except:
                print 'No file found at given path'
                return
            
            
        else:
            return
    def do_nano(self,line):
        '''
        nano:
            Opens a remote file in pythonista's editor. When the console is reopened, save confimation will be requested.
            usage:
                edit path/on/remote  
        '''
        self.do_edit(line)
            
    def do_editkey(self,line):
        '''
        editkey - Opens up the ssh key in the editor.
            usage:
                editkey [public/private]
        '''
        args = line.split(' ')
        if len(args) >1:
            return
        if args[0] == 'public':
            result = edit_file(open(DIR+'/id_ssh_key.pub.txt','r'))
            if result:
                open(DIR+'id_ssh_key.pub.txt','w').write(result.read())
        elif args[0] == 'private':
            result = edit_file(open(DIR+'/id_ssh_key.txt','r'))
            if result:
                open(DIR+'id_ssh_key.txt','w').write(result.read())
        else:
            return
        
    def do_scp(self,line):
        '''
        scp - secure copy
        scp copy_from copy_to
        
        host: designates remote location
        $LOCAL Designates pythonista Documents directory.
        $REMOTE Designates host user directory
        
            usage:
                scp host:projects/folder local/project
                scp $LOCAL/projects/folder host:remote/dir
                scp local/project/test.py host:$REMOTE/remote/project/test.py
        '''
        if self.connected:
            args = line.split(' ')
            if args[0]=='' or len(args) >2:
                return
            mode = ''
            if 'host:' in args[0]:
                args[0] = args[0][5:]
                mode = 'GET'
            elif 'host:' in args[1]:
                args[1] = args[1][5:]
                mode = 'PUT'
            else:
                print '*Invalid Usage*'
                return
            
            #get current directories
            cur_local = os.getcwd()
            cur_remote = self.client.pwd
            if mode == 'GET':
                if self.client.isdir(args[0]):
                    self.client.chdir(args[0])
                    os.chdir(args[1])
                    self.client.get_r('.','.')
                else:
                    remote_base,remote_head = os.path.split(args[0])
                    local_base,local_head = os.path.split(args[1])
    
                    if local_base!='':
                        os.chdir(local_base)
                    if remote_base!='':
                        self.client.chdir(remote_base)
                    self.client.get(remote_head,local_head)
            elif mode == 'PUT':
                if os.path.isdir(args[0]):
                    self.client.chdir(args[1])
                    os.chdir(args[0])
                    self.client.put_r('.','.')
                else:
                    remote_base,remote_head = os.path.split(args[1])
                    local_base,local_head = os.path.split(args[0])
                    if local_base!='':
                        os.chdir(local_base)
                    if remote_base!='':
                        self.client.chdir(remote_base)
                    self.client.put(local_head,remote_head)
            else:
                print sys.modules[__name__].__doc__
                
            #reset to current directories
            os.chdir(cur_local)
            self.client.chdir(cur_remote)
        else:
            print 'You must be connected to use this command.'
            return
    
    
    
    
    
#Connect to the ssh server
    def do_connect(self, line):
        '''
connect:
usage: 
    connect shortcut
    connect user@host
'''
        args = line.split(' ')
        if args[0] == '-P':
            self.port = args[1]
            args.pop(0) #pop -P
            args.pop(0) #pop port number
        
    #get username and host
        if len(args)==1:
            if '@' in args[0]:
                self.user, self.host = _parse_host(args[0])
                #args[0] = args[0].split(':')[1]
            else:
                print '**Invalid Usage**'
                return
        else:
            print '*Invalid Usage*'
            return
        
        pkey = DIR+'/'+KEY+'.txt'
        print 'connecting to host...'
        try:
            self.client = pysftp.Connection(self.host,username=self.user,private_key=pkey)
            print 'Key authenticated. Connected as %s on %s' % (self.user,self.host)
            self.connected = True
            self.prompt = self.user+'@'+self.host+'>'
        except:
            try: 
                self.passwd = getpass.getpass('password: ')
                self.client = pysftp.Connection(self.host,username=self.user,private_key=pkey, private_key_pass=self.passwd)
                print 'Key authenticated. Connected as %s on %s' % (self.user, self.host)
                self.connected = True
                self.prompt = self.user+'@'+self.host+'>'
            except Exception, e:
                try:
                    self.client = pysftp.Connection(self.host,username=self.user,password=self.passwd)
                    print 'Password Authenticated. Logged in as %s on %s' % (self.user, self.host)
                    self.connected = True
                    self.prompt = self.user+'@'+self.host+'>'
                except Exception, e:
                    print e
                    return
        #get home directory for remote
        self.remote_home = self.client.pwd
                    
        #get os 
        self.do_cd(' .')
        try:
            
            self.client.execute('ls')
            self.operating_system = 'LINUX'
            print 'Linux os'
        except :
        
            print 'Windows os'
            self.operating_system = 'WINDOWS'
            
    def do_cd(self,line):
        '''
        cd: change remote directory
        '''
        args = line.split(' ')
        if args[0] == '':
            return
        try:
            #print self.client.pwd()
            result = self.client.chdir(args[0])
            print result
        except :
            print 'Path does not exist.'
        return
            
            
    def do_disconnect(self,line):
        if self.connected:
            self.client.close()
            self.prompt = 'ssh >'
            self.connected = False
            
    def do_chdir(self,line):
        self.do_cd(line)
        
    def do_exit(self, line):
        return True
    def do_close(self,line):
        return self.do_exit(line)
        
        
def check_key():
    if not os.path.isdir(DIR):
        os.mkdir(DIR)
    if not os.path.isfile(DIR+'/'+KEY+'.txt'):
        print '*Keypair not found - generating key pair*'
        typ = raw_input('Key Type [RSA/DSA]: ')
        passwd = raw_input('RSA/DSA password [Blank for no password]: ')
        if passwd == '':
            passwd = None
        Keys.keygen(KEY, passwd,typ=typ)
        print 'Keypair has been generated'
        return
            

            

if __name__ == '__main__':
    SSH().cmdloop()
