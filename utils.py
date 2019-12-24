"""
Utility functions.
"""
import importlib
# importlib quirks....
import importlib.util
import json
import os
import re
import subprocess
import stat
import sys
import urllib.request
from packaging import version


def plug_debug(line):
    """
    Use $PWD/debug.log as stdout for print()-debugging a plugin
    """
    with open(os.path.join(os.getcwd(), "plugin_debug.log"), "a") as f:
        f.write(line + '\n')


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


def get_main_file(dir_path):
    """
    Returns the path to the first executable file of the provided directory
    """
    content = os.listdir(dir_path)
    for file in content:
        abs_path = os.path.join(dir_path, file)
        if os.access(abs_path, os.X_OK):
            return abs_path
    return None


def dl_github_repo(install_path, api_url, html_url):
    """
    Downloads all files from a Github repo, uses the frontend as much as
    possible in order to minimize API requests.

    :param install_path: Where to "clone" the repo.
    :param api_url: Github repo API url, of the form
                    `repos/<owner>/<repo>/git/trees/<sha>`.
    :param html_url: Github frontend repo url, of the form
                     `<owner>/<repo>/tree/<sha>`.
    """
    html_url = html_url.replace("//github.com", "//raw.githubusercontent.com")
    html_url = html_url.replace("/tree/", '/')
    json_string = urllib.request.urlopen(api_url + "?recursive=1").read()
    json_content = json.loads(json_string.decode("utf-8"))
    for element in json_content["tree"]:
        if element["path"][0] == '.':
            continue
        if element["mode"] == "040000":
            # We'll handle subdir creation below
            continue
        elif element["mode"] == "160000":
            # FIXME: Support submoduleception
            raise Exception("I don't support submodule inside a submodule")
        abs_path = os.path.join(install_path, element["path"])
        if len(element["path"].split('/')) > 1:
            subdirs = "/".join(abs_path.split('/')[:-1])
            os.makedirs(os.path.join(install_path, subdirs), exist_ok=True)
        urllib.request.urlretrieve(html_url + '/' + element["path"], abs_path)
        if element["mode"] == "100755":
            make_executable(abs_path)


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
            dl_github_repo(install_path, json_content["git_url"],
                           json_content["html_url"])
            return
        else:
            raise ValueError("Could not parse json: {}".format(json_content))
    for i in json_content:
        if "download_url" in i:
            if i["download_url"] is not None:
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
        elif "submodule_git_url" in i:
            dl_github_repo(os.path.join(install_path, i["name"]),
                           json_content["submodule_git_url"],
                           json_content["html_url"])


def install_folder_from_github(install_path, url):
    """
    This downloads the plugin folder from a repository, and makes the suitable
    file executable.

    :param install_path: Where to store the folder.
    :param url: Github API url of the form
                `api.github.com/repos/<owner>/<repo>/contents`.
    """
    assert re.match(r".*api.github.com/repos/.*/contents", url) is not None
    *repo_url, folder_name = url.split('/')
    dl_folder_from_github(install_path, url)
    # *The only* endpoint which has `mode` fields.. Required to make the
    # right file executable
    repo_url = '/'.join(repo_url)
    repo_url = repo_url.replace("/contents",
                                "/git/trees/master?recursive=1")
    json_repo = urllib.request.urlopen(repo_url).read()
    repo_content = json.loads(json_repo.decode("utf-8"))
    for element in repo_content["tree"]:
        if element["path"].startswith(folder_name):
            if element["mode"] == "100755":
                file_name = element["path"].split('/')[-1]
                file_path = os.path.join(install_path, file_name)
                make_executable(file_path)


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
    # Simple case: there is a Makefile
    for name in content:
        if name == "Makefile":
            subprocess.check_output(["make"])
            return
    # Otherwise we can still try to `go build` go plugins
    for filename in [name for name in content if '.' in name]:
        if filename.split('.')[1] == "go":
            try:
                go_bin = os.path.abspath("go")
                subprocess.check_output([go_bin, "build"])
            except (FileNotFoundError, subprocess.CalledProcessError):
                raise Exception("Could not 'go build' the plugin, is golang"
                                " installed ?")


def pip_install(package):
    """
    'pip' install a Python package if not already installed (likely, globally
    installed)
    """
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
