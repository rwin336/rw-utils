#!/usr/bin/python
###############################################################################
# Copyright 2017 R.A. Winters <rwin336@gmail.com>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
###############################################################################

# Devstack Rall Cleanup.
#
# The Openstack Rally tester can sometimes crash when testing a large
# scaling profile leaving the stack dirty with both routers and networks.
#
# This script will clean up the routers and networks created by the Rally
# test run.  The script was targetted to run against a Devstack deployed
# stack that has been configured with the Cisco ASR as the stack router.
#
# Steps to run:
#  1. Source the openrc for the targetted stack
#  2. Run the script.
#
#
import os
import time
from neutronclient.v2_0 import client
from novaclient.client import Client

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

def get_nova_credentials_v2():
    d = {}
    d['version'] = '2'
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    return d

def get_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d


print("- Rally devstack cleanup - start")
print("- Aquiring credentials")
credentials = get_credentials()
print("- Creds aquired")
print("- Creating Neutron network client")
neutron = client.Client(**credentials)
print("- Neutron network client created")
print("- Creating Nova client")
nova_creds = get_nova_credentials_v2()
nova = Client(**nova_creds)
print("- Nova client created")

print("- Getting list of servers")
serverw = nova.servers.list(search_opts={'all_tenants': 1})
print("- Server list aquired")
print("- Getting list of networks")
netw = neutron.list_networks()
print("- Network list aquired")
print("- Getting list of Routers")
rtrw = neutron.list_routers()
print("- Router list aquired")

print("- Processing server list: {0}".format(len(serverw)))
for server in serverw:
    print("-- Deleting server {0}".format(server.name))
    nova.servers.delete(server)
    print("-- Server deleted")
    time.sleep(2)

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
