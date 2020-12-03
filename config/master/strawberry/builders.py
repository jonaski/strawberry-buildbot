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

  cmake_qt_flag = "-DBUILD_WITH_QT6=ON" if name == "Qt6" else "-DBUILD_WITH_QT5=ON"

  f.addStep(
    shell.ShellCommand(
      name="run cmake",
      workdir="source/build",
      command=["cmake", "..", "-DCMAKE_INSTALL_PREFIX=/usr", cmake_qt_flag],
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
  env_version = {
    "VERSION": util.Interpolate("%(prop:output-version)s-%(kw:name)s", name=name)
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
      name="rename strawberry-tagreader",
      workdir="source/build",
      command=["mv", "AppDir/usr/bin/strawberry-tagreader", "./AppDir/usr/bin/strawberry-tagreader-bin"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy strawberry-tagreader.sh",
      workdir="source/build",
      command=["cp", "/config/dist/strawberry-tagreader.sh", "./AppDir/usr/bin/strawberry-tagreader"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="cp appdata",
      workdir="source/build",
      haltOnFailure=True,
      command=["cp", "./AppDir/usr/share/metainfo/org.strawberrymusicplayer.strawberry.appdata.xml", "./AppDir/"]
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="cp icon",
      workdir="source/build",
      haltOnFailure=True,
      command=["cp", "./AppDir/usr/share/icons/hicolor/128x128/apps/strawberry.png", "./AppDir/"]
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run appimagetool deploy",
      workdir="source/build",
      command=["appimagetool", "-s", "deploy", "AppDir/usr/share/applications/org.strawberrymusicplayer.strawberry.desktop"],
      env=env_version,
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy gst-plugin-scanner.sh",
      workdir="source/build",
      command=["cp", "/config/dist/gst-plugin-scanner.sh", "./AppDir/usr/libexec/gstreamer-1.0/"],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="run appimagetool",
      workdir="source/build",
      command=["appimagetool", "AppDir"],
      env=env_version,
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

  mingw32_name = ("x86_64-w64-mingw32.shared" if is_64 else "i686-w64-mingw32.shared")
  qt_dir = ("qt6" if with_qt6 else "qt5")
  mxe_path = "/persistent-data/mingw/mxe/source"
  target_path = mxe_path + "/usr/" + mingw32_name

  env = {
    "PKG_CONFIG_LIBDIR": target_path + "/lib/pkgconfig",
    "PATH": ":".join([
      mxe_path + "/usr/x86_64-pc-linux-gnu/bin",
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
    "-DBUILD_WITH_QT6=" + ("ON" if with_qt6 else "OFF"),
    "-DUSE_SYSTEM_TAGLIB=OFF",
    "-DENABLE_DBUS=OFF",
    "-DENABLE_LIBGPOD=OFF",
    "-DENABLE_LIBMTP=OFF",
  ]

  strip_cmd = mxe_path + "/usr/bin/" + mingw32_name + "-strip"

  extra_binary_fileslist = [
    "liborc-0.4-0.dll",
    "sqlite3.exe",
    "killproc.exe",
    "gdb.exe",
    "gst-launch-1.0.exe",
  ]
  extra_binary_files = []
  for i in extra_binary_fileslist:
    extra_binary_files.append(target_path + "/bin/" + i)

  nsi_files = [
    "strawberry.nsi",
    "Capabilities.nsh",
    "FileAssociation.nsh",
    "strawberry.ico",
  ]

  imageformats_filelist = [
    "qgif.dll",
    "qjpeg.dll",
    "qico.dll",
  ]
  imageformats_files = []
  for i in imageformats_filelist:
    imageformats_files.append(target_path + "/" + qt_dir + "/plugins/imageformats/" + i)

  gstreamer_plugins_path = target_path + "/bin/gstreamer-1.0/"
  gstreamer_plugins_filelist = [
    "libgstapp.dll",
    "libgstcoreelements.dll",
    "libgstaudioconvert.dll",
    "libgstaudiofx.dll",
    "libgstaudiomixer.dll",
    "libgstaudioparsers.dll",
    "libgstaudiorate.dll",
    "libgstaudioresample.dll",
    "libgstaudiotestsrc.dll",
    "libgstautodetect.dll",
    "libgstplayback.dll",
    "libgstvolume.dll",
    "libgstspectrum.dll",
    "libgstequalizer.dll",
    "libgstreplaygain.dll",
    "libgsttypefindfunctions.dll",
    "libgstgio.dll",
    "libgstdirectsound.dll",
    "libgstwasapi.dll",
    "libgstpbtypes.dll",
    "libgstapetag.dll",
    "libgsticydemux.dll",
    "libgstid3demux.dll",
    "libgsttaglib.dll",
    "libgsttcp.dll",
    "libgstudp.dll",
    "libgstsoup.dll",
    "libgstcdio.dll",
    "libgstrtp.dll",
    "libgstrtsp.dll",
    "libgstflac.dll",
    "libgstwavparse.dll",
    "libgstwavpack.dll",
    "libgstogg.dll",
    "libgstvorbis.dll",
    "libgstopus.dll",
    "libgstopusparse.dll",
    "libgstspeex.dll",
    "libgstlame.dll",
    "libgstaiff.dll",
    "libgstfaac.dll",
    "libgstfaad.dll",
    "libgstisomp4.dll",
    "libgstasf.dll",
    "libgstasfmux.dll",
    "libgstlibav.dll",
  ]

  gstreamer_plugins_files = []
  for i in gstreamer_plugins_filelist:
    gstreamer_plugins_files.append(gstreamer_plugins_path + "/" + i)

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
      command=[ "make", "-j", MAKE_JOBS ],
      workdir="source/build",
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
      command=[ "cp", target_path + "/lib/gio/modules/libgiognutls.dll", "." ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy qwindows.dll",
      workdir="source/build/platforms",
      command=[ "cp", target_path + "/" + qt_dir + "/plugins/platforms/qwindows.dll", "." ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy qsqlite.dll",
      workdir="source/build/sqldrivers",
      command=[ "cp", target_path + "/" + qt_dir + "/plugins/sqldrivers/qsqlite.dll", ".", ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy qt imageformats",
      workdir="source/build/imageformats",
      command=[ "cp", imageformats_files, "." ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy qt styles",
      workdir="source/build/styles",
      command=[ "cp", target_path + "/" + qt_dir + "/plugins/styles/qwindowsvistastyle.dll", "." ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy gstreamer-plugins",
      workdir="source/build/gstreamer-plugins",
      command=[ "cp", gstreamer_plugins_files, "." ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copy extra binaries",
      workdir="source/build",
      command=[ "cp", extra_binary_files, "." ],
      haltOnFailure=True
    )
  )

  f.addStep(
    shell.ShellCommand(
      name="copydlldeps.sh",
      workdir="source/build",
      command=[
        mxe_path + "/tools/copydlldeps.sh",
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
        target_path + "/apps",
        "-R",
        target_path,
      ],
      haltOnFailure=True
    )
  )

  if not is_debug:
    f.addStep(
      shell.ShellCommand(
        name="run strip",
        workdir="source/build",
        command=[ "/config/dist/win-strip.sh", strip_cmd ],
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
      name="run makensis",
      command=[ "makensis", "strawberry.nsi" ],
      workdir="source/build",
      haltOnFailure=True
    )
  )

  f.addStep(
    steps.SetPropertyFromCommand(
      name="get output filename 1",
      workdir="source",
      command=[ "sh", "-c", "ls -dt " + "build/StrawberrySetup-*.exe" + " | head -n 1" ],
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

