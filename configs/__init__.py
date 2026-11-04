import importlib

def get_config(dataset):
    return importlib.import_module(f"configs.{dataset}")


def method_config(dataset, method):
    return dict(getattr(get_config(dataset), method.upper()))
