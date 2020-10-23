import time
import os
import sys
from datetime import datetime
import subprocess
import paramiko

host = '182.222.81.199'
port = '2222'
username = 'pi'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

SENTRY_PATH = '/mnt/cam/TeslaCam/SentryClips'
SAVEDCAM_PATH = '/mnt/cam/TeslaCam/SavedClips'
#SENTRY_PATH = '/home/james/project/tesla/SentryClips'
#SAVEDCAM_PATH = '/home/james/project/tesla/SavedClips'
def wait(min):
    subprocess.call(['umount', '/mnt/cam'])
    time.sleep(min*60)
    subprocess.call(['mount', '/mnt/cam'])

def is_new_date(path, checkpoint):
    f = open(checkpoint, 'r')
    checkpoint_time = f.readline()
    if get_timestamp(path) > get_timestamp(checkpoint_time): 
        return True
    else:
        return False

def make_checkpoint(paths, checkpoint):
    temp = 0.0
    str_temp = ''
    for path in paths:
        if get_timestamp(path) > temp:
            temp = get_timestamp(path)
            str_temp = path
    f = open(checkpoint, 'w')
    f.write(str_temp)
    f.close()

def upload_for_sftp(root, paths, target_path):
    print(paths)
    if len(paths) == 0:
        return
    ssh.connect(host, username='pi', port=port, password='xxx')
    sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())

    for path in paths:
        print('send ' + path)
        try:
            sftp.stat('/media/hdd/TeslaCam/' + target_path + '/' + path)
        except:
            sftp.mkdir('/media/hdd/TeslaCam/' + target_path + '/' + path)
            send_files = get_event_files(root, path)
            for send_file in send_files:
                print(send_file)
                print('/media/hdd/TeslaCam/' + target_path + '/' + path + '/' + send_file.split('/')[-1])
                sftp.put(send_file, '/media/hdd/TeslaCam/' + target_path + '/' + path + '/' + send_file.split('/')[-1])

    sftp.close()
    ssh.close()

def get_event_files(root, path):
    files = os.listdir(root + '/' + path)
    files.sort(reverse=True)
    if len(files) >= 10:
        files = files[:10]
    else:
        files = files[:len(files)]

    for i in range(len(files)):
        files[i] = root + '/' + path  + '/' + files[i]
    return files

def get_timestamp(str_date):
    timestamp = time.mktime(datetime.strptime(str.strip(str_date), '%Y-%m-%d_%H-%M-%S').timetuple())
    return timestamp

def get_newcam_list(root, checkpoint):
    all_list = os.listdir(root)
    newcam_list = []

    if os.path.isfile(checkpoint) == True:
        for path in all_list:
            if is_new_date(path, checkpoint):
                newcam_list.append(path)
    else:
        newcam_list = all_list
    
    make_checkpoint(all_list, checkpoint)

    return newcam_list



if '__main__' == __name__:
     while(True):
        wait(3)
        #subprocess.call(['mount', '/mnt/cam'])
        cam_paths = get_newcam_list(SENTRY_PATH, '/home/pi/TeslaCam/SentryClips_Checkpoint')
        upload_for_sftp(SENTRY_PATH, cam_paths, 'SentryClips')
        print('Sentry done')            
        cam_paths = get_newcam_list(SAVEDCAM_PATH, '/home/pi/TeslaCam/SavedClips_Checkpoint')
        upload_for_sftp(SAVEDCAM_PATH, cam_paths, 'SavedClips')
        print('Saved done')            
        #subprocess.call(['umount', '/mnt/cam'])
