#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Athor:       grodi, chgrodde@googlemail.com
# Version:     0.4
# Description:
# This script prints QoS queueing information in an
# easy to read list format on NX-OS platforms.
#
# To use:
#      1. Copy script to N9K switch bootflash:scripts/
#      2. Execute using:
# source queue.py
#   or
# source queue.py <arg>
#   where arg 1 is in a range of 1 to 60 seconds.
#
#      3. Configure an alias, e.g.
# cli alias name qput source n9k_qput.py
#
# This script was tested on N9K using I5(1) release.
#

from __future__ import division

import sys
import json
import xml.etree.cElementTree as ET
import re
import time
#import math
from cli import *

# time between two measurements
delta_time = 30


def getqosstats(l_queue_stat_dict, l_run):
    # create a dictionary for interface/qos statistics
    l_queue_stat_dict[l_run] = {}
    # quantity of queues
    l_q_qty = 0
    # Load interface states and descriptions
    if_tree = ET.ElementTree(ET.fromstring(cli('show interface status | xml | exclude "]]>]]>"')))

    if_data = if_tree.getroot()
    if_manager = '{http://www.cisco.com/nxos:1.0:if_manager}'

    for i in if_data.iter(if_manager + 'ROW_interface'):
        try:
            l_int = i.find(if_manager + 'interface').text
            if re.match('^Ethernet.*', l_int):
                l_state = i.find(if_manager + 'state').text
                l_state = l_state.replace("connected", "1")
                l_state = l_state.replace("xcvrAbsent", "0")
                l_state = l_state.replace("noOperMembers", "0")
                # print l_state
                # only interfaces in up state are printed
                if l_state == '1':
                    # reset queue counter
                    l_q_qty = 0

                    ifqueue = json.loads(clid("show queuing interface %s" % l_int))['TABLE_module']['ROW_module'][
                        'TABLE_queuing_interface']['ROW_queuing_interface']

                    # qos_interface = ifqueue[0]['if_name_str']
                    egress_stats = ifqueue[0]['TABLE_qosgrp_egress_stats']['ROW_qosgrp_egress_stats']
                    # print l_int

                    l_queue_stat_dict[l_run][l_int] = {}
                    l_queue_stat_dict[l_run][l_int]['state'] = l_state

                    # print l_queue_stat_dict

                    for egress_gosgrp_entry in egress_stats:

                        eq_qosgrp = egress_gosgrp_entry['eq-qosgrp']
                        # print eq_qosgrp
                        if eq_qosgrp not in l_queue_stat_dict:
                            l_queue_stat_dict[l_run][l_int][eq_qosgrp] = {}

                        row_qosgrp_estats_entry = egress_gosgrp_entry['TABLE_qosgrp_egress_stats_entry'] \
                            ['ROW_qosgrp_egress_stats_entry']

                        # packet and byte stats available
                        # print eq_qosgrp

                        # standard qos group
                        if re.match('^[0-7]$', eq_qosgrp):
                            # sometimes only packet stats available
                            if len(row_qosgrp_estats_entry) == 2:
                                # print "Qgroup: " + eq_qosgrp
                                # tput stats
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units'] = \
                                    row_qosgrp_estats_entry[0]['eq-stat-units']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value'] = \
                                    row_qosgrp_estats_entry[0]['eq-uc-stat-value']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = '---'
                                # drop stats
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units_drop'] = \
                                    row_qosgrp_estats_entry[1]['eq-stat-units']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value_drop'] = \
                                    row_qosgrp_estats_entry[1]['eq-uc-stat-value']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = '---'
                                l_q_qty += 1

                            elif len(row_qosgrp_estats_entry) == 5 or len(row_qosgrp_estats_entry) == 6:
                                # tput stats in Bytes
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units'] = \
                                    row_qosgrp_estats_entry[1]['eq-stat-units']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value'] = \
                                    row_qosgrp_estats_entry[1]['eq-uc-stat-value']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = \
                                    row_qosgrp_estats_entry[1]['eq-mc-stat-value']

                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units_drop'] = \
                                    row_qosgrp_estats_entry[3]['eq-stat-units']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value_drop'] = \
                                    row_qosgrp_estats_entry[3]['eq-uc-stat-value']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = \
                                    row_qosgrp_estats_entry[3]['eq-mc-stat-value']
                                l_q_qty += 1

                            else:
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units_drop'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value_drop'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = '---'

                        # control plane qos group
                        if re.match('^CONTROL.*', eq_qosgrp):
                            if len(row_qosgrp_estats_entry) == 2:
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units'] = \
                                    row_qosgrp_estats_entry[0]['eq-stat-units']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value'] = \
                                    row_qosgrp_estats_entry[0]['eq-uc-stat-value']
                                if row_qosgrp_estats_entry[0].get('eq-mc-stat-value'):
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = \
                                        row_qosgrp_estats_entry[0]['eq-mc-stat-value']
                                else:
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = '---'

                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units_drop'] = \
                                    row_qosgrp_estats_entry[1]['eq-stat-units']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value_drop'] = \
                                    row_qosgrp_estats_entry[1]['eq-uc-stat-value']
                                if row_qosgrp_estats_entry[1].get('eq-mc-stat-value'):
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = \
                                        row_qosgrp_estats_entry[1]['eq-mc-stat-value']
                                else:
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = '---'

                            elif len(row_qosgrp_estats_entry) == 4 or len(row_qosgrp_estats_entry) == 5:
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units'] = \
                                    row_qosgrp_estats_entry[1]['eq-stat-units']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value'] = \
                                    row_qosgrp_estats_entry[1]['eq-uc-stat-value']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = \
                                    row_qosgrp_estats_entry[1]['eq-mc-stat-value']

                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units_drop'] = \
                                    row_qosgrp_estats_entry[3]['eq-stat-units']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value_drop'] = \
                                    row_qosgrp_estats_entry[3]['eq-uc-stat-value']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = \
                                    row_qosgrp_estats_entry[3]['eq-mc-stat-value']

                            else:
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value_drop'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = '---'

                            l_q_qty += 1

                        # span gos group
                        if re.match('^SPAN.*', eq_qosgrp):
                            if len(row_qosgrp_estats_entry) == 2:
                                if row_qosgrp_estats_entry[1]['eq-stat-type'] == 'Dropped':
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units_drop'] = \
                                        row_qosgrp_estats_entry[1]['eq-stat-units']
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value_drop'] = \
                                        row_qosgrp_estats_entry[1]['eq-uc-stat-value']
                                    if row_qosgrp_estats_entry[1].get('eq-mc-stat-value'):
                                        l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = \
                                            row_qosgrp_estats_entry[1]['eq-mc-stat-value']
                                    else:
                                        l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = '---'

                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units'] = \
                                        row_qosgrp_estats_entry[0]['eq-stat-units']
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value'] = \
                                        row_qosgrp_estats_entry[0]['eq-uc-stat-value']
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = '---'


                                elif row_qosgrp_estats_entry[1]['eq-stat-type'] == 'Tx':
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units'] = \
                                        row_qosgrp_estats_entry[1]['eq-stat-units']
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value'] = \
                                        row_qosgrp_estats_entry[1]['eq-uc-stat-value']
                                    if row_qosgrp_estats_entry[1].get('eq-mc-stat-value'):
                                        l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = \
                                            row_qosgrp_estats_entry[1]['eq-mc-stat-value']
                                    else:
                                        l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = '---'
                                    # in this case we have no drop statistics
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units_drop'] = '---'
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value_drop'] = '---'
                                    l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = '---'

                            elif len(row_qosgrp_estats_entry) == 5:
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units'] = \
                                    row_qosgrp_estats_entry[1]['eq-stat-units']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value'] = \
                                    row_qosgrp_estats_entry[1]['eq-uc-stat-value']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = \
                                    row_qosgrp_estats_entry[1]['eq-mc-stat-value']

                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units_drop'] = \
                                    row_qosgrp_estats_entry[3]['eq-stat-units']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value_drop'] = \
                                    row_qosgrp_estats_entry[3]['eq-uc-stat-value']
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = \
                                    row_qosgrp_estats_entry[3]['eq-mc-stat-value']

                            else:
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_stat_units_drop'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_uc_stat_value_drop'] = '---'
                                l_queue_stat_dict[l_run][l_int][eq_qosgrp]['eq_mc_stat_value_drop'] = '---'

                            l_q_qty += 1

        except AttributeError:
            pass
    return l_q_qty, l_queue_stat_dict


### Main Program ###

# check wheter absolut or q-rate should be determined
# in case of q-rate counter take 1st argument as seconds.
# max q-rate time is 60 seconds
rate_flag = False
if len(sys.argv) == 2:
    arg_1 = (sys.argv[1])
    if re.match(r'^\d{1,2}$', arg_1):
        if int(arg_1) <= 60:
            rate_flag = True
            delta_time = arg_1
else:
    rate_flag = False


# Collect data
queue_stat_dict = {}


# get absolut counter
if not rate_flag:
    print "Getting Queueing Stats..."
    print
    run = 1
    # get counter
    q_qty, queue_stat_dict = getqosstats(queue_stat_dict, run)
    # print "Q: " + str(q_qty)

    # 4 + 2 egress queues
    if q_qty == 6:
        table = "{0:19}{1:14}{2:14}{3:14}{4:14}{5:14}{6:14}"
        print '-------------------------------------------------------------------------------------------------------'
        print table.format("Interface", "0/Bytes", "1/Bytes", "2/Bytes", "3/Bytes", "CONTR", "SPAN")
        print '-------------------------------------------------------------------------------------------------------'
    # 8 + 2 egress queues
    elif q_qty == 10:
        table = "{0:19}{1:14}{2:14}{3:14}{4:14}{5:14}{6:14}{7:14}{8:14}{9:14}{10:14}"
        print '---------------------------------------------------------------------------------------------------------------------------------------------------------'
        print table.format("Interface", "0/Bytes", "1/Bytes", "2/Bytes", "3/Bytes", "4/Bytes", "5/Bytes", "6/Bytes",
                           "7/Bytes", "CONTR", "SPAN")
        print '---------------------------------------------------------------------------------------------------------------------------------------------------------'
    else:
        print 'Housten we got a problem....'
        sys.exit(1)

# get counter to calc throughput per seconds
elif rate_flag:
    run = 1
    print "Getting Queueing Stats, 1st run..."
    # get counter the first time
    q_qty, queue_stat_dict = getqosstats(queue_stat_dict, run)
    print "Q: " + str(q_qty)
    print
    print "Sleeping " + str(delta_time) + " seconds..."
    time.sleep(float(delta_time))
    run += 1
    print
    print "Getting Queueing Stats, 2nd run..."
    # get counter the second time
    q_qty, queue_stat_dict = getqosstats(queue_stat_dict, run)

    # 4 + 2 egress queues
    if q_qty == 6:
        table = "{0:22}{1:>10}{2:>10}{3:>10}{4:>10}{5:>10}{6:>10}"
        print '-------------------------------------------------------------------------------------'
        print table.format("Interface Thput in", "0/Mbps", "1/Mbps", "2/Mbps", "3/Mbps", "CONTR/M", "SPAN/M")
        print table.format("          Drops in", "  bps", "  bps", " bps", " bps", "bps", " ")
        print '-------------------------------------------------------------------------------------'
    # 8 + 2 egress queues
    elif q_qty == 10:
        table = "{0:22}{1:>10}{2:>10}{3:>10}{4:>10}{5:>10}{6:>10}{7:>10}{8:>10}{9:>10}{10:>10}"
        print '----------------------------------------------------------------------------------------------------------------------------'
        print table.format("Interface Thput in", "0/Mbps", "1/Mbps", "2/Mbps", "3/Mbps", "4/Mbps", "5/Mbps", "6/Mbps",
                           "7/Mbps", "CONTR/M", "SPAN/M")
        print table.format("          Drops in", "  bps", "  bps", " bps", " bps", " bps", " bps", " bps", " bps",
                           "bps", " ")
        print '----------------------------------------------------------------------------------------------------------------------------'
    else:
        print 'Housten we got a problem....'
        sys.exit(1)
else:
    print 'Housten we got a problem....'
    sys.exit(1)

### print collected data in table format ###

for interface, value in sorted(queue_stat_dict[1].items()):
    #print "int: " + interface
    state = 0
    for k, v in (queue_stat_dict[1][interface].items()):
        if k == 'state':
            state = v
            #print "val: " + v

    # print q-put only for active interfaces (state == 1), otherwise the output becomes to long
    if state == '1':
        # build output
        eq_uc_stat_row = []
        eq_uc_stat_drop_row = []
        eq_mc_stat_row = []
        eq_mc_stat_drop_row = []

        # build a pretty short interface name
        tab_interface = interface.replace('ernet', '')
        filler = ''
        if re.match('^Eth\d/\d$', tab_interface): filler = ' '

        tab_interface = '*' + tab_interface + filler
        eq_uc_stat_row.append(tab_interface + " UC Thput")
        eq_uc_stat_drop_row.append("         UC Drop")
        eq_mc_stat_row.append("         MC Thput")
        eq_mc_stat_drop_row.append("         MC Drop")

        for queue_1, val_1 in sorted(queue_stat_dict[1][interface].items()):
            # print "q1:" + queue_1
            # print val_1

            # print table with absolut counter
            if not rate_flag:
                if queue_1 != 'state':
                    # print "q1:" + queue_1 + " q2:" + queue_2
                    # tput unit
                    stat_units = val_1['eq_stat_units']
                    stat_units = stat_units.replace("Pkts", " P")
                    stat_units = stat_units.replace("Byts", "")

                    # drop unit
                    stat_units_drop = val_1['eq_stat_units_drop']
                    stat_units_drop = stat_units_drop.replace("Pkts", " P")
                    stat_units_drop = stat_units_drop.replace("Byts", "")

                    # uc stat
                    eq_uc_stat_row.append(str(val_1['eq_uc_stat_value']) + stat_units)
                    eq_uc_stat_drop_row.append(str(val_1['eq_uc_stat_value_drop']) + stat_units_drop)

                    # mc stat
                    if val_1['eq_mc_stat_value'] == '---':
                        eq_mc_stat_row.append(val_1['eq_mc_stat_value'])
                        eq_mc_stat_drop_row.append(val_1['eq_mc_stat_value_drop'])
                    else:
                        eq_mc_stat_row.append(str(val_1['eq_mc_stat_value']) + stat_units)
                        eq_mc_stat_drop_row.append(str(val_1['eq_mc_stat_value_drop']) + stat_units_drop)

            # print table with throughput per seconds
            elif rate_flag:
                for queue_2, val_2 in sorted(queue_stat_dict[2][interface].items()):
                    # we are interested on queue entries
                    if queue_1 != 'state':
                        if queue_1 == queue_2:

                            # uc tput unit
                            stat_units = val_2['eq_stat_units']
                            stat_units = stat_units.replace("Pkts", " P")
                            stat_units = stat_units.replace("Byts", "")

                            rate_eq_uc_stat_value = int(val_2['eq_uc_stat_value']) - int(val_1['eq_uc_stat_value'])
                            rate_eq_uc_stat_value = round(rate_eq_uc_stat_value / 1000000 * 8 / int(delta_time), 1)
                            rate_eq_uc_stat_value = str(rate_eq_uc_stat_value) + stat_units

                            # mc tput
                            if val_2['eq_mc_stat_value'] == "---":
                                rate_eq_mc_stat_value = "---"
                            else:
                                rate_eq_mc_stat_value = int(val_2['eq_mc_stat_value']) - int(val_1['eq_mc_stat_value'])
                                rate_eq_mc_stat_value = round(rate_eq_mc_stat_value / 1000000 * 8 / int(delta_time), 1)
                                rate_eq_mc_stat_value = str(rate_eq_mc_stat_value) + stat_units

                            # drop unit
                            stat_units_drop = val_2['eq_stat_units_drop']
                            stat_units_drop = stat_units_drop.replace("Pkts", " P")
                            stat_units_drop = stat_units_drop.replace("Byts", "")

                            # uc drop
                            if val_2['eq_uc_stat_value_drop'] == "---":
                                rate_eq_uc_stat_value_drop = "---"
                            else:
                                rate_eq_uc_stat_value_drop = int(val_2['eq_uc_stat_value_drop']) - int(
                                    val_1['eq_uc_stat_value_drop'])
                                rate_eq_uc_stat_value_drop = round(rate_eq_uc_stat_value_drop * 8 / int(delta_time), 1)
                                rate_eq_uc_stat_value_drop = str(rate_eq_uc_stat_value_drop) + stat_units_drop

                            # mc drops
                            if val_2['eq_mc_stat_value_drop'] == '---':
                                rate_eq_mc_stat_value_drop = '---'
                            else:
                                rate_eq_mc_stat_value_drop = int(val_2['eq_mc_stat_value_drop']) - int(
                                    val_1['eq_mc_stat_value_drop'])
                                rate_eq_mc_stat_value_drop = round(rate_eq_mc_stat_value_drop * 8 / int(delta_time), 1)
                                rate_eq_mc_stat_value_drop = str(rate_eq_mc_stat_value_drop) + stat_units_drop

                            eq_uc_stat_row.append(rate_eq_uc_stat_value)
                            eq_uc_stat_drop_row.append(rate_eq_uc_stat_value_drop)
                            eq_mc_stat_row.append(rate_eq_mc_stat_value)
                            eq_mc_stat_drop_row.append(rate_eq_mc_stat_value_drop)
            else:
                print 'Housten we got a problem....'
                sys.exit(1)
        # print q-put for this interface
        print table.format(*eq_uc_stat_row)
        print table.format(*eq_uc_stat_drop_row)
        print table.format(*eq_mc_stat_row)
        print table.format(*eq_mc_stat_drop_row)
sys.exit()
