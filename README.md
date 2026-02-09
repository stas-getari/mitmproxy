## `root` config
```sh
# update everything
apt update && apt upgrade -y

# install xfce4 and xrd
apt install xfce4 xfce4-goodies xrdp -y

# install some other packages usefull for development
apt install curl wget htop make -y

# make sure that system will choose xfce4 when it will render the display
# make sure that `/usr/bin/startxfce4` selected
update-alternatives --config x-session-manager

# start and enable xrdp
systemctl enable xrdp
systemctl start xrdp

# install google chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
apt update
apt install google-chrome-stable -y

# install docker
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
apt-get update
apt-get install ca-certificates -y
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# create mitmproxy and dating-engine folders in /srv
# and assign them to `user`
mkdir /srv/mitmproxy
mkdir /srv/dating-engine
chown 1000:1000 -R /srv/mitmproxy
chown 1000:1000 -R /srv/dating-engine

# make sure you enabled sysctl networking for mitmproxy
sed -i 's/^#*net\.ipv4\.ip_forward.*/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sed -i 's/^#*net\.ipv6\.conf\.all\.forwarding.*/net.ipv6.conf.all.forwarding=1/' /etc/sysctl.conf
sed -i 's/^#*net\.ipv4\.conf\.all\.send_redirects.*/net.ipv4.conf.all.send_redirects = 0/' /etc/sysctl.conf

# install adb and other android dependencies
apt-get install -y \
    android-tools-adb \
    android-sdk-build-tools
```

## configure iptables
```sh
# Create the script file
tee /usr/local/bin/setup-proxy-iptables.sh > /dev/null << 'EOF'
#!/bin/bash
LAN_INTERFACE=eth0
PROXY_IP=$(hostname -I | awk '{print $1}')
iptables -t nat -N PROXY
iptables -t nat -A PREROUTING -i $LAN_INTERFACE -p tcp --dport 443 -j PROXY
iptables -t nat -A PROXY -p tcp -j DNAT --to-destination $PROXY_IP:8080
EOF

# Make it executable
chmod +x /usr/local/bin/setup-proxy-iptables.sh

# Create the systemd service
tee /etc/systemd/system/proxy-iptables.service > /dev/null << 'EOF'
[Unit]
Description=Setup Proxy IPTables Rules
After=docker.service
Wants=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/setup-proxy-iptables.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl daemon-reload
systemctl enable proxy-iptables.service
systemctl start proxy-iptables.service
```

## `user` config
```sh
# create new user by name `user` and also activate xrdp for him
# make sure you provide password for him
useradd user -m
passwd user
su user

# switch to bash
chsh -s /bin/bash
bash

# add github cert
cd ~/
mkdir .ssh
cat >> ~/.ssh/config << 'EOF'
Host dating-engine-repo
  HostName github.com
  PreferredAuthentications publickey
  IdentityFile ~/.ssh/dating-engine-repo

Host mitmproxy-repo
  HostName github.com
  PreferredAuthentications publickey
  IdentityFile ~/.ssh/mitmproxy-repo
EOF

# now you need to get access to private ssh keys `dating-engine-repo` and `mitmproxy-repo` and save them into folder ~/.ssh/
# and assign proper permissions
chmod 0600 ~/.ssh/dating-engine-repo
chmod 0600 ~/.ssh/mitmproxy-repo

# download both repos
cd /srv/mitmproxy
git init
git remote add origin git@mitmproxy-repo:stas-getari/mitmproxy.git
git fetch --all
git checkout master
git config --global --add safe.directory /srv/mitmproxy
cd /srv/dating-engine
git init
git remote add origin git@dating-engine-repo:stas-getari/dating-engine.git
git fetch --all
git checkout main
git config --global --add safe.directory /srv/dating-engine

# make sure that you create .env files in both repositories and filled those files
cd /srv/mitmproxy && cp .env.example .env
cd /srv/dating-engine && cp .env.example .env

# add those env vars for `user`. So appium server will work well
ENV_VARS="
# Custom env vars added to that LXC
export ANDROID_HOME=/usr/bin
export ANDROID_SDK_ROOT=/usr/bin
source '$HOME/.nvm/nvm.sh'"
echo "$ENV_VARS" | tee -a ~/.bashrc ~/.xsessionrc > /dev/null

# download nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# install node 22. Before that you need to re-login into the `user`
nvm install 22

# install npm packages
cd /srv/dating-engine/engine-worker-api/
npm install

# after you opened xfce4 for the first time, make some adjustments to increase rendering speed
1. Settings → Desktop → Background Tab → Style: None
2. Applications Menu → Settings → Window Manager Tweaks → Compositor Tab → Uncheck “Enable display compositing”
3. Settings → Default Applications → configure default app for 'terminal' and 'web browser'
4. Settings → Settings Manager → Session and Startup → Application Autostart → disable everything not required for work
5. Settings → Screensaver → Disable everything in both Screensaver and Lock Screen

# on desktop create launcher file with command bellow
# working directory as `/srv/dating-engine/engine-worker-api/`
# make sure you configured it as 'Run in Terminal'
bash -c '. ~/.nvm/nvm.sh && nvm use default >/dev/null 2>&1 && npm run dev:worker'

# as root user!!! copy mitmproxy cert to system directory. We need that in case if we want to intercept also traffic originated from the LXC
su root
cp /srv/mitmproxy/certificate/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy.crt
update-ca-certificates  # update the system certificates

# as I see there is some issue with locale when you open shell: "can’t set the locale; make sure $LC_* and $LANG are correct"
# if you see that, then run command:
locale-gen "en_US.UTF-8"
```

## `frida` config
```bash
# Frida can be installed only via pip
sudo apt-get install -y python3-pip
python3 -m pip install -U frida-tools
```