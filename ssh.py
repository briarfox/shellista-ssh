import modules.pysftp as pysftp
import cmd
import getpass
import os
import sys
from modules.docopt import docopt,DocoptExit
import modules.Keys as Keys
import StringIO
import modules.shortcuts as shortcuts
from tempfile import TemporaryFile
#import modules.patchparamiko
from modules.edit import edit_file,clear_file
import re

HOME = os.path.expanduser('~/Documents')
DIR = os.path.expanduser('~/Documents/.ssh')
KEY = 'id_ssh_key'
key_mode = {'RSA': 'rsa',
            'DSA': 'dss'}
            
#decorator for args
def docopt_arg(func):
    '''          
    This decorator is used to simplify the try/except block and pass the result
    of the docopt parsing to the called action.
    '''
    def fn(self, arg):
        try:
            opt = docopt(fn.__doc__, arg)

        except DocoptExit as e:
            # The DocoptExit is thrown when the args do not match.
            # We print a message to the user and the usage block.

            print('Invalid Command!')
            print(e)
            return

        except SystemExit:
            # The SystemExit exception prints the usage for --help
            # We do not need to do the print here.

            return

        return func(self, opt)

    fn.__name__ = func.__name__
    fn.__doc__ = func.__doc__
    fn.__dict__.update(func.__dict__)
    return fn


def _parse_host(host):
    result = re.match(r'(.*)@(.*)',host)
    return result.group(1),result.group(2)

'''    
#parse ignore list for scp
def parse_ignore(args):
    tmp_list = []
    ignore_list=[]
    ignore_found = False
    for arg in args:
        if arg=='-i' or arg=='--ignore':
            ignore_found = True
        elif ignore_found==False:
            tmp_list.append(arg)
        else:
            ignore_list.append(arg)
    tmp_list.append(ignore_list)
    return tmp_list
'''


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
            if result:
                for line in result:
                    print line,
        else:
            print '***Invalid Command***'
            
######################################

#Edit shortcuts
    @docopt_arg
    def do_shortcut(self,line):
        '''
Creates shortcuts that can be used to store commands and paths
To use a shortcut call $your_shortcut

    Usage: shortcut (list|edit)
        '''
        if line['edit']:
            shortcuts.edit_shortcuts()
        if line=='list':
            shortcuts.list_shortcuts()
        return
    
    def do_alias(self,line):
        '''see shortcut'''
        self.do_shortcut(line)


#handle editing from remote
    @docopt_arg
    def do_edit(self, line):
        '''
Opens a remote file in pythonista's editor. When the console is reopened, save confimation will be requested.
            
Usage: edit <path>
        
        '''
        if self.connected:
            try:
                buff = TemporaryFile()
                self.client.getfo(line['<path>'], buff)
                buff.seek(0)
                result = edit_file(buff)
                if result:
                    self.client.putfo(result,line['<path>'])
                    clear_file()
            except:
                print 'No file found at given path'
                return
        else:
            return
            
            
    def do_nano(self,line):
        '''
See edit
        
        '''
        self.do_edit(line)
            
    @docopt_arg        
    def do_editkey(self,line):
        '''
Opens up the ssh key in the editor.
        
Usage: editkey (public|private)
        '''
        if line['public']:
            result = edit_file(open(DIR+'/id_ssh_key.pub.txt','r'))
            if result:
                open(DIR+'id_ssh_key.pub.txt','w').write(result.read())
        if line['private']:
            result = edit_file(open(DIR+'/id_ssh_key.txt','r'))
            if result:
                open(DIR+'id_ssh_key.txt','w').write(result.read())
    
    @docopt_arg    
    def do_scp(self,line):
        '''
        scp - secure copy
        
        host: designates remote location
        $LOCAL Designates pythonista Documents directory.
        $REMOTE Designates host user directory
        Example:
            scp $LOCAL/projects/folder host:remote/dir
            scp local/project/test.py host:$REMOTE/remote/project/test.py
        
        Usage:
            scp <copy_from> <copy_to> [--ignore <files>...]
            
            
        Options:
            -i, --ignore        Flag to ignore files/folders. Used without following <files> will default to .git, .svn     
        '''
        
            
        if self.connected:
            #callback for scp
            _ignore = []
            if line['--ignore']:
                if line['<files>']:
                    _ignore = line['<files>']
                else:
                    _ignore = ['.git','.svn']
                
            def _callback(copy_from,copy_to):
                print copy_to
                
            mode = ''
            if 'host:' in line['<copy_from>']:
                line['<copy_from>'] = line["<copy_from>"][5:]
                mode = 'GET'
            if 'host:' in line['<copy_to>']:
                line['<copy_to>'] = line["<copy_to>"][5:]
                mode = 'PUT'
            
            #get current directories
            cur_local = os.getcwd()
            cur_remote = self.client.pwd
            if mode == 'GET':
                if self.client.isdir(line['<copy_from>']):
                    self.client.chdir(line['<copy_from>'])
                    os.chdir(line['<copy_to>'])
                    self.client.get_r('.','.',ignore=_ignore,callback=_callback)
                else:
                    remote_base,remote_head = os.path.split(line['<copy_from>'])
                    local_base,local_head = os.path.split(line['<copy_to>'])
    
                    if local_base!='':
                        os.chdir(local_base)
                    if remote_base!='':
                        self.client.chdir(remote_base)
                    self.client.get(remote_head,local_head)
            elif mode == 'PUT':
                if os.path.isdir(line['<copy_from>']):
                    self.client.chdir(line['<copy_to>'])
                    os.chdir(line['<copy_from>'])
                    self.client.put_r('.','.',ignore=_ignore,callback=_callback)
                else:
                    remote_base,remote_head = os.path.split(line['<copy_to>'])
                    local_base,local_head = os.path.split(line['<copy_from>'])
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
    @docopt_arg
    def do_connect(self, line):
        '''
Connect to ssh server
Example:
    connect $shortcut_name
    connect user@host --port=8090

Usage: 
    connect <server> [--port=<port>]

Options:
    -p <port>, --port=<port>        Specify the port [default: 22]
'''
    #get username and host
        if '@' in line['<server>']:
            self.user, self.host = _parse_host(line['<server>'])
        else:
            print '**Invalid Usage**'
            return
            
        _port = int(line['--port'])

        
        pkey = DIR+'/'+KEY+'.txt'
        print 'connecting to host...'
        try:
            self.client = pysftp.Connection(self.host,port=_port,username=self.user,private_key=pkey)
            print 'Key authenticated. Connected as %s on %s' % (self.user,self.host)
            self.connected = True
            self.prompt = self.user+'@'+self.host+'>'
        except:
            try: 
                self.passwd = getpass.getpass('password: ')
                self.client = pysftp.Connection(self.host,port=_port,username=self.user,private_key=pkey, private_key_pass=self.passwd)
                print 'Key authenticated. Connected as %s on %s' % (self.user, self.host)
                self.connected = True
                self.prompt = self.user+'@'+self.host+'>'
            except Exception, e:
                try:
                    self.client = pysftp.Connection(self.host,port=_port,username=self.user,password=self.passwd)
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
