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
from lightning import Plugin
from search import search_github
from utils import (
    create_dir, get_main_file, dl_folder_from_github, make_executable,
    dl_github_repo, handle_requirements, handle_compilation, plug_debug
)


plugin = Plugin()


@plugin.init()
def init(plugin, options, configuration):
    plugin.plugins_path = os.path.join(plugin.lightning_dir, "plugins")
    if "plugins-path" in configuration:
        plugin.plugins_path = configuration["plugins-path"]
    plugin.log("Plugin reckless.py initialized with {} as plugins path"
               .format(plugin.plugins_path))


@plugin.method("install_plugin", desc=install_description,
               long_desc=install_long_description)
def install(plugin, url, install_auto=None, main_file=None, install_dir=None):
    """
    Installs a plugin to the default plugins directory given an url.
    Could have been named 'my_little_dirty_function'.

    :param url: Where to fetch the plugin from.
    :main_file: (optional) If the resource is a directory, specifies the
                file to make executable.
    :install_dir: (optional) The name of the directory to create in c-lightning's
                default plugins directory.
    """
    # We dont support pre-v0.7.2.1 anyway
    reply = {"response": "", "format-hint": "simple"}
    reply["response"] += "                                "
    reply["response"] += "===== Installation log ======\n\n"
    # Check that we have been given a supported url
    if url.split("://")[0] not in {"http", "https"}:
        reply["response"] += "You did not pass a valid url,"\
                             " treating as a keyword\n"
        search_result = search(plugin, url)
        if search_result:
            if install_auto:
                if len(search_result) > 1:
                    reply["response"] += "I cannot install the plugin"\
                                         " automatically since I found"\
                                         " two of them. Continuing.\n\n"
                else:
                    return install(plugin, search_result[0]["url_download"])
            reply["response"] += "You can install {} by running : ".format(url)
            reply["response"] += "`lightning-cli install_plugin {}`\n"\
                                 .format(search_result[0]["url_download"])
            if len(search_result) > 1:
                reply["response"] += "You can also install it via :"
                reply["response"] += ", ".join(r["url_download"]
                                               for r in search_result[1:])
        else:
            reply["response"] += "No known plugin was found matching {}"\
                                 .format(url)
        return reply
    res_name = urllib.parse.urlparse(url).path.split('/')[-1]
    if not install_dir:
        install_dir = res_name.split('.')[0]
    install_path = os.path.join(plugin.plugins_path, install_dir)
    create_dir(install_path)
    reply["response"] += "Created {} directory\n".format(install_path)
    file_path = os.path.join(install_path, res_name)
    if os.path.exists(file_path):
        return "Destination {} already exists\n".format(file_path)
    # A special case to handle repositories with many plugins as folders
    if "api.github.com" in url and len(res_name.split('.')) == 1:
        dl_folder_from_github(install_path, url)
    elif "github.com" in url:
        # A Github url, but not the api. Must be a repo.
        dl_github_repo(install_path, url)
    else:
        urllib.request.urlretrieve(url, file_path)
    # Separated because url and path can be long
    reply["response"] += "Downloaded file from {}".format(url)
    reply["response"] += " to {}\n".format(file_path)

    # If the file has been urlretrieved, it's either an archive or a single
    # file
    if file_path.endswith(".tar.gz") or file_path.endswith("tar") \
            or file_path.endswith(".zip"):
        reply["response"] += "Extracting the archive {}\n".format(res_name)
        if file_path.endswith(".tar.gz") or file_path.endswith("tar"):
            with tarfile.open(file_path, "r:*") as tar_file:
                tar_file.extractall(install_path)
            os.remove(file_path)
        elif file_path.endswith(".zip"):
            with zipfile.ZipFile(file_path, "r") as zip_file:
                zip_file.extractall(install_path)
            os.remove(file_path)
    # The common case where the plugin is in Python and has dependencies
    handle_requirements(install_path)
    # The case where the plugin is not written in a scripting language
    handle_compilation(install_path)

    # Trying to figure out which file to set executable, otherwise we would not
    # be able to load the plugin
    possible_filenames = {file_path.split('/')[-1].split('.')[0], "main",
                          "plugin"}
    main_file = get_main_file(possible_filenames, install_path)
    # We might not have found the main_file...
    if main_file:
        reply["response"] += "Making {} executable\n".format(main_file)
        make_executable(main_file)
    else:
        reply["response"] += "Could not find a main file, hence not making"\
                             " anything executable\n"
        return reply
    reply["response"] += "\n"

    active_plugins = plugin.rpc.plugin_start(os.path.abspath(main_file))
    if main_file in [p["name"] for p in active_plugins["plugins"]]:
        reply["response"] += "Started {}".format(main_file.split('/')[-1])
    else:
        reply["response"] += "Timeout while trying to start {}.".format(main_file)
    return reply


@plugin.method("search_plugin", desc=search_description,
               long_desc=search_long_description)
def search(plugin, keyword):
    """
    Search for a plugin url in known plugin repositories.

    :param keyword: Which plugin to search for.
    """
    github_repos = {"lightningd/plugins", "conscott/c-lightning-plugins",
                    "renepickhardt/c-lightning-plugin-collection"}
    github_urls = search_github(github_repos, keyword)
    # Hopefully more sources to come !
    urls = github_urls
    return urls if urls else "Could not find any plugin matching this keyword"


plugin.run()
