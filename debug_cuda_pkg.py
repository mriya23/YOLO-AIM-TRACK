
import pkgutil
import cuda
print(f"cuda path: {cuda.__path__}")
for importer, modname, ispkg in pkgutil.iter_modules(cuda.__path__):
    print(f"Found submodule: {modname}")
