FROM mitmproxy/mitmproxy:12.1.1

# install requirements
RUN mkdir /code
RUN pip install motor==3.7.1 pymongo==4.15.1

# copy files
COPY . /code
WORKDIR /code/src

# without that env path python can't import our modules
ENV PYTHONPATH "${PYTHONPATH}:/code/src"
