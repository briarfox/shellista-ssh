'''
ssh: open ssh shell.
'''

import ssh

alias=[]

def main(line):
    ssh.SSH().cmdloop()
    
if __name__=='__main__':
    main('')
