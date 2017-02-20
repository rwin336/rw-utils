#!/usr/bin/python
###########################################################
#
import os
from neutronclient.v2_0 import client

def print_values(val, type):
    if type == 'ports':
        val_list = val['ports']
    if type == 'networks':
        val_list = val['networks']
    if type == 'routers':
        val_list = val['routers']
    for p in val_list:
        for k, v in p.items():
            print("%s : %s" % (k, v))
        print('\n')

def get_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d


print("- Rally devstack cleanup - start")
print("- Aqquiring credentials")
credentials = get_credentials()
print("- Creds aqquired")
print("- Creating Neutron network client")
neutron = client.Client(**credentials)
print("- Neutron network client created")

print("- Getting list of networks")
netw = neutron.list_networks()
print("- Network list aqquired")
print("- Getting list of Routers")
rtrw = neutron.list_routers()
print("- Router list aqquired")

rtr_name_prefix = "rally_net"
backup_postfix = "HA_backup_1"
print("- Processing router list")
for rtr in rtrw['routers']:
    if rtr_name_prefix in rtr['name'] and backup_postfix not in rtr['name']:
        print("-- Deleting Router: {0}".format(rtr['name']))
        neutron.remove_gateway_router(rtr['id'])
        rtr_interfaces = neutron.list_ports(device_id=rtr['id'])
        for port_detail in rtr_interfaces['ports']:
            print("--- Removing port {0} from router".format(port_detail['id']))
            port = { 'port_id': port_detail['id'] }
            neutron.remove_interface_router(rtr['id'], body=port)
        neutron.delete_router(rtr['id'])
        print("-- Router delete complete")
print("- Router list processed")

print("- Processsing network list")
net_name_prefix = "rally_net"
print("- Checking networks to be deleted")
for net in netw['networks']:
    if net_name_prefix in net['name']:
        print("-- Deleting Network: {0}".format(net['name']))
        ports = neutron.list_ports(network_id=net['id'])
        for port in ports['ports']:
            print("--- Deleting port {0}".format(port['id']))
            neutron.delete_port(port['id'])
        dhcp_agents = neutron.list_dhcp_agent_hosting_networks(net['id'])
        for agent in dhcp_agents['agents']:
            print("--- Deleting DHCP Agent {0}".format(agent['id']))
            neutron.delete_agent(agent=agent['id'])
        neutron.delete_network(net['id'])
        print("-- Network delet complete")
print("- Network list processed")
print("- Rally devstack cleanup - complete")
