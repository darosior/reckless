import os
from pyln.testing.fixtures import *  # noqa: F401,F403

plugin_path = os.path.join(os.path.dirname(__file__), "reckless.py")


def test_helpme_starts(node_factory):
    l1 = node_factory.get_node()
    # Test dynamically
    l1.rpc.plugin_start(plugin_path)
    l1.rpc.plugin_stop(plugin_path)
    l1.rpc.plugin_start(plugin_path)
    l1.stop()
    # Then statically
    l1.daemon.opts["plugin"] = plugin_path
    l1.start()


def test_install_basic(node_factory):
    l1 = node_factory.get_node()
    l1.rpc.plugin_start(plugin_path)
    urls = l1.rpc.call("search_plugin", {"keyword": "drain"})[0]
    # We got 2 results here, since there is Rene's one too !
    l1.rpc.call("install_plugin", {"url": urls["url_download"]})
    print(l1.rpc.plugin_list())
    l1.rpc.check("drain")


def test_install_from_keyword(node_factory):
    l1 = node_factory.get_node(options={"plugin": plugin_path})
    l1.rpc.call("install_plugin", {"url": "summary", "install_auto": True})
    l1.rpc.call("summary", {})


def test_install_submodule(node_factory):
    l1 = node_factory.get_node(options={"plugin": plugin_path})
    urls = l1.rpc.call("search_plugin", {"keyword": "lightning-qt"})[0]
    l1.rpc.call("install_plugin", {"url": urls["url_download"]})
    l1.rpc.check("gui")


def test_install_repo(node_factory):
    l1 = node_factory.get_node(options={"plugin": plugin_path})
    repo_url = "https://github.com/darosior/lightning-qt"
    l1.rpc.call("install_plugin", {"url": repo_url})
    l1.rpc.check("gui")


def test_install_everyone(node_factory):
    l1 = node_factory.get_node()
    l1.rpc.plugin_start(plugin_path)
    # autopilot, autoreload are static
    # FIXME: intall Go and add graphql, sitzprobe
    l1.rpc.call("install_plugin", {"url": "monitor", "install_auto": True})
    l1.rpc.call("install_plugin", {"url": "persistent-channels",
                                   "install_auto": True})
    l1.rpc.call("install_plugin", {"url": "summary", "install_auto": True})
    probe_url = "https://api.github.com/repos/lightningd/plugins/contents/probe"
    l1.rpc.call("install_plugin", {"url": probe_url})
    rebalance_url = "https://api.github.com/repos/lightningd/plugins/contents/rebalance"
    l1.rpc.call("install_plugin", {"url": rebalance_url})
    l1.rpc.call("install_plugin", {"url": "sendinvoiceless",
                                   "install_auto": True})
    l1.rpc.call("install_plugin", {"url": "zmq", "install_auto": True})
