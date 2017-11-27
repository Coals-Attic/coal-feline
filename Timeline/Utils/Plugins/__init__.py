from Timeline.Utils.Plugins.IPlugin import IPlugin, RequirementsManager
from Timeline.Utils.Plugins.AbstractManager import Abstraction
from Timeline.Utils.Plugins.IPlugin import IPluginAbstractMeta
from pkgutil import iter_modules
from importlib import import_module

PermissionError = type('PermissionError', (Exception,), {})
PLUGINS_LOADED = list()
PLUGIN_ABSTRACT_OBJECTS = list()

def extend(base, plugin):
    if not hasattr(base, 'extend'):
        raise NotImplementedError("Unable to extend object - {}".format(base))

    if not base.extend:
        raise PermissionError("Extend feature disabled for  - {}".format(base))

    if not issubclass(plugin, IPlugin):
        raise TypeError("Extend allowed only for IPlugin children")

    if not issubclass(base, object):
        raise TypeError("Can extend only new-styled classes deriving objects")

    bases = tuple(base.__bases__)
    if not plugin in bases:
        bases = (plugin,) + bases

    base.__bases__ = bases

def loadPlugins(module):
    path = module.__path__
    name = module.__name__

    for im, mname, ispkg in iter_modules(path):
        scope = "{}.{}".format(name, mname)
        m = import_module(scope, path)

        if ispkg:
            loadPlugins(m)

        PLUGINS_LOADED.append(m)

def getPlugins():
    '''
    Returns all object which inherits IPlugin.
    Make sure to either import the module or class, or use loadModule() before using this, to get all available plugins
    '''
    return IPlugin.__subclasses__()

def satisfyPluginDependency(plugin):
    if isinstance(plugin, list):
        for k in plugin:
            satisfyPluginDependency(k)
        return
    p = RequirementsManager.getRequirement(plugin)
    if p is None:
        # try loading plugin
        _plugin = RequirementsManager.getRequirement(plugin, [(k.code, k) for k in getPlugins()])
        if _plugin is None:
            return # plugin doesn't exists!

        satisfyPluginDependency(_plugin)
        _plugin()

def loadPluginObjects():
    plugins = getPlugins()

    for plugin in plugins:
        if type(plugin) is IPluginAbstractMeta:
            continue

        satisfyPluginDependency(plugin.requirements)

        exists = sum(k.name == plugin.name and k.developer == plugin.developer and (k.version == plugin.version or k.version == 0 or plugin.version == 0) for k in Abstraction.getAllPlugins()) > 0
        if not exists:
            plugin()