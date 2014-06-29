import os
import sys
import importlib
import traceback

from datatypes import Path

from .exceptions import BadPlugin


class Plugin:
    """Phpsploit plugin class

    This object instanciates a new plugin object.

    Example:
    >>> plugin = Plugin("./plugins/file_system/ls")
    >>> plugin.name
    'ls'
    >>> plugin.category
    'File system'
    >>> plugin.run(['ls', '-la'])  # run the plugin with args

    """

    def __init__(self, path):
        if path.endswith(os.sep) or path.endswith("/"):
            path = path[:-1]
        self.path = path
        self.name = os.path.basename(path)

        try:
            Path(path, mode='drx')()
        except ValueError as e:
            print("[#] Couldn't load plugin: «%s»" % self.path)
            print("[#]     Plugin directory error: %s" % e)
            raise BadPlugin

        category = os.path.basename(os.path.dirname(path))
        self.category = category.replace("_", " ").capitalize()

        self.help = ""
        try:
            script = Path(self.path, "plugin.py", mode='fr').read()
        except ValueError as e:
            print("[#] Couldn't load plugin: «%s»" % self.path)
            print("[#]     File error on plugin.py: %s" % e)
            print("[#] ")
            raise BadPlugin
        if not script.strip():
            print("[#] Couldn't load plugin: «%s»" % self.path)
            print("[#]     File plugin.py is empty")
            print("[#] ")
            raise BadPlugin
        try:
            code = compile(script, "", "exec")
        except BaseException as e:
            e = traceback.format_exception(type(e), e, e.__traceback__)
            print("[#] Couldn't compile plugin: «%s»" % self.path)
            print("[#] " + "\n[#] ".join("".join(e).splitlines()))
            print("[#] ")
            raise BadPlugin
        if "__doc__" in code.co_names:
            self.help = code.co_consts[0]

    def run(self, argv):

        try:
            ExecPlugin(self)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except SystemExit:
            evalue = str(sys.exc_info()[1])
            if evalue:
                print(evalue)
        except BaseException as err:
            print("[-] An error occured while launching the plugin:")
            raise err


class ExecPlugin:

    filename = "plugin"
    _instance_id = 0

    def __init__(self, plugin):
        script_path = os.path.join(plugin.path, self.filename + ".py")
        sys.path.insert(0, plugin.path)
        try:
            self.exec_module(script_path)
        finally:
            sys.path.pop(0)

    @classmethod
    def is_first_instance(cls):
        if cls._instance_id == 0:
            result = True
        else:
            result = False
        cls._instance_id += 1
        return result

    def exec_module(self, path):
        loader = importlib.machinery.SourceFileLoader(self.filename, path)
        module = importlib.import_module(self.filename)

        # If the instance is the first one, it means that
        # the import already executed the plugin.
        if not self.is_first_instance():
            loader.exec_module(module)
