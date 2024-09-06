from ape import plugins
from .provider import QuickNode
from .constants import QUICKNODE_NETWORKS

@plugins.register(plugins.ProviderPlugin)
def providers():
    for ecosystem_name in QUICKNODE_NETWORKS:
        for network_name in QUICKNODE_NETWORKS[ecosystem_name]:
            yield ecosystem_name, network_name, QuickNode