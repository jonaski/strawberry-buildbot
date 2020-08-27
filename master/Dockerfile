FROM ubuntu:groovy

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y pkg-config python3-pip python3-dev python3-cairo-dev

RUN pip3 install --upgrade pip
RUN pip3 install pycairo requests buildbot==2.8.3 buildbot-www==2.8.3 buildbot-waterfall-view==2.8.3 buildbot-console-view==2.8.3 buildbot-grid-view==2.8.3 buildbot-badges sqlalchemy

RUN ln -s /usr/local/bin/buildbot /usr/bin/buildbot

RUN useradd -r -s /bin/false buildbot

EXPOSE 9989
ENV PYTHONPATH /config/master
ENTRYPOINT ["/usr/bin/python3", "/config/master/start.py"]
CMD []
