#!python3

class Edge:

    # Defines an Edge device

    def __init__(self, edge):
        self.sys_ip = edge['deviceId']
        self.hostname = edge['host-name']
        self.model = edge['device-model']
        self.reachability = edge['reachability']
        self.validity = edge['validity']
        self.uuid = edge['uuid']
        self.version = edge['version']
        self.tables = {}
        self.interfaces = []
        self.config = ''
        self.tloc_ext_interfaces = []
        self.tloc_ext_addresses = []

    def get_tables(self, vmanage):

        # Adds the ARP table (type dict) to Edge

        for table in ['arp', 'vrrp']:
            url = f'device/{table}?deviceId={self.sys_ip}'
            self.tables[table] = vmanage.get_request(url)['data']
        for table in ['omp', 'bfd']:
            url = f'device/{table}/summary?deviceId={self.sys_ip}'
            self.tables[table] = vmanage.get_request(url)['data']
        for table in ['bgp']:
            url = f'device/{table}/neighbors?deviceId={self.sys_ip}'
            self.tables[table] = vmanage.get_request(url)['data']

    def get_wan_interfaces(self, vmanage):

        # Adds a list of WAN interfaces (type dict) to Edge

        url = f'device/control/waninterface?deviceId={self.sys_ip}'
        self.interfaces = vmanage.get_request(url)['data']

    def get_interface_stats(self, vmanage, duration='168', interval=30):

        # Adds a list of tx & rx kbbps stats to each WAN interface dict.  duration in hours, interval in minutes

        url = 'statistics/interface/aggregation'
        for interface in self.interfaces:
            query = QueryPayload.stats_if_agg(self.sys_ip, interface['interface'], duration=duration, interval=interval)
            interface['stats'] = vmanage.post_request(url, query)['data']

    def get_config(self, vmanage):

        # Adds the edge CLI configuration to self.config

        url = f'/device/config?deviceId={self.sys_ip}'
        self.config = vmanage.get_request(url)

    def get_tloc_ext_interfaces(self):

        # Find the interface names where tloc-extension is configured
        # Assumes that the interface name is in the config line immediately preceding the tloc-extension line

        config_list = self.config.split('\n')
        for num, line in enumerate(config_list):
            if 'tloc-extension' in line:
                int_list = config_list[num-1].split(' ')
                for expression in int_list.copy():
                    if 'Ethernet' in expression:
                        self.tloc_ext_interfaces.append(expression)
                        break

    def get_tloc_ip_addresses(self):

        for address in self.tables['arp']:
            try:
                if address['interface'] in self.tloc_ext_interfaces:
                    self.tloc_ext_addresses.append(address['address'])
            except KeyError:
                continue


class Site:

    # Defines a site which contains edges (type Edge)
    # Site.valid is true if site exists

    def __init__(self, vmanage, site_id):
        self.site_id = site_id
        self.edges = []
        url = f'device?site-id={self.site_id}'
        devices = vmanage.get_request(url)['data']
        if not devices:
            self.valid = False
        else:
            self.valid = True
            for device in devices:
                edge = Edge(device)
                self.edges.append(edge)


class QueryPayload:

    @staticmethod
    def stats_if_agg(system_ip, interface, duration="168", interval=30):
        data = {"query": {
          "condition": "AND",
          "rules": [
            {
              "value": [duration],
              "field": "entry_time",
              "type": "date",
              "operator": "last_n_hours"
            },
            {
              "value": [system_ip],
              "field": "vdevice_name",
              "type": "string",
              "operator": "in"
            },
            {
              "value": [interface],
              "field": "interface",
              "type": "string",
              "operator": "in"
            }
          ]
        },
          "sort": [
            {
              "field": "entry_time",
              "type": "date",
              "order": "asc"
            }
          ],
          "aggregation": {
            "field": [
              {
                "property": "interface",
                "sequence": 1
              }
            ],
            "histogram": {
              "property": "entry_time",
              "type": "minute",
              "interval": interval,
              "order": "asc"
              },
            "metrics": [
              {
                "property": "rx_kbps",
                "type": "avg"
              },
              {
                "property": "tx_kbps",
                "type": "avg"
              }
            ]
          }
        }
        return data
