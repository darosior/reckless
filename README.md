# Reckless
A plugin manager for C-lightning

## Installation - requirements
As any other plugin, `reckless` can be installed by being put in `lightningd`'s default plugin directory (`~/.lightning/bitcoin/plugins` by default) or at startup via command line:
```bash
lightningd --plugin /path/to/reckless.py
```
It also supports to be started dynamically:
```bash
lightning-cli plugin start /path/to/reckless.py
```
C-lightning v0.7.2 or superior is required.

## Usage
You can search for a plugin from known plugin repos:
```bash
lightning-cli search_plugin rebalance
```
This will return a list of objects with 2 entries: 'human_url' which points to
the plugin location in a human readable format, and `install_url` to be passed
to `lightning_install` to install the actual plugin. For example the
'rebalance' keyword from above points to both @gallizoltan's rebalance plugin and
@renepickhardt's rebalance-JIT-routing (WIP).

You can install a plugin by providing an url, or a keyword and setting the optional second
parameter to `true`, for example:
```bash
$ lightning-cli install_plugin lightning-qt true
```
This will output a somewhat exhaustive log of what happened (in case installation goes wrong,
or so that you know what this plugin does with your money-related software):
```bash
                                ===== Installation log ======

Created /home/darosior/projects/reckless/regtest/lndir1/regtest/plugins/lightning-qt directory
Downloaded file from https://api.github.com/repos/lightningd/plugins/contents/lightning-qt to /home/darosior/projects/reckless/regtest/lndir1/regtest/plugins/lightning-qt/lightning-qt
Made /home/darosior/projects/reckless/regtest/lndir1/regtest/plugins/lightning-qt/lightning-qt.py executable

Started lightning-qt.py
```

## A note on managers
Package managers have led to severe flaws in the past, and especially in Bitcoin space.
C-lightning plugins are direclty connected to `lightningd` and manage funds, please be sure of what you are installing.
That's why the installation is in two stades (`search` then `install`). That's why there is a `human_url` entry in the search results.
That's also why this plugin is named `reckless` :-)..

## Licence
BSD 3-clause-clear
