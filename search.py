"""
This file contains the search functions for the search command.
It only contains a Github-scraping function for now, but other are welcome too.
"""
import json
import urllib.request


def search_github(repos, keyword):
    """
    Scraps Github for plugin urls.

    :param repos: A list of repos to search in.
    :param keyword: Get a file url if it contains this.
    :return: A list of dictionnaries containing an url and a download url.
    """
    urls = []
    for repo in repos:
        api_url = "https://api.github.com/repos/{}/git/trees/master"\
                  .format(repo)
        json_string = urllib.request.urlopen(api_url).read().decode("utf-8")
        content_list = json.loads(json_string)["tree"]
        for f in content_list:
            if keyword in f["path"]:
                if f["mode"] == "160000":
                    # This a submodule
                    json_string = urllib.request.urlopen(
                        "https://api.github.com/repos/{}/contents"
                        .format(repo) + f["path"]).read().decode("utf-8")
                    submodule_url = json.loads(json_string)["submodule_git_url"]
                    url = {"url_human": submodule_url}
                else:
                    url = {"url_human": "https://github.com/{}/tree/master/{}"
                                        .format(repo, f["path"])}
                # If this is a 'regular' file
                if "size" in f:
                    url["url_download"] = "https://raw.github.com/{}/master/{}"\
                                          .format(repo, f["path"])
                # If this is a folder
                else:
                    url["url_download"] = "https://api.github.com/repos/{}/contents/{}"\
                                          .format(repo, f["path"])
                urls.append(url)
    return urls
