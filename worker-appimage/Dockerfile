FROM centos:8

RUN dnf install -y epel-release
RUN dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
RUN dnf install -y 'dnf-command(config-manager)'
RUN dnf config-manager --set-enabled PowerTools

RUN dnf clean all
RUN dnf update -y
RUN dnf install -y \
                   glibc gcc gcc-c++ make meson automake libtool cmake3 patchelf ccache rpmdevtools \
                   redhat-lsb-core git fuse fuse-libs wget curl man tar gettext bzip2 nasm yasm perl bison flex \
                   boost-devel fuse-devel dbus-devel libnotify-devel gnutls-devel sqlite-devel openssl-devel glib2-devel \
                   libogg-devel opus-devel libvorbis-devel flac-devel lame-devel libsoup-devel speex-devel wavpack-devel \
                   protobuf-devel protobuf-compiler \
                   alsa-lib-devel pulseaudio-libs-devel libglvnd-devel \
                   qt5-devel qt5-qtbase-devel qt5-qtx11extras-devel qt5-qttools-devel \
                   fftw-devel libchromaprint-devel \
                   libcdio-devel libgpod-devel libplist-devel libusbmuxd-devel libmtp-devel \
                   libjpeg-devel cairo-devel \
                   dbus-x11 xorg-x11-server-Xvfb xorg-x11-xauth vim-common \
                   desktop-file-utils libappstream-glib appstream-data hicolor-icon-theme \
                   python3-pip python3-devel



RUN dnf clean all && dnf update -y

RUN pip3 install --upgrade pip
RUN pip3 install buildbot_worker==2.8.4

RUN echo "appimage" > /worker-name
RUN useradd -r -m -s /bin/false buildbot

RUN mkdir -p /home/buildbot/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
RUN chown buildbot /home/buildbot/rpmbuild/{,BUILD,RPMS,SOURCES,SPECS,SRPMS}

RUN export PKG_CONFIG_PATH=/usr/lib64/pkgconfig

RUN cd /tmp && wget https://gstreamer.freedesktop.org/src/gstreamer/gstreamer-1.16.2.tar.xz
RUN cd /tmp && tar -xvf gstreamer-1.16.2.tar.xz
RUN cd /tmp/gstreamer-1.16.2 && ./configure --prefix=/usr --libdir=/usr/lib64 --disable-examples --disable-tests --disable-benchmarks --disable-tools
RUN cd /tmp/gstreamer-1.16.2 && make install

RUN cd /tmp && wget https://gstreamer.freedesktop.org/src/gst-plugins-base/gst-plugins-base-1.16.2.tar.xz
RUN cd /tmp && tar -xvf gst-plugins-base-1.16.2.tar.xz
RUN cd /tmp/gst-plugins-base-1.16.2 && ./configure --prefix=/usr --libdir=/usr/lib64 --disable-examples --disable-videoconvert --disable-videorate --disable-videoscale --disable-videotestsrc --disable-overlaycomposition --disable-compositor
RUN cd /tmp/gst-plugins-base-1.16.2 && make install

RUN cd /tmp && wget https://gstreamer.freedesktop.org/src/gst-plugins-good/gst-plugins-good-1.16.2.tar.xz
RUN cd /tmp && tar -xvf gst-plugins-good-1.16.2.tar.xz
RUN cd /tmp/gst-plugins-good-1.16.2 && ./configure --prefix=/usr --libdir=/usr/lib64 --disable-examples --disable-alpha --disable-avi --disable-cutter --disable-debugutils --disable-deinterlace --disable-dtmf --disable-effectv --disable-flv --disable-flx --disable-goom --disable-goom2k1 --disable-imagefreeze --disable-interleave --disable-law --disable-matroska --disable-multifile --disable-multipart --disable-shapewipe --disable-smpte --disable-videobox --disable-videocrop --disable-videofilter --disable-videomixer --disable-y4m
RUN cd /tmp/gst-plugins-good-1.16.2 && make install

RUN cd /tmp && wget https://files.jkvinge.net/packages/strawberry-dependencies/faad2-2.8.8.tar.gz
RUN cd /tmp && tar -xvf faad2-2.8.8.tar.gz
RUN cd /tmp && cd faad2-2.8.8 && ./configure --prefix=/usr
RUN cd /tmp && cd faad2-2.8.8 && make install

#RUN cd /tmp && wget http://downloads.sourceforge.net/faac/faac-1.28.tar.bz2
#RUN cd /tmp && tar -xvf faac-1.28.tar.bz2
#RUN cd /tmp && cd faac-1.28 && ./configure
#RUN cd /tmp && cd faac-1.28 && make install

RUN cd /tmp && wget https://gstreamer.freedesktop.org/src/gst-plugins-bad/gst-plugins-bad-1.16.2.tar.xz
RUN cd /tmp && tar -xvf gst-plugins-bad-1.16.2.tar.xz
RUN cd /tmp/gst-plugins-bad-1.16.2 && ./configure --prefix=/usr --libdir=/usr/lib64 --disable-examples --disable-accurip --disable-adpcmdec --disable-adpcmenc --disable-aiff --disable-asfmux --disable-audiobuffersplit --disable-audiofxbad --disable-audiolatency --disable-audiomixmatrix --disable-audiovisualizers --disable-autoconvert --disable-bayer --disable-camerabin2 --disable-coloreffects --disable-debugutils --disable-dvbsuboverlay --disable-dvdspu --disable-faceoverlay --disable-festival --disable-fieldanalysis --disable-freeverb --disable-frei0r --disable-gaudieffects --disable-gdp --disable-geometrictransform --disable-id3tag --disable-inter --disable-interlace --disable-ivfparse --disable-ivtc --disable-jp2kdecimator --disable-jpegformat --disable-librfb --disable-midi --disable-mpegdemux --disable-mpegpsmux --disable-mpegtsdemux --disable-mpegtsmux --disable-mxf --disable-netsim --disable-onvif --disable-pcapparse --disable-pnm --disable-proxy --disable-rawparse --disable-removesilence --disable-sdp --disable-segmentclip --disable-siren --disable-smooth --disable-speed --disable-subenc --disable-timecode --disable-videofilters --disable-videoframe_audiolevel --disable-videoparsers --disable-videosignal --disable-vmnc --disable-y4m --disable-yadif --disable-decklink --disable-dtls --disable-dvb --disable-hls --disable-ipcpipeline --disable-shm --disable-smoothstreaming
RUN cd /tmp/gst-plugins-bad-1.16.2 && make install


RUN cd /tmp && wget https://gstreamer.freedesktop.org/src/gst-plugins-ugly/gst-plugins-ugly-1.16.2.tar.xz
RUN cd /tmp && tar -xvf gst-plugins-ugly-1.16.2.tar.xz
RUN cd /tmp/gst-plugins-ugly-1.16.2 && ./configure --prefix=/usr --libdir=/usr/lib64 --disable-examples
RUN cd /tmp/gst-plugins-ugly-1.16.2 && make install


RUN cd /tmp && wget https://gstreamer.freedesktop.org/src/gst-libav/gst-libav-1.16.2.tar.xz
RUN cd /tmp && tar -xvf gst-libav-1.16.2.tar.xz
RUN cd /tmp/gst-libav-1.16.2 && ./configure --prefix=/usr --libdir=/usr/lib64
RUN cd /tmp/gst-libav-1.16.2 && make install


CMD ["/usr/bin/python3", "/config/worker/start.py"]
