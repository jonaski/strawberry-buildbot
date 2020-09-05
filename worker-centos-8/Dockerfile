FROM centos:8

RUN dnf install -y epel-release
RUN dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
RUN dnf install -y 'dnf-command(config-manager)'
RUN dnf config-manager --set-enabled PowerTools

RUN dnf clean all
RUN dnf update -y
RUN dnf install -y \
                   glibc gcc-c++ make automake libtool cmake3 patchelf ccache rpmdevtools \
                   redhat-lsb-core git fuse fuse-libs wget curl man tar gettext \
                   boost-devel fuse-devel dbus-devel libnotify-devel gnutls-devel sqlite-devel \
                   protobuf-devel protobuf-compiler \
                   alsa-lib-devel pulseaudio-libs-devel \
                   qt5-devel qt5-qtbase-devel qt5-qtx11extras-devel qt5-qttools-devel \
                   fftw-devel libchromaprint-devel \
                   libcdio-devel libgpod-devel libplist-devel libusbmuxd-devel libmtp-devel \
                   libjpeg-devel cairo-devel \
                   dbus-x11 xorg-x11-server-Xvfb xorg-x11-xauth vim-common \
                   desktop-file-utils libappstream-glib appstream-data hicolor-icon-theme \
                   python3-pip python3-devel

RUN dnf install -y gstreamer1-devel gstreamer1-plugins-base-devel \
                   gstreamer1 gstreamer1-plugins-base gstreamer1-plugins-good \
                   gstreamer1-plugins-bad-free gstreamer1-plugins-ugly-free


RUN dnf clean all && dnf update -y

RUN pip3 install --upgrade pip
RUN pip3 install buildbot_worker==2.8.4

RUN echo "centos-8" > /worker-name
RUN useradd -r -m -s /bin/false buildbot

RUN mkdir -p /home/buildbot/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS} && \
    chown buildbot /home/buildbot/rpmbuild/{,BUILD,RPMS,SOURCES,SPECS,SRPMS}

CMD ["/usr/bin/python3", "/config/worker/start.py"]
