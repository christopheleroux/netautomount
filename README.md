# Netautomount.py
**Automtic network resources mount script**

I wrote this script in order to automaticly mount my nas's filesystem with sshfs.

When nas is available (network has ip and resource is available), the script mounts resource. when resource becomes unavailable (no netwok connection), it is unmounted

## Configuration
configuration is read from mount config files present in $HOME/.netautomount.d/

mount config file format is :
```
server=<server ip>
server_dir=<server mounted dir>
mount_point=<local mount point>
```
## Logs
logfile is $HOME/.netautomount.log

## Notification
Depends gnome notifier. I should improve that point to support generic notifications or optionnal
