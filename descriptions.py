"""
This file contains commands description (short and detailed)
"""

install_description = "Install and load a plugin given an url"
install_long_description = \
        """
        This command will, if provided an url, fetch the resource and add it in
        the default plugins directory. It will then try to find the main file
        and load it as a plugin.\n
        In addition to (optionally archive) files, the command can be passed a
        Github repo. If you want to download a specific folder from a Github
        repo, please use the 'search_plugin' command with the folder name.\n
        This command will, if provided a keyword, scrap known C-lightning
        plugins repositories and return url of matching ones. It __will not__
        install it by default.\n
        \n
        The `install_auto` optional parameter, if set and if a keyword is
        passed instead of an url, will make me install the plugin returned by
        the search __if the search returns only one result__ : I can not
        choose between plugins, maybe you should buy me an AI ?..
        The `main_file` optional parameter can be passed to help me to find
        the plugin's directory main file.\n
        The `install_dir` optional parameter can be passed to change the name
        of created directory in the default plugins directory.\n
        """

search_description = "Search a plugin from known plugin sources"
search_long_description = \
        """
        This command will, given a keyword, search in multiple well-known
        C-lightning plugins repositories for a plugin whose __title__ match the
        keyword.\n
        It will return a json object for each match, containing 2 entries:\n
        - 'url_human': An url pointing to a webpage so that you can
          double-check what you are installing.\n
        - 'url_download': The url to provide to the `install_plugin` command to
          install the actual plugin\n
        """
