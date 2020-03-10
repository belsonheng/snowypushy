import yaml

class Configuration(object):
    def __init__(self, file):
        self._config = yaml.load(open(file), Loader=yaml.FullLoader)

    def get(self, property_name):
        if property_name not in self._config.keys():
            return None
        # set default values if none
        if not self._config[property_name]:
            pass
        return self._config[property_name]
