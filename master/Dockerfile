FROM opensuse/leap:15.2

RUN zypper --non-interactive --gpg-auto-import-keys ref
RUN zypper --non-interactive --gpg-auto-import-keys up -l -y
RUN zypper --non-interactive --gpg-auto-import-keys install git gcc python3-pip python3-devel libcairo2 cairo-tools python3-cairo

RUN pip3 install --upgrade pip
RUN pip3 install pycairo requests buildbot==3.2.0 buildbot-www==3.2.0 buildbot-waterfall-view==3.2.0 buildbot-console-view==3.2.0 buildbot-grid-view==3.2.0 buildbot-badges sqlalchemy==1.3.23

RUN useradd -r -s /bin/false buildbot

EXPOSE 9989
ENV PYTHONPATH /config/master
ENTRYPOINT ["/usr/bin/python3", "/config/master/start.py"]
CMD []
