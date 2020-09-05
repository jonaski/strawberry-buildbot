FROM debian:bullseye

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y \
                    git make cmake gcc fakeroot gettext lsb-release dput \
                    libboost-dev libglib2.0-dev dpkg-dev libdbus-1-dev libprotobuf-dev protobuf-compiler libsqlite3-dev libgnutls28-dev \
                    libasound2-dev libpulse-dev \
                    qtbase5-dev qtbase5-dev-tools qttools5-dev libqt5x11extras5-dev \
                    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-alsa gstreamer1.0-pulseaudio \
                    libchromaprint-dev libfftw3-dev \
                    libcdio-dev libmtp-dev libgpod-dev libimobiledevice-dev libplist-dev libusbmuxd-dev \
                    python3-pip python3-dev

RUN pip3 install --upgrade pip
RUN pip3 install buildbot_worker==2.8.4

RUN echo "debian-bullseye" > /worker-name
RUN useradd -r -m -s /bin/false buildbot

CMD ["/usr/bin/python3", "/config/worker/start.py"]
