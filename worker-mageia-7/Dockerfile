FROM mageia:7

#RUN urpmi.addmedia --distrib http://www.mirrorservice.org/sites/mageia.org/pub/mageia/distrib/7/x86_64
RUN urpmi.update --auto -a
RUN urpmi --auto --auto-update
RUN urpmi --auto --force urpmi-debuginfo-install \
                  git \
                  glibc \
                  gcc-c++ \
                  binutils \
                  make \
                  cmake \
                  man \
                  tar \
                  rpmdevtools \
                  gettext \
                  lib64boost-devel \
                  lib64protobuf-devel \
                  lib64sqlite3-devel \
                  lib64alsa2-devel \
                  lib64pulseaudio-devel \
                  lib64notify-devel \
                  lib64qt5core-devel \
                  lib64qt5gui-devel \
                  lib64qt5widgets-devel \
                  lib64qt5network-devel \
                  lib64qt5concurrent-devel \
                  lib64qt5sql-devel \
                  lib64qt5dbus-devel \
                  lib64qt5x11extras-devel \
                  lib64qt5help-devel \
                  libqt5test-devel \
                  lib64gstreamer1.0-devel \
                  lib64gstreamer-plugins-base1.0-devel \
                  lib64cdio-devel \
                  lib64gpod-devel \
                  lib64plist-devel \
                  lib64usbmuxd-devel \
                  lib64mtp-devel \
                  lib64raw1394-devel \
                  lib64taglib-devel \
                  lib64chromaprint-devel \
                  libgnutls-devel \
                  libfftw-devel \
                  lib64mesaegl1 \
                  notification-daemon \
                  protobuf-compiler \
                  dbus-devel \
                  python3 \
                  libpython3-devel \
                  python3-pip \
                  desktop-file-utils \
                  appstream-util \
                  libappstream-glib8 \
                  hicolor-icon-theme \
                  qt5ct

RUN pip3 install --upgrade pip
RUN pip3 install buildbot_worker==2.8.4

RUN echo "mageia-7" > /worker-name
RUN useradd -r -m -s /bin/false buildbot

RUN mkdir -p /home/buildbot/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS} && \
    chown buildbot /home/buildbot/rpmbuild/{,BUILD,RPMS,SOURCES,SPECS,SRPMS}


CMD ["/usr/bin/python3", "/config/worker/start.py"]
