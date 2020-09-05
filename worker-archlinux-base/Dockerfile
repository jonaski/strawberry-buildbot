FROM archlinux/base

RUN pacman -Syu --noconfirm
RUN pacman -S --noconfirm \
                    git make cmake gcc fakeroot sudo pkgconf python-pip gettext \
                    desktop-file-utils hicolor-icon-theme \
                    udisks2 dbus sqlite3 alsa-lib pulseaudio boost protobuf gnutls \
                    qt5-base qt5-x11extras qt5-tools \
                    gst-plugins-base gst-plugins-good vlc phonon-qt5 \
                    taglib chromaprint \
                    libcdio libmtp libgpod libusbmuxd libplist libimobiledevice

RUN pacman -S --noconfirm fftw

RUN pip3 install --upgrade pip
RUN pip3 install buildbot_worker==2.8.4

RUN echo "archlinux-base" > /worker-name
RUN echo "PACKAGER=\"Jonas Kvinge <jonas@strawbs.net>\"" >>/etc/makepkg.conf
RUN useradd -r -m -s /bin/false buildbot

CMD ["/usr/bin/python3", "/config/worker/start.py"]
