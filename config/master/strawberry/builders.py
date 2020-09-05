import os.path
import pprint
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from buildbot.changes import gitpoller
from buildbot.plugins import steps, util
from buildbot.process import factory
from buildbot.steps import master
from buildbot.steps import shell
from buildbot.steps import transfer
from buildbot.steps.source import git

UPLOADBASE = "/srv/www/htdocs/builds"
UPLOADURL = "https://builds.strawberrymusicplayer.org"
MAKE_JOBS = '4'

def GitBaseUrl(repository):
  return "https://github.com/strawberrymusicplayer/%s.git" % repository


def GitArgs(repository, branch):
  return {
    "repourl": GitBaseUrl(repository),
    "branch": branch,
    "mode": "incremental",
    "retry": (5 * 60, 3),
    "workdir": "source",
  }


def GitPoller(repository, branch):
  return gitpoller.GitPoller(
      project=repository.lower(),
      repourl=GitBaseUrl(repository),
      pollinterval=60 * 5,  # seconds
      branch=branch,
      workdir="gitpoller_%s_%s" % (repository.lower(), branch))

@util.renderer

def get_base_filename(props):

  output_filepath = props.getProperty('output-filepath')
  base_filename = os.path.basename(output_filepath)

  return {
    "output-filepath": output_filepath,
    "base-filename": base_filename,
  }

def get_git_revision(props):
    include_git_revision = props.getProperty('include_git_revision')
    return include_git_revision['include_git_revision']

def UploadPackage(directory):

  return transfer.FileUpload(
    #mode=0644,
    workdir="source",
    workersrc=util.Interpolate("%(prop:output-filepath)s"),
    masterdest=util.Interpolate(
      "%(kw:base)s/%(kw:directory)s/%(prop:base-filename)s",
      base=UPLOADBASE,
      directory=directory,
    ),
    url=util.Interpolate(
      "%(kw:base)s/%(kw:directory)s/%(prop:base-filename)s",
      base=UPLOADURL,
      directory=directory,
    ),
  )


def MakeSourceBuilder():

  git_args = GitArgs("strawberry", "master")
  git_args["mode"] = "full"
  git_args["method"] = "fresh"

  f = factory.BuildFactory()
  f.addStep(git.Git(**git_args))

  f.addStep(
    shell.ShellCommand(
      name="run cmake",
      workdir="source/build",
      command=["cmake", ".." ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run maketarball",
      workdir="source/dist/scripts",
      command=["./maketarball.sh"],
      haltOnFailure=True
    )
  )

  f.addStep(
    steps.SetPropertyFromCommand(
      name="get output filename",
      workdir="source",
      command=[
        "sh", "-c",
        "ls -dt " + "dist/scripts/strawberry-*.tar.xz" + " | head -n 1"
      ],
      property="output-filepath",
      haltOnFailure=True
    )
  )
  f.addStep(steps.SetProperties(properties=get_base_filename))
  f.addStep(UploadPackage("source"))

  f.addStep(
    shell.ShellCommand(
      name="delete file",
      workdir="source/dist/scripts",
      command="rm -f *.bz2 *.xz",
      haltOnFailure=True
    )
  )

  return f


def MakeRPMBuilder(distro, version):

  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("strawberry", "master")))

  f.addStep(
    shell.ShellCommand(
      name="run cmake",
      workdir="source/build",
      command=["cmake", ".."],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run maketarball",
      workdir="source/build",
      command=["../dist/scripts/maketarball.sh"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="move tarball to SOURCES",
      workdir="source/build",
      command="mv strawberry-*.tar.xz ~/rpmbuild/SOURCES",
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.Compile(
      name="run rpmbuild",
      workdir="source/build",
      command=["rpmbuild", "-ba", "../dist/unix/strawberry.spec"],
      haltOnFailure=True
    )
  )

  f.addStep(
    steps.SetPropertyFromCommand(
      name="get output filename",
      workdir="source",
      command=[
        "sh", "-c",
        "ls -dt ~/rpmbuild/RPMS/*/strawberry-*.rpm | grep -v debuginfo | grep -v debugsource | head -n 1"
      ],
      property="output-filepath",
      haltOnFailure=True
    )
  )
  f.addStep(steps.SetProperties(properties=get_base_filename))

  if not version in ['tumbleweed']:
    f.addStep(UploadPackage(distro + "/" + version))

  f.addStep(
    shell.ShellCommand(
      name="delete files",
      workdir="source",
      command="rm -f ~/rpmbuild/SOURCES/*.xz ~/rpmbuild/RPMS/*/*.rpm",
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="clean rpmbuild",
      workdir="source/build",
      command="find ~/rpmbuild/ -type f -delete"
    )
  )

  return f


def MakeDebBuilder(distro, version):

  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("strawberry", "master")))

  f.addStep(
    shell.ShellCommand(
      name="run cmake",
      workdir="source/build",
      command=["cmake", ".."],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.Compile(
      name="run dpkg-buildpackage",
      workdir="source",
      command=["dpkg-buildpackage", "-b", "-d", "-uc", "-us", "-nc", "-tc"],
      haltOnFailure=True
    )
  )

  f.addStep(
    steps.SetPropertyFromCommand(
      name="get output filename",
      workdir="source",
      command=[
        "sh", "-c",
        "ls -dt ../strawberry_*.deb | grep -v debuginfo | head -n 1"
      ],
      property="output-filepath",
      haltOnFailure=True
    )
  )
  f.addStep(steps.SetProperties(properties=get_base_filename))

  f.addStep(UploadPackage("%s/%s" % (distro, version)))

  f.addStep(
    shell.ShellCommand(
      name="delete file",
      workdir=".",
      command="rm -f *.deb *.ddeb *.buildinfo *.changes",
      haltOnFailure=True
    )
  )

  return f


def MakePPABuilder(distro, ppa_type, ppa_path):

  f = factory.BuildFactory()

  git_args = GitArgs("strawberry", "master")
  git_args["mode"] = "full"
  f.addStep(git.Git(**git_args))

  f.addStep(
    shell.ShellCommand(
      name="gpg import key",
      workdir="source",
      command="gpg --import --no-tty --batch --yes /config/secret/jonas-gpg-private-key",
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run cmake",
      workdir="source/build",
      command=["cmake", ".."],
      haltOnFailure=True,
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="cleanup",
      workdir="source",
      command="rm -rf .git build",
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run dpkg-buildpackage",
      workdir="source",
      command=["dpkg-buildpackage", "-S", "-d", "-k573D197B5EA20EDF"],
      haltOnFailure=True,
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="dput",
      workdir=".",
      command=["/config/dist/upload-ppa.sh", ppa_type, ppa_path],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="cleanup",
      workdir=".",
      command="rm -rf *.diff.*z *.tar.*z *.dsc *_source.changes *_source.buildinfo *_source.ppa.upload source/build/*",
      haltOnFailure=True
    )
  )

  return f


def MakePacmanBuilder(distro, version):

  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("strawberry", "master")))

  f.addStep(
    shell.ShellCommand(
      name="clean build",
      workdir="source",
      command="rm -rf build",
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run cmake",
      workdir="source/build",
      command=["cmake", ".."],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run maketarball",
      workdir="source/build",
      command=["../dist/scripts/maketarball.sh"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy PKGBUILD",
      workdir="source/build",
      command=["cp", "../dist/unix/PKGBUILD", "."],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.Compile(
      name="run makepkg",
      workdir="source/build",
      command=["makepkg", "-f"],
      haltOnFailure=True
    )
  )

  f.addStep(
    steps.SetPropertyFromCommand(
      name="get output filename",
      workdir="source",
      command=[
        "sh", "-c",
        "ls -dt build/strawberry-*.pkg.tar.xz | head -n 1"
      ],
      property="output-filepath",
      haltOnFailure=True
    )
  )
  f.addStep(steps.SetProperties(properties=get_base_filename))

  #f.addStep(UploadPackage(distro))

  f.addStep(
    shell.ShellCommand(
      name="delete file",
      workdir="source/build",
      command="rm -f *.xz",
      haltOnFailure=True
    )
  )

  return f


def MakeAppImageBuilder(name):

  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("strawberry", "master")))

  f.addStep(
    shell.ShellCommand(
      name="clean build",
      workdir="source",
      command="rm -rf build/AppDir",
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run cmake",
      workdir="source/build",
      command=["cmake", "..", "-DUSE_BUNDLE=ON", "-DCMAKE_INSTALL_PREFIX=/usr"],
      haltOnFailure=True
    )
  )

  f.addStep(
    steps.SetPropertyFromCommand(
      name="get version",
      workdir="source",
      command=["git", "describe", "--tags", "--always"],
      property="output-version",
      haltOnFailure=True
    )
  )
  env_output = {
    "OUTPUT": util.Interpolate("Strawberry%(kw:name)s-%(prop:output-version)s.AppImage", name=name)
  }

  f.addStep(
    shell.Compile(
      name="compile",
      workdir="source/build",
      command=["make", "-j", MAKE_JOBS],
      haltOnFailure=True
    )
  )
  f.addStep(
    shell.ShellCommand(
      name="run make install",
      workdir="source/build",
      command=["make", "install", "DESTDIR=AppDir"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="remove appdata",
      workdir="source/build",
      haltOnFailure=True,
      command=["rm", "./AppDir/usr/share/metainfo/org.strawberrymusicplayer.strawberry.appdata.xml"]
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="curl linuxdeploy-x86_64.AppImage",
      workdir="source/build",
      command=["curl", "-O", "-L", "https://artifacts.assassinate-you.net/artifactory/list/linuxdeploy/travis-456/linuxdeploy-x86_64.AppImage"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="curl linuxdeploy-plugin-appimage-x86_64.AppImage",
      workdir="source/build",
      command=["curl", "-O", "-L", "https://github.com/linuxdeploy/linuxdeploy-plugin-appimage/releases/download/continuous/linuxdeploy-plugin-appimage-x86_64.AppImage"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="curl linuxdeploy-plugin-qt-x86_64.AppImage",
      workdir="source/build",
      command=["curl", "-O", "-L", "https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-x86_64.AppImage"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run chmod",
      workdir="source/build",
      command="chmod +x linuxdeploy*.AppImage",
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run linuxdeploy --appimage-extract",
      workdir="source/build",
      command=["./linuxdeploy-x86_64.AppImage", "--appimage-extract"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run linuxdeploy-plugin-appimage --appimage-extract",
      workdir="source/build",
      command=["./linuxdeploy-plugin-appimage-x86_64.AppImage", "--appimage-extract"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run linuxdeploy-plugin-qt-x86_64.AppImage --appimage-extract",
      workdir="source/build",
      command=["./linuxdeploy-plugin-qt-x86_64.AppImage", "--appimage-extract"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run linuxdeploy",
      workdir="source/build",
      command=["./squashfs-root/usr/bin/linuxdeploy", "--appdir", "AppDir", "-e", "strawberry", "--plugin", "qt"],
      env=env_output,
      haltOnFailure=True
    )
  )

  gstreamer_plugins_files = [
    '/usr/lib64/gstreamer-1.0/libgstapp.so',
    '/usr/lib64/gstreamer-1.0/libgstcoreelements.so',
    '/usr/lib64/gstreamer-1.0/libgstaudioconvert.so',
    '/usr/lib64/gstreamer-1.0/libgstaudiofx.so',
    '/usr/lib64/gstreamer-1.0/libgstaudiomixer.so',
    '/usr/lib64/gstreamer-1.0/libgstaudioparsers.so',
    '/usr/lib64/gstreamer-1.0/libgstaudiorate.so',
    '/usr/lib64/gstreamer-1.0/libgstaudioresample.so',
    '/usr/lib64/gstreamer-1.0/libgstaudiotestsrc.so',
    '/usr/lib64/gstreamer-1.0/libgstaudiovisualizers.so',
    '/usr/lib64/gstreamer-1.0/libgstautodetect.so',
    '/usr/lib64/gstreamer-1.0/libgstautoconvert.so',
    '/usr/lib64/gstreamer-1.0/libgstplayback.so',
    '/usr/lib64/gstreamer-1.0/libgstvolume.so',
    '/usr/lib64/gstreamer-1.0/libgstspectrum.so',
    '/usr/lib64/gstreamer-1.0/libgstequalizer.so',
    '/usr/lib64/gstreamer-1.0/libgstlevel.so',
    '/usr/lib64/gstreamer-1.0/libgstreplaygain.so',
    '/usr/lib64/gstreamer-1.0/libgsttypefindfunctions.so',
    '/usr/lib64/gstreamer-1.0/libgstgio.so',
    '/usr/lib64/gstreamer-1.0/libgstalsa.so',
    '/usr/lib64/gstreamer-1.0/libgstoss4.so',
    '/usr/lib64/gstreamer-1.0/libgstossaudio.so',
    '/usr/lib64/gstreamer-1.0/libgstpulseaudio.so',
    '/usr/lib64/gstreamer-1.0/libgstapetag.so',
    '/usr/lib64/gstreamer-1.0/libgsticydemux.so',
    '/usr/lib64/gstreamer-1.0/libgstid3demux.so',
    '/usr/lib64/gstreamer-1.0/libgstxingmux.so',
    '/usr/lib64/gstreamer-1.0/libgsttcp.so',
    '/usr/lib64/gstreamer-1.0/libgstudp.so',
    '/usr/lib64/gstreamer-1.0/libgstsoup.so',
    '/usr/lib64/gstreamer-1.0/libgstcdio.so',

    '/usr/lib64/gstreamer-1.0/libgstflac.so',
    '/usr/lib64/gstreamer-1.0/libgstwavparse.so',
    '/usr/lib64/gstreamer-1.0/libgstwavpack.so',
    '/usr/lib64/gstreamer-1.0/libgstogg.so',
    '/usr/lib64/gstreamer-1.0/libgstvorbis.so',
    '/usr/lib64/gstreamer-1.0/libgstopus.so',
    '/usr/lib64/gstreamer-1.0/libgstopusparse.so',
    '/usr/lib64/gstreamer-1.0/libgstspeex.so',
    '/usr/lib64/gstreamer-1.0/libgstlame.so',
    '/usr/lib64/gstreamer-1.0/libgstaiff.so',
    '/usr/lib64/gstreamer-1.0/libgstasfmux.so',
    '/usr/lib64/gstreamer-1.0/libgstisomp4.so',
    '/usr/lib64/gstreamer-1.0/libgstlibav.so',
    '/usr/lib64/gstreamer-1.0/libgstfaad.so',
    '/usr/lib64/gstreamer-1.0/libgstasf.so',
    '/usr/lib64/gstreamer-1.0/libgstrealmedia.so',

    #'/usr/lib64/gstreamer-1.0/libgstmusepack.so',
  ]

  #f.addStep(
  #  shell.ShellCommand(
  #    name="mkdir gstreamer",
  #    workdir="source/build",
  #    command=[ "mkdir", "-p", "./AppDir/usr/plugins/gstreamer" ],
  #    haltOnFailure=True
  #  )
  #)

  # Bundling plugins in ./AppDir/usr/plugins/gstreamer doesn't work so just link the directory to the lib dir.

  f.addStep(
    shell.ShellCommand(
      name="link gstreamer plugins",
      workdir="source/build/AppDir/usr/plugins",
      command=[ "ln", "-s", "../lib/", "gstreamer" ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="list gstreamer plugins",
      workdir="source/build",
      command=[ "ls", "-la", "/usr/lib64/gstreamer-1.0/" ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy gstreamer plugins",
      workdir="source/build",
      command=[ "cp", "-f", gstreamer_plugins_files, "./AppDir/usr/plugins/gstreamer/" ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy gstreamer plugin scanner",
      workdir="source/build",
      command=["cp", "-r", "-f", "/usr/libexec/gstreamer-1.0/gst-plugin-scanner", "./AppDir/usr/plugins/"],
      env=env_output,
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run linuxdeploy output appimage",
      workdir="source/build",
      command=["./squashfs-root/usr/bin/linuxdeploy", "--appdir", "AppDir", "-e", "strawberry", "--plugin", "qt", "--output", "appimage"],
      env=env_output,
      haltOnFailure=True
    )
  )

  f.addStep(
    steps.SetPropertyFromCommand(
      name="get output filename",
      workdir="source",
      command=[
        "sh", "-c",
        "ls -dt build/Strawberry*.AppImage | head -n 1"
      ],
      property="output-filepath",
      haltOnFailure=True
    )
  )
  f.addStep(steps.SetProperties(properties=get_base_filename))
  f.addStep(UploadPackage("appimage"))

  f.addStep(
    shell.ShellCommand(
      name="delete files",
      workdir="source/build",
      command="rm -rf AppDir *.AppImage",
      haltOnFailure=True
    )
  )

  return f


def MakeMXEBuilder():

  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("strawberry-mxe", "master")))

  f.addStep(
    shell.Compile(
      name="compile",
      workdir="source",
      command=["make", "-j", MAKE_JOBS, "icu4c" ],
      timeout=108000,
      haltOnFailure=True,
    )
  )

  f.addStep(
    shell.Compile(
      name="compile",
      workdir="source",
      command=["make", "-j", MAKE_JOBS],
      timeout=108000,
      haltOnFailure=True,
    )
  )

  return f


def MakeWindowsBuilder(is_debug, is_64, with_qt6):

  env_lang = {
    "RC_LANG": "en_US.UTF-8",
    "RC_LC_ALL": "en_US.UTF-8",
    "RC_LC_CTYPE": "en_US.UTF-8",
    "RC_LC_TIME": "nb_NO.UTF-8",
    "RC_LC_NUMERIC": "nb_NO.UTF-8",
    "RC_LC_MONETARY": "nb_NO.UTF-8",
    "RC_LC_PAPER": "nb_NO.UTF-8",
  }

  mingw32_name = ("x86_64-w64-mingw32.shared" if is_64 else "i686-w64-mingw32.shared")
  qt_dir = ("qt6" if with_qt6 else "qt5")

  env = {
    "PKG_CONFIG_LIBDIR": "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/lib/pkgconfig",
    "PATH": ":".join([
      "/persistent-data/mingw/mxe/source/usr/x86_64-pc-linux-gnu/bin",
      "/usr/local/bin",
      "/usr/bin",
      "/bin",
    ]),
  }

  cmake_cmd = [
    "cmake",
    "..",
    "-DCMAKE_TOOLCHAIN_FILE=/config/dist/" + ("Toolchain-x86_64-w64-mingw32.cmake" if is_64 else "Toolchain-i686-w64-mingw32.cmake"),
    "-DCMAKE_BUILD_TYPE=" + ("Debug" if is_debug else "Release"),
    "-DARCH=" + ("x86_64" if is_64 else "x86"),
    "-DENABLE_WIN32_CONSOLE=" + ("ON" if is_debug else "OFF"),
    "-DENABLE_DBUS=OFF",
    "-DENABLE_LIBGPOD=OFF",
    "-DENABLE_IMOBILEDEVICE=OFF",
    "-DENABLE_LIBMTP=OFF",
    "-DUSE_SYSTEM_TAGLIB=OFF",
    "-DWITH_QT6=" + ("ON" if with_qt6 else "OFF"),
  ]

  executable_files = [
    "strawberry.exe",
    "strawberry-tagreader.exe",
  ]

  strip_command = "/persistent-data/mingw/mxe/source/usr/bin/" + mingw32_name + "-strip"
  nsi_filename = "strawberry.nsi"

  nsi_files = [
    "strawberry.nsi",
    "Capabilities.nsh",
    "FileAssociation.nsh",
    "strawberry.ico",
  ]

  imageformats_files = [
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/" + qt_dir + "/plugins/imageformats/qgif.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/" + qt_dir + "/plugins/imageformats/qjpeg.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/" + qt_dir+ "/plugins/imageformats/qico.dll",
  ]
  gstreamer_plugins_files = [
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstapp.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstcoreelements.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstaudioconvert.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstaudiofx.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstaudiomixer.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstaudioparsers.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstaudiorate.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstaudioresample.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstaudiotestsrc.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstautodetect.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstplayback.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstvolume.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstspectrum.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstequalizer.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstreplaygain.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgsttypefindfunctions.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstgio.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstdirectsound.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstwasapi.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstpbtypes.dll",

    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstapetag.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgsticydemux.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstid3demux.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgsttaglib.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgsttcp.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstudp.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstsoup.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstcdio.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstrtp.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstrtsp.dll",

    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstflac.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstwavparse.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstwavpack.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstogg.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstvorbis.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstopus.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstopusparse.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstspeex.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstlame.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstaiff.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstfaac.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstfaad.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstisomp4.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstasf.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstasfmux.dll",
    "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/gstreamer-1.0/libgstlibav.dll",
  ]

  f = factory.BuildFactory()
  f.addStep(git.Git(**GitArgs("strawberry", "master")))

  f.addStep(
    shell.ShellCommand(
      name="run cmake",
      workdir="source/build",
      command=cmake_cmd,
      env=env,
      haltOnFailure=True
    )
  )
  f.addStep(
    shell.Compile(
      name="compile",
      command=["make", "-j", MAKE_JOBS],
      workdir="source/build",
      haltOnFailure=True
    )
  )
  f.addStep(
    shell.ShellCommand(
      name="run strip",
      workdir="source/build",
      command=[strip_command] + executable_files,
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="mkdir platforms/sqldrivers/imageformats/styles/gstreamer-plugins/nsisplugins",
      workdir="source/build",
      command=[
        "mkdir",
        "-p",
        "gio-modules"
        "platforms",
        "sqldrivers",
        "imageformats",
        "styles",
        "gstreamer-plugins",
        "nsisplugins",
      ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy libgiognutls.dll",
      workdir="source/build/gio-modules",
      command=[
        "cp",
        "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/lib/gio/modules/libgiognutls.dll",
        ".",
      ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy qwindows.dll",
      workdir="source/build/platforms",
      command=[
        "cp",
        "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/" + qt_dir + "/plugins/platforms/qwindows.dll",
        ".",
      ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy qsqlite.dll",
      workdir="source/build/sqldrivers",
      command=[
        "cp",
        "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/" + qt_dir + "/plugins/sqldrivers/qsqlite.dll",
        ".",
      ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy imageformats",
      workdir="source/build/imageformats",
      command=[
        "cp",
        imageformats_files,
        ".",
      ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy styles",
      workdir="source/build/styles",
      command=[
        "cp",
        "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/" + qt_dir + "/plugins/styles/qwindowsvistastyle.dll",
        ".",
      ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy gstreamer-plugins",
      workdir="source/build/gstreamer-plugins",
      command=[
        "cp",
        gstreamer_plugins_files,
        ".",
      ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy liborc",
      workdir="source/build",
      command=[
        "cp",
        "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/liborc-0.4-0.dll",
        ".",
      ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copydlldeps.sh",
      workdir="source/build",
      command=[
        "/persistent-data/mingw/mxe/source/tools/copydlldeps.sh",
        "-c",
        "-d",
        ".",
        "-F",
        ".",
        "-F",
        "./platforms",
        "-F",
        "./sqldrivers",
        "-F",
        "./imageformats",
        "-F",
        "./styles",
        "-F",
        "./gstreamer-plugins",
        "-X",
        "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/apps",
        "-R",
        "/persistent-data/mingw/mxe/source/usr/" + mingw32_name,
      ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy nsi files",
      workdir="source/dist/windows",
      command=["cp", nsi_files, "../../build/" ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy killproc.exe",
      workdir="source/build",
      command=["cp", "/persistent-data/mingw/mxe/source/usr/" + mingw32_name + "/bin/killproc.exe", "." ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run makensis",
      command=["makensis", nsi_filename],
      workdir="source/build",
      env=env_lang,
      haltOnFailure=True
    )
  )

  f.addStep(
    steps.SetPropertyFromCommand(
      name="get output filename",
      workdir="source",
      command=[
        "sh",
        "-c",
        "ls -dt " + "build/StrawberrySetup-*.exe" + " | head -n 1"
      ],
      property="output-filepath",
      haltOnFailure=True
    )
  )
  f.addStep(steps.SetProperties(properties=get_base_filename))

  if with_qt6:
    f.addStep(UploadPackage("windows-qt6-exprimental"))
  else:
    f.addStep(UploadPackage("windows"))

  f.addStep(
    shell.ShellCommand(
      name="delete files",
      workdir="source/build",
      command="rm -rf *.exe *.dll gio-modules platforms sqldrivers imageformats styles gstreamer-plugins nsisplugins",
      haltOnFailure=True
    )
  )

  return f

