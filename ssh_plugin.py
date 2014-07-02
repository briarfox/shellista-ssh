'''
ssh:
    usage:
        editkey [private/public] - opens key files for editing
        keygen - Generates a new ssh key pair
        edithost - edit shortcuts to host names
        connect [-p port] user@host.com
'''

import ssh

alias=[]

def main(line):
    ssh.SSH().cmdloop()
    
if __name__=='__main__':
    main('')
