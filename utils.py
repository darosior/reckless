"""
Utility functions.
"""
import importlib
import json
import os
import re
import subprocess
import stat
import sys
import urllib.request
import zipfile
from packaging import version


def plug_debug(line):
    """
    Use $PWD/debug.log as stdout for print()-debugging a plugin
    """
    with open(os.path.join(os.getcwd(), "plugin_debug.log"), "a") as f:
        f.write(line)


def create_dir(abs_path):
    """
    Creates a directory
    """
    if not os.path.isdir(abs_path):
        subprocess.call(["mkdir", "-p", abs_path])


def make_executable(abs_path):
    """
    Add the exec permission to a file
    """
    os.chmod(abs_path, os.stat(abs_path).st_mode | stat.S_IEXEC)


def get_main_file(possible_filenames, install_path):
    """
    Tries to detect the main file of a plugin directory
    """
    content = os.listdir(install_path)
    if len(content) == 1:
        tmp_file = os.path.join(install_path, content[0])
        if not os.path.isdir(tmp_file):
            # There is only one file, this is the main one !
            return tmp_file
        else:
            # The archive actually contained a directory, let's clean it up
            for f in os.listdir(tmp_file):
                os.rename(os.path.join(tmp_file, f),
                          os.path.join(install_path, f))
            os.rmdir(tmp_file)
            content = os.listdir(install_path)
    # Iterate through all files that are not source files of a compiled
    # language, to check if there is the main one
    for filename in [f for f in content
                     if os.path.isfile(os.path.join(install_path, f))
                     and not re.findall(r"^.*\.cpp|\.c|\.go$",
                                        os.path.join(install_path, f))]:
        # FIXME: Improve main file detection
        for possible_filename in possible_filenames:
            if possible_filename in filename:
                return os.path.join(install_path, filename)
    return None


def dl_github_repo(install_path, url):
    """
    Downloads a whole Github repo, then delete the '.git' directory.

    :param install_path: Where to clone the repo.
    :param url: Repo url.
    """
    url = url.replace(".git", "")
    # Let's download it as a zip
    dl_url = url + "archive/master.zip" if url[:-1] == '/' \
                                        else url + '/' + "archive/master.zip"
    zip_path, _ = urllib.request.urlretrieve(dl_url,
                               os.path.join(install_path, url.split("/")[-1]))
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        zip_file.extractall(install_path)
    os.remove(zip_path)
    # Remove extra dir (likely "<pluginname>-master")
    if len(os.listdir(install_path)) == 1:
        extra_dir = os.path.join(install_path, os.listdir(install_path)[0])
        for name in os.listdir(extra_dir):
            os.rename(os.path.join(extra_dir, name),
                      os.path.join(install_path, name))
        os.rmdir(extra_dir)


def dl_folder_from_github(install_path, url):
    """
    Recursively fetches files from a github repo's folder.

    :param install_path: Where to store the folder.
    :param url: From where to fetch the folder (Github API url).
    """
    if not re.search(r"[api.github.com/repos/]+[/contents/]+", url):
        raise ValueError("Unsupported url")
    json_string = urllib.request.urlopen(url).read().decode("utf-8")
    json_content = json.loads(json_string)
    if not isinstance(json_content, list):
        if "submodule_git_url" in json_content:
            # For 'git@username:repo/' urls
            repo_url = json_content["submodule_git_url"]
            if "git@" in repo_url:
                repo_url = repo_url.replace(":", "/")
                repo_url = repo_url.replace("git@", "http://")
            dl_github_repo(install_path, repo_url)
            return
        else:
            raise ValueError("Could not parse json: {}".format(json_content))
    for i in json_content:
        if "download_url" in i:
            if i["download_url"]:
                dest = os.path.join(install_path, i["name"])
                urllib.request.urlretrieve(i["download_url"], dest)
            # This is a folder
            else:
                new_install_path = os.path.join(install_path, i["name"])
                create_dir(new_install_path)
                dl_folder_from_github(new_install_path,
                                      url + i["name"] if url[:-1] == '/' else
                                      url + '/' + i["name"])
        # Unlikely
        if "submodule_git_url" in i:
            dl_github_repo(os.path.join(install_path, i["name"]),
                           json_content["submodule_git_url"])


def handle_requirements(directory):
    """
    Handles the 'pip install's if this is a Python plugin (most are).
    """
    content = os.listdir(directory)
    for filename in content:
        if "requirements" in filename:
            with open(os.path.join(directory, filename), 'r') as f:
                for line in f:
                    # Some requirements.txt have blank lines...
                    if line not in {'\n', ' '}:
                        pip_install(line)


def handle_compilation(directory):
    """
    Handles the compilation of a GO/C/C++ plugin
    """
    content = os.listdir(directory)
    for filename in [name for name in content if '.' in name]:
        if filename.split('.')[1] == "go":
            # Check for a Makefile otherwise `go build` it
            for name in content:
                if name == "Makefile":
                    subprocess.check_output(["make"])
                    return
            try:
                go_bin = os.path.abspath("go")
                subprocess.check_output([go_bin, "build"])
            except (FileNotFoundError, subprocess.CalledProcessError):
                raise Exception("Could not 'go build' the plugin, is golang"
                                "installed ?")
            return
        elif filename.split('.')[1] in {"c", "cpp"}:
            # We need a Makefile
            for name in content:
                if name == "Makefile":
                    subprocess.check_output(["make"])
                    return


def pip_install(package):
    """
    'pip' install a Python package if not already installed (likely, globally
    installed)
    """
    # Raising an error here is vital because starting a plugin without its
    # requirements installed will crash `lightningd`.
    package_name = package.split("==")[0]
    if ">=" in package:
        package_name = package.split(">=")[0]
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        # MUST NOT fail
        subprocess.check_output([sys.executable, "-m", "pip",
                                 "install", package])
    if "==" in package:
        package_version = version.parse(package.split("==")[1])
        try:
            installed_version = version.parse(importlib.
                                              import_module(package_name)
                                              .__version__)
            if package_version > installed_version:
                # MUST NOT fail
                subprocess.check_output([sys.executable, "-m", "pip",
                                         "install", package])
        except AttributeError:
            # No __version__ ..
            pass
    spec = importlib.util.find_spec(package_name)
    assert spec is not None
