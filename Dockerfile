FROM mitmproxy/mitmproxy:12.1.1

# # install pia-vpn
# RUN apt-get update && apt-get install -y jq wireguard-tools curl iproute2 procps iptables

# install requirements
RUN mkdir /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --upgrade pip  && pip install -r /code/requirements.txt

# copy files
COPY . /code
WORKDIR /code/src

# without that env path python can't import our modules
ENV PYTHONPATH "${PYTHONPATH}:/code/src"
