FROM opensuse/tumbleweed

RUN zypper -n ar -c -f -n 'repo-packman' https://ftp.gwdg.de/pub/linux/misc/packman/suse/openSUSE_Tumbleweed/ repo-packman
RUN zypper -n ar -c -f -n 'repo-qt6' https://download.opensuse.org/repositories/home:/jonaski:/qt6/openSUSE_Tumbleweed/ repo-qt6

RUN zypper --non-interactive --gpg-auto-import-keys ref
RUN zypper --non-interactive --gpg-auto-import-keys dup -l -y

RUN zypper --non-interactive --gpg-auto-import-keys install \
    git make cmake gcc gcc-c++ tar gettext-tools wget \
    lsb-release rpm-build squashfs patchelf desktop-file-utils \
    glibc-devel glib2-devel glib2-tools dbus-1-devel libgnutls-devel alsa-devel libpulse-devel libnotify-devel \
    boost-devel libboost_headers-devel protobuf-devel sqlite3-devel fftw3-devel \
    qt6-core-devel qt6-gui-devel qt6-widgets-devel qt6-concurrent-devel qt6-network-devel \
    qt6-sql-devel qt6-dbus-devel qt6-test-devel qt6-x11extras-devel qt6-base-common-devel qt6-sql-sqlite \
    gstreamer-devel gstreamer-plugins-base-devel \
    libcdio-devel libgpod-devel libplist-devel libmtp-devel libusbmuxd-devel libchromaprint-devel \
    desktop-file-utils update-desktop-files appstream-glib AppStream hicolor-icon-theme \
    python3-base python3-devel python3-pip go \
    gstreamer gstreamer-plugins-base gstreamer-plugins-good \
    gstreamer-plugins-bad gstreamer-plugins-bad-orig-addon gstreamer-plugins-ugly gstreamer-plugins-ugly-orig-addon \
    gstreamer-plugins-libav \
    alsa alsa-plugins-oss alsa-plugins-upmix alsa-plugins-pulse alsa-plugins-jack

RUN pip3 install --upgrade pip
RUN pip3 install buildbot_worker==2.8.4

RUN echo "appimage-qt6" > /worker-name
RUN useradd -r -m -s /bin/false buildbot

RUN mkdir -p /home/buildbot/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS} && \
    chown buildbot /home/buildbot/rpmbuild/{,BUILD,RPMS,SOURCES,SPECS,SRPMS}

RUN rm -rf /tmp/go-appimage
RUN cd /tmp && git clone https://github.com/jonaski/go-appimage
RUN cd /tmp/go-appimage && git checkout strawberry
RUN cd /tmp/go-appimage/src/appimagetool && go build -trimpath -ldflags="-s -w"
RUN cp /tmp/go-appimage/src/appimagetool/appimagetool /usr/local/bin/
RUN rm -f /usr/local/bin/runtime-x86_64 && wget -P /usr/local/bin https://github.com/AppImage/AppImageKit/releases/download/continuous/runtime-x86_64

CMD ["/usr/bin/python3", "/config/worker/start.py"]
