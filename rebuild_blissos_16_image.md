- mount .iso and extract it's content
```sh
cd /srv
mkdir /mnt/iso
mount -o loop /var/lib/vz/template/iso/Bliss-v16.9.6-x86_64-OFFICIAL-gapps-20240602.iso /mnt/iso  # mount original .iso as new partition in /mnt/iso
mkdir /srv/iso
cp -a /mnt/iso/* /srv/iso/  # copy all files from /mnt/iso and save their chown/chmod
umount /mnt/iso  # unmout original .iso because we don't need it any more
rm -r /mnt/iso
```

- mount .efs file that containes .img file inside it. Extract it's content
```sh
mkdir -p /mnt/efs
mount -t erofs -o loop /srv/iso/system.efs /mnt/efs
mkdir /srv/efs
cp -a /mnt/efs/* /srv/efs/
umount /mnt/efs
rm -r /mnt/efs
```

- mount .img that contains all android os files. Extract it's content
```sh
mkdir /mnt/img
mount -t ext4 -o loop /srv/efs/system.img /mnt/img
mkdir /srv/img
cp -a /mnt/img/* /srv/img/
umount /mnt/img
```

- rebuild new .img
```sh
dd if=/dev/zero of=/srv/system.img bs=4096 count=1280000
mkfs.ext4 -F -O "ext_attr,dir_index,filetype,extent,sparse_super,large_file,huge_file,uninit_bg,dir_nlink,extra_isize" system.img
mount -o loop system.img /mnt/img
cp -a /srv/img/* /mnt/img/
cp /root/rebuild_bliss_instructions/c8750f0d.0 /mnt/img/system/etc/security/cacerts/  # copy the mitmproxy CA cert into system cacerts folder
chcon --reference=/mnt/img/system/etc/security/cacerts/c491639e.0 /mnt/img/system/etc/security/cacerts/c8750f0d.0  # copy SElinux rules from c491639e.0 to our new CA cert file 
umount /mnt/img
rm -r /mnt/img
```

- rebuild new .efs
```sh
mv /srv/system.img /srv/efs/
chown nobody:nogroup /srv/efs/system.img
chmod 644 /srv/efs/system.img
apt-get install erofs-utils -y
mkfs.erofs -zlz4 /srv/system.efs /srv/efs
```

- **optional** step: make sure that we set "VIRT_WIFI=1" (to enable wifi) by default
```sh
cfg=/srv/iso/efi/boot/android.cfg
tmp="${cfg}.tmp"

awk '
  /^[[:space:]]*submenu "VM Options -> " --class forward[[:space:]]*\{/ {in_vm=1}
  in_vm && /^[[:space:]]*add_entry[[:space:]]/ && $0 !~ /(^|[[:space:]])VIRT_WIFI=1([[:space:]]|$)/ {$0=$0" VIRT_WIFI=1"}
  in_vm && /^[[:space:]]*\}/ {in_vm=0}
  {print}
' "$cfg" > "$tmp" &&
chown --reference="$cfg" "$tmp" &&
chmod --reference="$cfg" "$tmp" &&
mv "$tmp" "$cfg"
```

- build new .iso image
```sh
mv /srv/system.efs /srv/iso/
chown nobody:nogroup /srv/iso/system.efs
chmod 644 /srv/iso/system.efs
apt-get install xorriso -y  # install xorriso to create new (modified) .iso image
xorriso -as mkisofs -R -f -e /srv/iso/boot/grub/efi.img -no-emul-boot -o /srv/new_bliss.iso -J -joliet-long -cache-inodes /srv/iso  # with app xorriso create new .iso image
mv new_bliss.iso /var/lib/vz/template/iso/
```

- delete all traces of your work
```sh
rm -r /srv/iso
rm -r /srv/efs
rm -r /srv/img
```