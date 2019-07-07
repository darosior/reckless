"""
This file contains commands description (short and detailed)
"""

install_description = "Install and load a plugin given an url"
install_long_description = \
        """
        This command will, if provided an url, fetch the resource and add it in
        the default plugins directory. It will then try to find the main file
        and load it as a plugin.\n
        This command will, if provided a keyword, scrap known C-lightning
        plugins repositories and return url of matching ones. It __will not__
        install it by default.\n
        \n
        The `main_file` optional parameter can be passed to help BUG to find
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
        - 'url_download': The url to provide to the `install` command to
          install the actual plugin\n
        """
