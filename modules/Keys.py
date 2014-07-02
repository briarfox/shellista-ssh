import os

DIR = os.path.expanduser('~/Documents/.ssh')
FILENAME = 'id_ssh_key'

#Keygen for keypair
def keygen(filename, password=None,typ='RSA', bits=1024):
    import paramiko
    import modules.patchparamiko
    try:
        if typ == 'RSA':
            k = paramiko.RSAKey.generate(bits)
        else:
            k = paramiko.DSSKey.generate(bits)
        k.write_private_key_file(DIR+'/'+FILENAME+'.txt', password=password)
        o = open(DIR+'/'+FILENAME+'.pub.txt', "w").write('ssh-'+key_mode[typ]+' '+k.get_base64())
        return True
    except:
        return False
