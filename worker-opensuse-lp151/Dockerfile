FROM opensuse/leap:15.1

RUN zypper --non-interactive --gpg-auto-import-keys ref
RUN zypper --non-interactive --gpg-auto-import-keys up -l -y

RUN zypper --non-interactive --gpg-auto-import-keys install \
    lsb-release rpm-build rpmdevtools \
    git make cmake gcc gcc-c++ tar gettext-tools \
    glibc-devel glib2-devel glib2-tools dbus-1-devel alsa-devel libpulse-devel libnotify-devel libgnutls-devel \
    boost-devel protobuf-devel sqlite3-devel \
    libQt5Core-devel libQt5Gui-devel libQt5Widgets-devel libQt5Concurrent-devel libQt5Network-devel libQt5Sql-devel libQt5DBus-devel libQt5Test-devel \
    libqt5-qtx11extras-devel libqt5-qtbase-common-devel libQt5Sql5-sqlite libqt5-linguist-devel \
    gstreamer-devel gstreamer-plugins-base-devel vlc-devel \
    libcdio-devel libgpod-devel libplist-devel libmtp-devel libusbmuxd-devel libchromaprint-devel \
    desktop-file-utils update-desktop-files appstream-glib hicolor-icon-theme \
    python3-base python3-devel python3-pip

RUN pip3 install --upgrade pip
RUN pip3 install buildbot_worker==2.8.4

RUN echo "opensuse-lp151" > /worker-name
RUN useradd -r -m -s /bin/false buildbot

RUN mkdir -p /home/buildbot/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS} && \
    chown buildbot /home/buildbot/rpmbuild/{,BUILD,RPMS,SOURCES,SPECS,SRPMS}
CMD ["/usr/bin/python3", "/config/worker/start.py"]
