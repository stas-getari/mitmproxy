- to start mitmproxy: `mitmdump --mode transparent --showhost`
- save logs as .json: `mitmdump --mode transparent --showhost --scripts src/logs_to_json.py`
- save logs to mongodb: `mitmdump --mode transparent --showhost --scripts src/logs_to_mongodb.py`
- save logs as proprietary mitm format: `mitmdump --mode transparent --showhost --save-stream-file logs.mitm`
- read logs from .mitm file: `mitmproxy --showhost --rfile logs.mitm`
- to see what service listen on port 8080: `ss -lntup | grep 8080`
- example of command if you start it from `mitmproxyuser`: `sudo -u mitmproxyuser -H bash -c 'cd /srv/mitmproxy && mitmdump --mode transparent --showhost --scripts src/logs_to_mongodb.py'`

--------------

1. Enable forwarding
```
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv6.conf.all.forwarding=1
sysctl -w net.ipv4.conf.all.send_redirects=0
```

2. Create mitmproxy user
```
sudo useradd --create-home mitmproxyuser
sudo -u mitmproxyuser -H bash -c 'cd ~ && pip install --user mitmproxy motor pyyaml'
```

3. Add NAT to forward http/https to mitmproxy:
```
iptables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner mitmproxyuser --dport 80 -j REDIRECT --to-port 8080
iptables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner mitmproxyuser --dport 443 -j REDIRECT --to-port 8080
ip6tables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner mitmproxyuser --dport 80 -j REDIRECT --to-port 8080
ip6tables -t nat -A OUTPUT -p tcp -m owner ! --uid-owner mitmproxyuser --dport 443 -j REDIRECT --to-port 8080
```
- download packet that save iptables `sudo apt-get install iptables-persistent`
- save everything `netfilter-persistent save`

4. Set mitmproxy as system boot service
- create file `/etc/systemd/system/mitmdump.service` with content:
```
[Unit]
Description=mitmproxy service
After=network.target

[Service]
Type=simple
User=mitmproxyuser
WorkingDirectory=/srv/mitmproxy
ExecStart=mitmdump --mode transparent --showhost --scripts src/logs_to_mongodb.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```
- then run commands
```
- `sudo systemctl daemon-reload`
- `sudo systemctl enable mitmdump.service`
- `sudo systemctl start mitmdump.service`
- `sudo systemctl status mitmdump.service`
```

5. Copy content of **./certificate** folder into **/home/mitmproxyuser/.mitmproxy/**

6. Add CA cert from http://mitm.it to both browser and as trusted CA over whole system

7. If you need to add more options to how you run the mitmproxy, you can use **/home/mitmproxyuser/.mitmproxy/config.yaml** file
