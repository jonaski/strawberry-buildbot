FROM ubuntu:bionic

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y \
                    git make cmake gcc fakeroot wget curl gettext lsb-release dput build-essential dh-make \
                    dpkg-dev libglib2.0-dev libdbus-1-dev \
                    libboost-dev libprotobuf-dev protobuf-compiler libsqlite3-dev libgnutls28-dev \
                    libasound2-dev libpulse-dev \
                    qtbase5-dev qtbase5-private-dev qtbase5-dev-tools qttools5-dev \
                    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-good1.0-dev \
                    libtag1-dev libchromaprint-dev libfftw3-dev \
                    libcdio-dev libmtp-dev libgpod-dev libimobiledevice-dev libplist-dev libusbmuxd-dev \
                    python3-pip python3-dev

RUN pip3 install --upgrade pip
RUN pip3 install buildbot_worker==3.2.0

RUN echo "ubuntu-bionic" > /worker-name
RUN useradd -r -m -s /bin/false buildbot

CMD ["/usr/bin/python3", "/config/worker/start.py"]
