#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time,os,daemon,logging,sys
import netifaces as ni
# TODO Optionnal support
from gi.repository import Notify


# INIT LOGGER
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh = logging.FileHandler(os.getenv('HOME')+"/.netautomount.log")
fh.setFormatter(formatter)
logger.addHandler(fh)
context = daemon.DaemonContext(
   files_preserve = [
      fh.stream,
   ],
)
class gnome_notifier:
    def __init__(self):
        Notify.init ("automount")

    def notify_mount(self,mount):
        logger.info('Mount done '+mount.mount_point)
        try:
            mount_notif=Notify.Notification.new ("Automount "+mount.server_ip,
                                           "Montage effectué : "+mount.mount_point,
                                           "dialog-information")
            mount_notif.show()
        except:
            logger.error('Mount Notify Error')
            pass
    def notify_umount(self,mount):
        logger.info('Umount done '+mount.mount_point)
        try:

            mount_notif=Notify.Notification.new ("Automount "+mount.server_ip,
                                           "Démontage effectué "+mount.mount_point,
                                           "dialog-information")
            mount_notif.show()
        except:
            logger.error('Umount Notify error')
            pass

class mount:
    def __init__(self,label,server_ip,server_dir,mount_point,notifier):
        self.label = label
        self.server_ip = server_ip
        self.server_dir = server_dir
        self.mount_point = mount_point
        self.notifier=notifier

    def can_join_server(self):
        response = os.system("ping -c 1 " + self.server_ip + " > /dev/null")
        return response == 0
    def mounted(self):
        return os.path.ismount(self.mount_point)

class sshfs(mount):
    def __init__(self,label,server_ip,server_dir,mount_point,notifier):
        mount.__init__(self,label,server_ip,server_dir,mount_point,notifier)
        self.command="sshfs"
        self.command_umount="sudo umount -f"

    def mount(self):
        # TODO test server mac address
        if self.can_join_server() and not self.mounted():
            mounted = os.system(self.command+" "+self.server_ip+":"+self.server_dir+" "+self.mount_point)
            if int(mounted) == 0:
                self.notifier.notify_mount(self)

    def umount(self):
        if not self.can_join_server() and self.mounted():
            unmounted = os.system(self.command_umount+" "+self.mount_point)
            if int(unmounted) == 0:
                self.notifier.notify_umount(self)

class interface:
    def __init__(self,label):
        self.label = label
        self.carrier_changes=0
        self.ip=""

    """
        Returns True if change
    """
    def check_status(self):
        with open('/sys/class/net/'+self.label+'/carrier_changes', 'rb') as iface_status:
            status = iface_status.read().rstrip('\r\n')
            if status != self.carrier_changes:
                # Changement détecté : mise a jour de l'ip
                logger.debug('>>> '+self.label+' status change')
                self.carrier_changes = status
                time.sleep(5)
                try:
                    self.ip = ni.ifaddresses(self.label)[2][0]['addr']
                except:
                    self.ip=""
                logger.debug(">>>> "+ self.label +" - ip= "+ self.ip)
                return True
        return False

    def has_ip(self):
        return self.ip != ""

class iface_monitor:
    def __init__(self,loop_interval):
        self.loop_interval = loop_interval
        self.interfaces = []
        self.mountpoints = []

    def add_iface(self,interface):
        self.interfaces.append(interface)

    def add_mount(self,mount):
        self.mountpoints.append(mount)

    def run(self):
        try:
            while True:
                for i in self.interfaces:
                    if i.check_status():
                        for m in self.mountpoints:
                            if i.has_ip():
                                m.mount()
                            else:
                                m.umount()
                time.sleep(self.loop_interval)
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    loop_delay = 10
    conf_dir=os.getenv('HOME')+"/.netautomount.d"
    ifaces_startpatterns=['eth','enp0s25','wlan','wlp4s']

    monitor = iface_monitor(loop_delay)

    # Load interfaces
    for iface in ni.interfaces():
        iface_active = False
        for s in ifaces_startpatterns:
            if iface.startswith(s):
                iface_active=True
        if iface_active:
            monitor.add_iface(interface(iface))

    # Load conf
    for (dirpath, dirnames, filenames) in os.walk(conf_dir):
        for f in filenames:
            conf=  {}
            with open(conf_dir+"/"+f) as myfile:
                for line in myfile:
                    name, var = line.partition("=")[::2]
                    conf[name.strip()] = str(var).rstrip()
                monitor.add_mount(sshfs(f, conf['server'],conf['server_dir'],
                conf['mount_point'],gnome_notifier()))


    # daemon mode
    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        logger.info('Starting NetAutomount daemon mode')
        context.open()
        monitor.run()

    else:
        logger.info('Starting NetAutomount inline mode')
        monitor.run()
