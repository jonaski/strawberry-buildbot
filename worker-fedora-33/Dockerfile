FROM fedora:33

RUN yum update --assumeyes
RUN yum upgrade --assumeyes
RUN dnf install --assumeyes \
    redhat-lsb-core \
    glibc gcc-c++ git tar rpmdevtools make cmake glib man gettext \
    boost-devel dbus-devel protobuf-devel protobuf-compiler sqlite-devel alsa-lib-devel pulseaudio-libs-devel libnotify-devel gnutls-devel \
    qt5-qtbase-devel qt5-qtx11extras-devel qt5-qttools-devel \
    gstreamer1-devel gstreamer1-plugins-base-devel \
    libcdio-devel libgpod-devel libplist-devel libusbmuxd-devel libmtp-devel \
    taglib-devel libchromaprint-devel fftw-devel \
    dbus-x11 xorg-x11-server-Xvfb xorg-x11-xauth \
    desktop-file-utils libappstream-glib hicolor-icon-theme \
    python3 python3-devel python3-pip

RUN pip3 install --upgrade pip
RUN pip3 install buildbot_worker==2.8.4

RUN echo "fedora-33" > /worker-name
RUN useradd -r -m -s /bin/false buildbot

RUN mkdir -p /home/buildbot/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS} && \
    chown buildbot /home/buildbot/rpmbuild/{,BUILD,RPMS,SOURCES,SPECS,SRPMS}

CMD ["/usr/bin/python3", "/config/worker/start.py"]
