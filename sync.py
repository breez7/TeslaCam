import time
import os
import sys
from datetime import datetime
import subprocess
import paramiko
import smbclient

MOUNT_POINT = '/mnt/cam'

# WAIT_TIME = 180
# TARGET_SENTRYCLIPS_PATH = '/182.222.81.199/pi/TeslaCam/SentryClips'
# TARGET_SAVEDCLIPS_PATH = '/182.222.81.199/pi/TeslaCam/SavedCLips'
# SENTRYCLIPS_CHECKPOINT = '/home/pi/TeslaCam/SentryClips_Checkpoint'
# SAVEDCLIPS_CHECKPOINT  = '/home/pi/TeslaCam/SavedClips_Checkpoint'
# SENTRYCLIPS_PATH = '/mnt/cam/TeslaCam/SentryClips'
# SAVEDCLIPS_PATH = '/mnt/cam/TeslaCam/SavedClips'
WAIT_TIME = 1
TARGET_SENTRYCLIPS_PATH = '/182.222.81.199/pi/TeslaCam2/SentryClips'
TARGET_SAVEDCLIPS_PATH = '/182.222.81.199/pi/TeslaCam2/SavedCLips'
SENTRYCLIPS_CHECKPOINT = '/home/james/project/tesla/SentryClips_Checkpoint'
SAVEDCLIPS_CHECKPOINT  = '/home/james/project/tesla/SavedClips_Checkpoint'
SENTRYCLIPS_PATH = '/home/james/project/tesla/SentryClips'
SAVEDCLIPS_PATH = '/home/james/project/tesla/SavedClips'

UPLOAD_METHOD = 'smb' # sftp or smb

host = '182.222.81.199'
username = 'pi'
password = 'xxx'
smb_port = 2445
ssh_port = '2222'
ssh = ''
if UPLOAD_METHOD == 'smb':
    smbclient.register_session(host, username=username, password=password, port=smb_port)
else:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

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

def upload_for_smb(root, paths, target_path, checkpoint):
    if len(paths) == 0:
        return

    for path in paths:
        print('send path : ' + path)
        try:
            smbclient.mkdir(target_path + '/' + path,username=username, password=password, port=smb_port)
        except:
            pass
        
        send_files = get_event_files(root, path)
        for send_file in send_files:
            try:
                smbclient.stat(target_path + '/' + path + '/' + send_file.split('/')[-1],username=username, password=password, port=smb_port)
            except:
                print('sending ' + send_file)
                dest = smbclient.open_file(target_path+'/'+path+'/'+send_file.split('/')[-1], 'wb',username=username, password=password, port=smb_port)
                src = open(send_file, 'rb')
                while True:
                    temp = src.read(1024 * 4)
                    if len(temp) == 0:
                        break
                    dest.write(temp)
                src.close()
                dest.close()

    make_checkpoint(paths, checkpoint)

def upload_for_sftp(root, paths, target_path, checkpoint):
    if len(paths) == 0:
        return
    ssh.connect(host, username=username, port=ssh_port, password=password)
    sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())

    root_prefix = '/media/hdd/TeslaCam/'
    for path in paths:
        print('send path : ' + path)
        try:
            sftp.stat(root_prefix + target_path + '/' + path)
        except:
            sftp.mkdir(root_prefix + target_path + '/' + path)
        
        send_files = get_event_files(root, path)
        for send_file in send_files:
            try:
                sftp.stat(root_prefix + target_path + '/' + path + '/' + send_file.split('/')[-1])
            except:
                print('sending ' + send_file)
                sftp.put(send_file, root_prefix + target_path + '/' + path + '/' + send_file.split('/')[-1])

    sftp.close()
    ssh.close()
    make_checkpoint(paths, checkpoint)

def get_event_files(root, path):
    files = os.listdir(root + '/' + path)
    files.sort(reverse=True)
    if len(files) >= 10:
        files = files[:10]
    else:
        files = files[:len(files)]

    if not 'thumb.png' in files:
        files = files[:-1]
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
    
    print(newcam_list)
    return newcam_list

if '__main__' == __name__:
    #  while(True):
        subprocess.call(['mount', MOUNT_POINT])

        time.sleep(WAIT_TIME)

        cam_paths = get_newcam_list(SENTRYCLIPS_PATH, SENTRYCLIPS_CHECKPOINT)
        if UPLOAD_METHOD == 'smb':
            upload_for_smb(SENTRYCLIPS_PATH, cam_paths, TARGET_SENTRYCLIPS_PATH, SENTRYCLIPS_CHECKPOINT)
        else:
            upload_for_sftp(SENTRYCLIPS_PATH, cam_paths, 'SentryClips', SENTRYCLIPS_CHECKPOINT)
        print('Sentry done')            

        cam_paths = get_newcam_list(SAVEDCLIPS_PATH, SAVEDCLIPS_CHECKPOINT)
        if UPLOAD_METHOD == 'smb':
            upload_for_smb(SAVEDCLIPS_PATH, cam_paths, TARGET_SAVEDCLIPS_PATH, SAVEDCLIPS_CHECKPOINT)
        else:
            upload_for_sftp(SAVEDCLIPS_PATH, cam_paths, 'SavedClips', SAVEDCLIPS_CHECKPOINT)
        print('Saved done')            

        subprocess.call(['umount', '/mnt/cam'])
