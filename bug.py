#!/usr/bin/env python3
import os
import tarfile
import time
import urllib.parse
import urllib.request
import zipfile

from descriptions import (
    install_description, install_long_description, search_description,
    search_long_description
)
from pylightning import Plugin
from search import search_github
from utils import (
    create_dir, get_main_file, dl_folder_from_github, make_executable
)


plugin = Plugin()


@plugin.init()
def init(plugin, options, configuration):
    plugin.plugins_path = os.path.join(plugin.lightning_dir, "plugins")
    if "plugins-path" in configuration:
        plugin.plugins_path = configuration["plugins-path"]
    plugin.log("Plugin bug.py initialized with {} as plugins path"
               .format(plugin.plugins_path))


@plugin.method("install", desc=install_description,
               long_desc=install_long_description)
def install(plugin, url, main_file=None, install_dir=None):
    """
    Installs a plugin to the default plugins directory given an url.
    Could have been named 'my_little_dirty_function'.

    :param url: Where to fetch the plugin from.
    :main_file: (optional) If the resource is a directory, specifies the
                file to make executable.
    :install_dir: (optional) The name of the directory to create in c-lightning's
                default plugins directory.
    """
    # We use the command return to "log" for the user
    response = ""
    res_name = urllib.parse.urlparse(url).path.split('/')[-1]
    if not install_dir:
        install_dir = res_name.split('.')[0]
    install_path = os.path.join(plugin.plugins_path, install_dir)
    response += "Creating {} directory ..".format(install_path)
    create_dir(install_path)
    file_path = os.path.join(install_path, res_name)
    if os.path.exists(file_path):
        return "Destination {} already exists".format(file_path)
    response += "Downloading file from {} to {}\n".format(url, file_path)
    if "api.github.com" in url and len(res_name.split('.')) == 1:
        dl_folder_from_github(install_path, url)
    else:
        urllib.request.urlretrieve(url, file_path)
    if file_path.endswith(".tar.gz") or file_path.endswith("tar") \
            or file_path.endswith(".zip"):
        response += "Extracting the archive {}\n".format(res_name)
        if file_path.endswith(".tar.gz") or file_path.endswith("tar"):
            with tarfile.open(file_path, "r:*") as tar_file:
                tar_file.extractall(install_path)
            os.remove(file_path)
        elif file_path.endswith(".zip"):
            with zipfile.ZipFile(file_path, "r") as zip_file:
                zip_file.extractall(install_path)
            os.remove(file_path)
    response += "Searching for a main file in {} to make executable\n"\
                .format(res_name)
    # Trying to figure out which file to set executable
    possible_filenames = {file_path.split('/')[-1].split('.')[0], "main",
                          "plugin"}
    main_file = get_main_file(possible_filenames, install_path)
    # The above function can return None
    if main_file:
        response += "Making {} executable\n".format(main_file)
        try:
            make_executable(os.path.join(install_path, main_file))
        except:
            return "Could not set {} executable".format(main_file)
    else:
        response += "Could not find a main file, hence not making anything\
                    executable\n"
    response += "Reloading plugins from lightningd\n"
    plugin.rpc.plugin(command="reload")
    response += "Waiting for a second to check if plugin has been loaded\n"
    time.sleep(1)
    active_plugins = plugin.rpc.plugin(command="list")
    response += "Active plugins : "\
                + ", ".join(p.split('/')[-1] for p in active_plugins) + '\n'
    return response

@plugin.method("search", desc=search_description, long_desc=search_long_description)
def search(plugin, keyword):
    """
    Search for a plugin url in known plugin repositories.

    :param keyword: Which plugin to search for.
    """
    github_repos = {"lightningd/plugins", "conscott/c-lightning-plugins",
                    "renepickhardt/c-lightning-plugin-collection"}
    github_urls = search_github(github_repos, keyword)
    urls = github_urls # + another source + another source + ...
    return urls if urls else "Could not find any plugin matching this keyword"

plugin.run()
