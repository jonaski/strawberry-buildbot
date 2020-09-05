FROM opensuse/tumbleweed

RUN zypper -n ar -c -f -n 'repo-tools' https://download.opensuse.org/repositories/devel:/tools/openSUSE_Tumbleweed/ repo-tools
RUN zypper -n ar -c -f -n 'repo-mingw' https://download.opensuse.org/repositories/windows:/mingw:/win32/openSUSE_Tumbleweed/ repo-mingw

RUN zypper --non-interactive --gpg-auto-import-keys ref
RUN zypper --non-interactive --gpg-auto-import-keys dup -l -y

RUN zypper --non-interactive --gpg-auto-import-keys install \
    glibc glibc-extra glibc-locale glibc-i18ndata glibc-32bit gcc-c++ \
    which patch gperf wget curl git ruby diffutils \
    make cmake libtool pkg-config autoconf automake meson ninja intltool makeinfo scons bison flex gettext-tools \
    tar gzip bzip2 xz p7zip p7zip-full lzip zip unzip \
    linux-glibc-devel glibc-devel file-devel libopenssl-devel gdk-pixbuf-devel gtk-doc \
    mingw32-cross-nsis \
    python-base python-devel python3-base python3-devel python3-pip python-xml

RUN pip3 install --upgrade pip
RUN pip3 install buildbot_worker==2.8.4

RUN echo "mingw" > /worker-name
RUN useradd -r -m -s /bin/false buildbot

CMD ["/usr/bin/python3", "/config/worker/start.py"]
