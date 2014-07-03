'''
ssh: open ssh shell.
'''

import ssh
__version__ = '0.1.0'
alias=[]

def main(self,line):
    ssh.SSH().cmdloop()
    return
    

