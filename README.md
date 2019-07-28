# Bug
A plugin manager for C-lightning  
  
## Installation - requirements
As any other plugin, `bug` can be installed by being put in `lightningd`'s default plugin directory or at startup via command line:
```bash
lightningd --plugin /path/to/bug.py
```
C-lightning v0.7.2 or master branch is required.  

## Usage
You can search for a plugin from known plugin repos:
```bash
lightning-cli search_plugin rebalance
```
This will return a list of objects with 2 entries: 'human_url' which points to the plugin location in a human readable format, and `install_url` to be passed to `lightning_install` to install the actual plugin. For example the 'rebalance' keyword from above points to @gallizoltan's rebalance plugin @renepickhardt's rebalance-JIT-routing (WIP).  
  
You can install a plugin by providing an url:
```bash
lightning-cli install_plugin https://api.github.com/repos/lightningd/plugins/contents/rebalance
```
This will output a somewhat exhaustive log of what happened (in case installation goes wrong, or so that you know what this plugin does with your money-related software):
```bash
[
   "===== Installation result ======",
   "",
   "Created /home/darosior/test-dir/plugins/rebalance directory",
   "Downloaded file from https://api.github.com/repos/lightningd/plugins/contents/rebalance ..",
   ".. to /home/darosior/test-dir/plugins/rebalance/rebalance",
   "Making /home/darosior/test-dir/plugins/rebalance/rebalance.py executable",
   "Reloaded plugins from lightningd",
   "Waiting for a second to check if the brand new pluginhas been loaded",
   "Active plugins : pay, autoclean, bug.py, rebalance.py"
]
```
*(lightning-cli escapes the `\n`s so I used a list)*  
  
There is a little trick with installing plugins with `bug`. As you may know, they have to be executable to be usable: for now `bug` (inefficiently) tries to guess which file to make executable. It can lead to strange behaviors if it's wrong.  
  
## A note on managers
Package managers have led to severe flaws in the past, and especially in Bitcoin space. C-lightning plugins are direclty connected to `lightningd` and manage funds, please be sure of what you are installing. That's why the installation is in two stades (`search` then `install`(only url)). That's why there is a `human_url` entry in the search results.  
That's also why this plugin is named `bug` :-).  
  
## Licence
BSD 3-clause-clear
