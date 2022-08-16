# ------------< Ardent >-------------
# A script to build Ardour on Windows
# -----------------------------------

import subprocess
import os

try:
    from colorama import init as colorama_init
    colorama_init()
except:
    pass

SYSTEM_DEPENDENCIES = set(
    [f"mingw-w64-x86_64-{x}" for x in [
        "atk",
        "atkmm",
        "binutils",
        "boost",
        "c-ares",
        "ca-certificates",
        "cairo",
        "cairomm",
        "cmake",
        "cppunit",
        "crt-git",
        "curl",
        "dlfcn",
        "docbook-xsl",
        "fftw",
        "flac",
        "fontconfig",
        "freetype",
        "gcc",
        "gcc-libs",
        "gcc-objc",
        "gdb",
        "gdb-multiarch",
        "gdk-pixbuf2",
        "gettext",
        "glib2",
        "glibmm",
        "gnome-common",
        "gnutls",
        "gobject-introspection",
        "gtk-doc",
        "gtk2",
        "gtkmm",
        "harfbuzz",
        "headers-git",
        "icu",
        "jasper",
        "jbigkit",
        "ladspa-sdk",
        "libgccjit",
        "libidn",
        "libjpeg-turbo",
        "libmangle-git",
        "libogg",
        "libpng",
        "libsamplerate",
        "libsigc++",
        "libsndfile",
        "libssh2",
        "libtiff",
        "libusb",
        "libvorbis",
        "libxml2",
        "libwinpthread-git",
        "lld",
        "lua",
        "make",
        "meson",
        "nasm",
        "pango",
        "pangomm",
        "pcre",
        "perl",
        "pixman",
        "pkgconf",
        "portaudio",
        "python",
        "python-setuptools",
        "rtmpdump-git",
        "rubberband",
        "shared-mime-info",
        "soundtouch",
        "taglib",
        "tools-git",
        "vamp-plugin-sdk",
        "wget",
        "wineditline",
        "winpthreads-git",
        "winstorecompat-git",
    ]] + [
        "autoconf",
        "autogen",
        "automake-wrapper",
        "bison",
        "dos2unix",
        "flex",
        "git",
        "gnome-doc-utils",
        "gtk-doc",
        "intltool",
        "libgnutls-devel",
        "libtool",
        "libutil-linux-devel",
        "msys2-runtime-devel",
        "patch",
        "pkgconf",
    ]
)

class ArdentError(Exception):
    """Base exception class used for all unrecoverable script errors."""
    
    def __init__(self, message):
        self.message = message

def status(message, color="96"):
    """Prints out a message in colored text."""
    print(f"\u001b[{color}m{message}\u001b[0m")

def run(*args, **kwargs):
    """Runs a command, raising ArdentError if the return code is non-zero."""
    command_line = ' '.join(args[0])
    status(f"> {command_line}", color="94")
    out = subprocess.run(*args, **kwargs, encoding='utf8')
    if out.returncode != 0:
        raise ArdentError(f"\nFailed to run subprocess (exit code {out.returncode}):\n{command_line}")
    return out

def clone(url, target_dir="."):
    """Clones a repository if it doesn't already exist. Returns True if the repository was cloned."""
    if not os.path.isdir(target_dir + os.path.sep + url.split("/")[-1]):
        run(["git", "clone", "--recurse-submodules", url], cwd=target_dir)
        return True
    else:
        return False

def patch(patch_name):
    """Applies a patch from the patches/ directory."""
    run(["patch", "-i", "patches/" + patch_name, "-p0"])

def waf(*args, cwd="./", waf="waf", env={}, c=False, cxx=False):
    """Runs ./waf with a couple of default options."""
    options = ["python3", waf, "configure", "build", "install", "--prefix=/mingw64"]
    if c:
        options.append("--check-c-compiler=gcc")
    if cxx:
        options.append("--check-cxx-compiler=g++")
    if len(args) > 0 and type(args[0]) is list:
        options += args[0]
    run(options, cwd=cwd, env=dict(os.environ) | env)

def ac(cwd="./"):
    """Runs autogen && make install"""
    run(["sh", "./autogen.sh"], cwd=cwd, env=dict(os.environ) | {"ACLOCAL_PATH": "/usr/share/aclocal"})
    run(["make", "install"], cwd=cwd)

def meson(*args, cwd="./"):
    """Sets up and invokes meson"""
    build = cwd + os.path.sep + "build"
    if not os.path.isdir(build):
        run(["meson", "setup", "build"], cwd=cwd)

    options = ["meson", "configure"]
    if len(args) > 0 and type(args[0]) is list:
        options += args[0]
    run(options, cwd=build)
    run(["meson", "compile"], cwd=build)
    run(["meson", "install"], cwd=build)

def check_shell():
    if os.getenv("MSYSTEM") != "MINGW64":
        raise ArdentError("Ardent should be executed from a MSYS2 shell. If you don't have MSYS2, you can install it from https://www.msys2.org/.")

def install_package_deps():
    status("Checking packages...")
    packages = set(run(["pacman", "-Qq"], stdout=subprocess.PIPE).stdout.split("\n"))
    to_install = SYSTEM_DEPENDENCIES - packages

    if to_install:
        status("Installing required dependencies...")
        run(["pacman", "-S", "--noconfirm", "--needed"] + list(to_install))
        status("Installed all required system dependencies.")
    else:
        status("All system dependencies have already been installed.")

def fetch_libraries():
    status("Fetching libraries...")
    clone("https://github.com/jackaudio/jack2", target_dir="deps")
    if clone("https://github.com/aubio/aubio", target_dir="deps"):
        patch("aubio_priv.h.patch")
    clone("https://github.com/radarsat1/liblo", target_dir="deps")
    clone("https://github.com/x42/libltc", target_dir="deps")
    if clone("https://github.com/swh/LRDF", target_dir="deps"):
        patch("lrdf_types.h.patch")
    if clone("https://github.com/dajobe/raptor", target_dir="deps"):
        patch("sort_r.h.patch")
    if clone("https://github.com/lv2/lv2kit", target_dir="deps"):
        patch("win_in_gtk2.cpp.patch")
    if clone("git://git.ardour.org/ardour/ardour", target_dir="deps"):
        patch("ardour-wscript.patch")
        patch("main.cc.patch")
        patch("pbd.cc.patch")

def build_libraries():
    status("Building libraries...")
    waf(cwd="deps/jack2", c=True, cxx=True)
    ac(cwd="deps/liblo")
    ac(cwd="deps/libltc")
    ac(cwd="deps/raptor")
    ac(cwd="deps/LRDF")
    meson(["-Dcxx=true"], cwd="deps/lv2kit")
    waf(["--disable-tests"], cwd="deps/aubio", waf="../ardour/waf", c=True)

def build_ardour():
    status("Building Ardour...")
    waf(
        [
            "--prefix=/mingw64",
            "--configdir=/share",
            "--check-c-compiler=gcc",
            "--check-cxx-compiler=g++",
            "--dist-target=mingw",
            "--no-dr-mingw",
            "--use-lld",
            "--optimize",
            "--exports-hidden",
            "--windows-vst",
        ],
        cwd="deps/ardour",
        env={
            "PKG_CONFIG_PATH": os.getenv("PKG_CONFIG_PATH") + os.path.pathsep + "C:\\mingw64\\lib\\pkgconfig"
        },
        c=True,
        cxx=True,
    )

def main():
    check_shell()
    install_package_deps()
    fetch_libraries()
    build_libraries()
    build_ardour()

if __name__ == "__main__":
    try:
        main()
    except ArdentError as e:
        status(e.message, color="91")
        raise
