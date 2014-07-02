import modules.pysftp as pysftp
import cmd
import getpass
import os
import sys
import ui
import traceback
import StringIO
from tempfile import TemporaryFile
#import modules.patchparamiko
from modules.edit import edit_file
import re

HOME = os.path.expanduser('~/Documents')
DIR = os.path.expanduser('~/Documents/.ssh')
KEY = 'id_scp_key'
key_mode = {'RSA': 'rsa',
            'DSA': 'dss'}

def _parse_host(host):
    result = re.match(r'(.*)@(.*)',host)
    return result.group(1),result.group(2)

class SSH(cmd.Cmd):
    "SSH class for sshlista"
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.sshlista_path = os.path.dirname(os.path.realpath(__file__))
        self.connected = False
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
 
#catch help cmd when used in ssh       
    def precmd(self,line):
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
            print path
            result = self.client.execute('cd '+path+self.os_sign[self.operating_system] +line)
            for line in result:
                print line
        else:
            print '***Invalid Command***'
            
######################################


#handle editing from remote
    def do_edit(self, line):
        if self.connected:
            args = line.split(' ')
            if len(args) > 1:
                return
            print args[0]
            buff = TemporaryFile()
            self.client.getfo(args[0], buff)
            buff.seek(0)
            result = edit_file(buff)
            if result:
                self.client.putfo(result,args[0])
            
            
        else:
            return
        
    def do_scp(self,line):
        args = line.split(' ')
        if args[0]=='' or len(args) >2:
            return
        mode = ''
        if 'host:' in args[0]:
            print 'mode GET'
            args[0] = args[0][5:]
            mode = 'GET'
        elif 'host:' in args[1]:
            print 'mode PUT'
            args[1] = args[1][5:]
            mode = 'PUT'
        else:
            print '*Invalid Usage*'
            return
            
        print 'Global mode is '+mode
        if mode == 'GET':
            if self.client.isdir(args[0]):
                #check for $HOME
                cur_dir = os.getcwd()
                if '$HOME' in args[1]:
                    os.chdir(os.path.expanduser('~/Documents'))
                    args[1] = args[1][6:]
                path = args[0].split('/')
                print path[:-1]
                dir = path[len(path)-1]
                self.client.chdir(args[0])
                self.client.get_r('.',args[1])
                os.chdir(cur_dir)
            else:
                if '$HOME' in args[1]:
                    cur_dir = os.getcwd()
                    os.chdir(os.path.expanduser('~/Documents'))
                    args[1] = args[1][6:]
                self.client.get(args[0],args[1])
                os.chdir(cur_dir)
        elif mode == 'PUT':
            cur_dir = os.getcwd()
            if '$HOME' in args[0]:
                    cur_dir = os.getcwd()
                    os.chdir(os.path.expanduser('~/Documents'))
                    args[0] = args[0][6:]
                    print args[0]
            if os.path.isdir(args[0]):
                try:
                    import traceback
                    self.client.put_r(args[0],args[1])
                    os.chdir(cur_dir)
                except:
                    print traceback.format_exc()
            else:
                self.client.put(args[0],args[1])
                os.chdir(cur_dir)
        else:
            print sys.modules[__name__].__doc__
    
    
    
    
    
#Connect to the ssh server
    def do_connect(self, line):
        '''
connect:
usage: 
    connect saved_name
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
                print self.user, self.host
            else:
                print '**Invalid Usage**'
                return
        else:
            print '*Invalid Usage*'
            return
        
        pkey = DIR+'/'+KEY+'.txt'
        print pkey
        print self.user
        print self.host

        try:
            self.client = pysftp.Connection(self.host,username=self.user,private_key=pkey)
            print 'Key authenticated. Connected as %s on %s' % (self.user,self.host)
            self.connected = True
            self.prompt = self.user+'@'+self.host+'>'
        except:
            try: 
                passwd = getpass.getpass('password: ')
                self.client = pysftp.Connection(self.host,username=self.user,private_key=pkey, private_key_pass=passwd)
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
        "Exit"
        return True
            

            

if __name__ == '__main__':
    SSH().cmdloop()
