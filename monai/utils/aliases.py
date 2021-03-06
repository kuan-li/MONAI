# Copyright 2020 MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading
import sys
import inspect
import importlib


alias_lock = threading.RLock()
GlobalAliases = {}


def alias(*names):
    """
    Stores the decorated function or class in the global aliases table under the given names.
    """

    def _outer(obj):
        for n in names:
            with alias_lock:
                GlobalAliases[n] = obj

        return obj

    return _outer


def resolve_name(name):
    """
    Search for the declaration (function or class) with the given name. This will first search the list of aliases to
    see if it was declared with this aliased name, then search treating `name` as a fully qualified name, then search
    the loaded modules for one having a declaration with the given name. If no declaration is found, raise ValueError.
    """
    # attempt to resolve an alias
    with alias_lock:
        obj = GlobalAliases.get(name, None)

    assert name not in GlobalAliases or obj is not None

    # attempt to resolve a qualified name
    if obj is None and "." in name:
        modname, declname = name.rsplit(".", 1)

        try:
            mod = importlib.import_module(modname)
            obj = getattr(mod, declname, None)
        except ModuleNotFoundError:
            raise ValueError("Module %r not found" % modname)

        if obj is None:
            raise ValueError("Module %r does not have member %r" % (modname, declname))

    # attempt to resolve a simple name
    if obj is None:
        # Get all modules having the declaration/import, need to check here that getattr returns something which doesn't
        # equate to False since in places __getattr__ returns 0 incorrectly:
        # https://github.com/tensorflow/tensorboard/blob/a22566561d2b4fea408755a951ac9eaf3a156f8e/tensorboard/compat/tensorflow_stub/pywrap_tensorflow.py#L35  # noqa: B950
        mods = [m for m in list(sys.modules.values()) if getattr(m, name, None)]

        if len(mods) > 0:  # found modules with this declaration or import
            if len(mods) > 1:  # found multiple modules, need to determine if ambiguous or just multiple imports
                foundmods = {inspect.getmodule(getattr(m, name)) for m in mods}  # resolve imports
                foundmods = {m for m in foundmods if m is not None}

                if len(foundmods) > 1:  # found multiple declarations with the same name
                    modnames = [m.__name__ for m in foundmods]
                    msg = "Multiple modules (%r) with declaration name %r found, resolution is ambiguous" % (modnames, name)
                    raise ValueError(msg)
                else:
                    mods = list(foundmods)

            obj = getattr(mods[0], name)

        if obj is None:
            raise ValueError("No module with member %r found" % name)

    return obj
