#!python
"""
Copyright (c) 2012 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
__author__ = "David Brown <davibrow@cisco.com>"
__contributors__ = []
__copyright__ = "Copyright (c) 2012 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

from flask import Flask, make_response, render_template, redirect, url_for, session
from markupsafe import Markup
from includes import *
from json2html import *
import json
from urllib import parse
from vmanage_classes import Site
from datetime import datetime
import pandas as pd
import plotly
import plotly.express as px
import csv
from requests import get as get_request


app = Flask(__name__)
app.secret_key = 'any random string'


###########################################################################
#  Prompt user to set vManage settings
###########################################################################

@app.route('/')
def getsettings():
    vmanage = request.cookies.get('vmanage')
    userid = request.cookies.get('userid')
    password = request.cookies.get('password')
    my_ip = get_request('https://api.ipify.org/?format=json').json()['ip']
    if vmanage is None:
        vmanage = userid = password = 'not set'
    return render_template('getsettings.html', vmanage=vmanage, userid=userid, password=password,
                           secret='*****' + password[-2:], my_ip=my_ip)


###########################################################################
#  Read and save settings
###########################################################################

@app.route('/savesettings')
def savesettings():
    resp = make_response(redirect(url_for('menu')))

    # Save vManage settings in a cookie
    for arg in request.args:
        resp.set_cookie(arg, request.args.get(arg), secure=True, httponly=True)

    return resp


###########################################################################
#  Main menu.  This screen also clears any leftover session variables
###########################################################################

@app.route('/menu')
def menu():
    # Clear user session variables from previous tasks
    session.clear()
    try:
        vmanage = login()
    # Problems logging into vManage should be caught here...
    except Exception as err:
        return render_template('error.html', err=err)
    devices = vmanage.get_request('system/device/vedges')
    vmanage.logout()
    models = '<option label="all">all</option>\n'
    sites_list = []
    sites = ''
    models_list = []
    for device in devices['data']:
        if device['deviceModel'] not in models_list:
            models_list.append(device['deviceModel'])
        try:
            if device['site-id'] not in sites_list:
                sites_list.append(device['site-id'])
        except KeyError:
            continue
    models_list.sort()
    sites_list.sort()
    for model in models_list:
        models += f'<option label="{model}">{model}</option>\n'
    for site in sites_list:
        sites += f'<option label="{site}">{site}</option>\n'

    return render_template('menu.html', vmanage=request.cookies.get('vmanage'), models=Markup(models),
                           sites=Markup(sites))


###########################################################################
#  List edges.  Takes parameters model and mode.
###########################################################################

@app.route('/listedges')
def listedges():
    model = request.args.get('model') or 'all'
    mode = request.args.get('mode') or 'all'

    vmanage = login()
    data = list_edges(vmanage, mode=mode, model=model)
    vmanage.logout()
    data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
    output = buildtable(data)

    return render_template('table.html', title='List Edges', instructions='List of all edge devices',
                           data=Markup(output))


###########################################################################
#  List templates.  Takes parameter model.
###########################################################################

@app.route('/listtemplates')
def listtemplates():
    model = request.args.get('model') or 'all'
    vmanage = login()
    data = list_templates(vmanage, model)
    vmanage.logout()
    data.insert(0, ['UUID', 'Name', 'Description', 'Device Type'])
    output = buildtable(data)

    return render_template('table.html', title='List Templates', instructions='List of all templates',
                           data=Markup(output))


###########################################################################
#  RMA Edge. Collects device to replace, new device, and template details
###########################################################################
@app.route('/rmaedge')
def rmaedge():
    model = request.args.get('model') or session['model']
    session['model'] = model
    # List edges in vManage mode for user to select from
    # If oldedge is already set move to the next step.
    try:
        oldedge = request.args.get('oldedge') or session['oldedge']
        #oldedge = parse.quote_plus(oldedge)
        session['oldedge'] = oldedge
    except KeyError:
        vmanage = login()
        data = list_edges(vmanage, mode='vmanage', model=model)
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        output = buildtable(data, link='/rmaedge?oldedge=')
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Pick Old Edge',
                               instructions=Markup('Select the Edge device to replace:<br><br>'))

    # List edges in CLI mode for user to choose from.
    # If replacement edge is already set, move to the next step.
    try:
        newedge = request.args.get('newedge') or session['newedge']
        session['newedge'] = newedge
    except KeyError:
        vmanage = login()
        oldedge = parse.quote_plus(oldedge)
        model = vmanage.get_request(f'device/models/{oldedge}')['name']
        session['model'] = model
        data = list_edges(vmanage, mode='cli', model=model)
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        output = buildtable(data, link='/rmaedge?newedge=')
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Pick New Edge',
                               instructions=Markup('Select the replacement Edge:<br><br>'))

    #
    # Gather data and pass to the RMA confirmation page
    #

    vmanage = login()
    template = get_device_template_variables(vmanage, oldedge)
    session['template'] = template
    vmanage.logout()
    jtemplate = Markup(json2html.convert(template))
    return render_template('rmaconfirm.html', template=jtemplate, oldedge=oldedge, newedge=newedge)


###########################################################################
#  RMA Edge confirmation screen prompts for confirmation and executes exchange
###########################################################################
@app.route('/rmaconfirm')
def rmaconfirm():
    #
    # Deletes oldedge, attaches template to newedge, returns job result
    #

    # Invalidate Device Certificate
    vmanage = login()
    cert_status = set_certificate(vmanage, session['oldedge'], session['model'], 'invalid')
    output = '<b>Invalidate Certificate:</b><br>'
    output += str(cert_status)

    # Delete old device
    delete_status = vmanage.delete_request(f'system/device/{session["oldedge"]}')
    output += '<br><b>Delete Edge:</b><br>'
    output += str(delete_status)

    # Create template variables JSON object with new UUID
    template = session['template']
    template['device'][0]['csv-deviceId'] = session['newedge']
    payload = {"deviceTemplateList": [
        template
    ]
    }
    output += '<br><b>Build template payload</b><br>'
    output += (json.dumps(payload, indent=2))

    # Attach template to new edge
    attach_job = vmanage.post_request('template/device/config/attachment', payload=payload)
    output += '<br><b>Attach Template:</b><br>'
    output += str(attach_job)
    output += action_status(vmanage, attach_job['id'])

    vmanage.logout()
    output += '<br><br><a href="/">Return to main menu</a>'
    return Markup(output)


###########################################################################
#  Edit edge.  Collects edge device, displays form with template values
###########################################################################
@app.route('/editedge')
def editedge():
    model = request.args.get('model') or session['model']
    session['model'] = model
    # Build a table of edges for user to select from.
    # If edge has already been set, move to next step.
    try:
        edge = request.args.get('edge') or session['edge']
        session['edge'] = edge
    except KeyError:
        vmanage = login()
        data = list_edges(vmanage, mode='vmanage', model=model)
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        output = buildtable(data, link='/editedge?edge=')
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Edit Edge Values',
                               instructions=Markup('Select the Edge device to edit:<br><br>'))

    # Build a form of template variables for user to edit.
    # Uses templateId parameter or finds attached templateId
    # Post form to update template
    vmanage = login()
    try:
        templateId = request.args.get('templateId') or session['templateId']
        try:
            template = get_device_template_variables(vmanage, edge, templateId)
        # If user does not have Write privileges, error will be caught here
        except Exception as err:
            return render_template('error.html', err=err)
    except KeyError:
        template = get_device_template_variables(vmanage, edge)
    vmanage.logout()
    session['template'] = template
    data = template['device'][0]
    tabdata = [['Field', 'Value']]
    formdata = {}
    for item in data:
        if item[0] == '/':
            formdata[item] = data[item]
        else:
            tabdata.append([item, data[item]])
    output = buildtable(tabdata)
    output += buildform(formdata, action='/updatetemp')
    return render_template('table.html', data=Markup(output), title='Edit Edge Values',
                           instructions=Markup(
                               'Edit any values below and submit to update the device configuration:<br><br>'))


###########################################################################
#  Attach template and monitor job result
###########################################################################
@app.route('/updatetemp', methods=['POST'])
def updatetemp():
    # Retrieve variables and modify template
    template = session['template']
    output = '<A HREF="/menu">Return to Main Menu.</A><BR>'
    output += 'Old Template:<BR>' + json2html.convert(template)

    # Create template variables JSON object with new UUID
    variables = request.form
    for value in variables:
        template['device'][0][value] = variables[value]
    payload = {"deviceTemplateList": [
        template
    ]
    }
    output += "<BR>New Template:<BR>" + json2html.convert(payload)

    # Attach template to new edge
    vmanage = login()
    attach_job = vmanage.post_request('template/device/config/attachment', payload=payload)
    output += '<br><b>Attach Template:</b><br>'
    output += str(attach_job)
    output += action_status(vmanage, attach_job['id'])
    vmanage.logout()

    output += '<br><br><a href="/menu">Return to main menu</a>'

    return Markup(output)


###########################################################################
#  Deploy new edge. Prompt for edge, prompt for template, hand off to edit edge
###########################################################################
@app.route('/deployedge')
def deployedge():
    # List edges in CLI mode for user to choose from.
    # If replacement edge is already set, move to the next step.
    model = request.args.get('model') or session['model']
    session['model'] = model
    try:
        edge = request.args.get('edge') or session['edge']
        session['edge'] = edge
    except KeyError:
        vmanage = login()
        data = list_edges(vmanage, mode='cli', model=model)
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        for edge in data:
            edgelink = f'<a href="/deployedge?edge={edge[0]}&model={edge[2]}">{edge[0]}</a>'
            edge[0] = edgelink
        output = buildtable(data)
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Pick New Edge',
                               instructions=Markup('Select the replacement Edge:<br><br>'))

    # Build a list of templates that apply to the edge deviceType for the user to choose from
    # Send the templateId and deviceId to the Edit Edge routine
    vmanage = login()
    data = list_templates(vmanage, model=session['model'])
    vmanage.logout()
    data.insert(0, ['uuid', 'Name', 'Description', 'device type'])
    output = buildtable(data, link='/editedge?templateId=')
    return render_template('table.html', data=Markup(output), title='Pick a template',
                           instructions=Markup('Select the template to apply:<br><br>'))


@app.route('/sitebandwidth')
def sitebandwidth():
    siteid = request.args.get('siteid')
    vmanage = login()
    site = Site(vmanage, siteid)
    for edge in site.edges:
        edge.get_wan_interfaces(vmanage)
        edge.get_interface_stats(vmanage, interval=5)
    vmanage.logout()

    totals = {}
    headers = ['Time', 'Total WAN Bandwidth']
    for edge in site.edges:
        for interface in edge.interfaces:
            for stat in interface['stats']:
                # timestamp = datetime.fromtimestamp(stat['entry_time']/1000)
                timestamp = stat['entry_time']/1000
                int_bandwidth = stat['rx_kbps'] + stat['tx_kbps']
                if timestamp in totals.keys():
                    totals[timestamp]['Total WAN Bandwidth'] += int_bandwidth
                else:
                    totals[timestamp] = {
                        'Time': datetime.fromtimestamp(timestamp),
                        'Total WAN Bandwidth': int_bandwidth
                    }
                interface_name = f'{edge.hostname}:{interface["interface"]}'
                if interface_name + ' RX' not in headers:
                    headers.append(f'{interface_name} RX')
                    headers.append(f'{interface_name} TX')
                totals[timestamp][f'{interface_name} RX'] = stat['rx_kbps']
                totals[timestamp][f'{interface_name} TX'] = stat['tx_kbps']

    totals = dict(sorted(totals.items()))
    data = totals.values()

    df = pd.DataFrame(data)
    y_values = headers.copy()
    y_values.remove('Time')
    fig = px.line(df, x='Time', y=y_values)
    table = Markup(df.to_html())

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    description = 'WAN Bandwidth'
    return render_template('bandwidth.html', graphJSON=graphJSON, siteid=siteid, description=description, table=table)


@app.route('/sitereport')
def sitereport():

    siteid = request.args.get('siteid')
    vmanage = login()
    site = Site(vmanage, siteid)
    for edge in site.edges:
        edge.get_wan_interfaces(vmanage)
        edge.get_tables(vmanage)
    vmanage.logout()

    edges_dict = {}
    interfaces_tables = []
    vrrp_tables = []
    bfd_tables = []
    bgp_tables = []
    arp_tables = []
    omp_tables = []
    for edge_num, edge in enumerate(site.edges):
        edges_dict.update({edge.hostname: {
            'Model': edge.model,
            'System IP': edge.sys_ip,
            'Certificate': edge.validity,
            'Reachability': edge.reachability,
            'Software': edge.version,
            'Serial Number': edge.uuid,
            'WAN Interfaces': f'table{edge_num}table',
            'OMP': f'omp{edge_num}omp',
            'BFD': f'bfd{edge_num}bfd',
            'BGP': f'bgp{edge_num}bgp',
            'ARP': f'arp{edge_num}arp',
            'VRRP': f'vrrp{edge_num}vrrp',
        }})
        wan_interfaces = {}
        vrrp = bgp = {}
        for num, interface in enumerate(edge.interfaces):
            wan_interfaces[f'WAN Interface {num + 1}'] = {f'Interface': interface['interface'],
                                                          f'Color': interface['color'],
                                                          f'Weight': interface['weight'],
                                                          f'vManage Conns': interface['num-vmanages'],
                                                          f'vSmart Conns': interface['num-vsmarts']
                                                          }
        interfaces_tables.append(pd.DataFrame(wan_interfaces).to_html())
        for group in edge.tables['vrrp']:
            vrrp[group["if-name"]] = {'Group': group['group-id'],
                                      'VIP': group['virtual-ip'],
                                      'State': group['vrrp-state']
                                      }
        vrrp_tables.append(pd.DataFrame(vrrp).to_html())
        omp_tables.append(f'State:{edge.tables["omp"][0]["operstate"]}<br>'
                          f'Routes Rec:{edge.tables["omp"][0]["routes-received"]}<br>'
                          f'Routes Sent:{edge.tables["omp"][0]["routes-sent"]}<br>'
                          f'Routes Installed:{edge.tables["omp"][0]["routes-installed"]}<br>')
        bfd_tables.append(f'BFD Max:{edge.tables["bfd"][0]["bfd-sessions-max"]}<br>'
                          f'BFD Up:{edge.tables["bfd"][0]["bfd-sessions-up"]}<br>')
        if len(edge.tables['bgp']) == 0:
            bgp_tables.append('N/A')
        arp_list = 'ARP Learned on:'
        for entry in edge.tables['arp']:
            try:
                if 'dynamic' in entry['mode']:
                    if entry['interface'] not in arp_list:
                        arp_list += f'<br>{entry["interface"]}'
            except KeyError:
                continue
        if arp_list == 'ARP Learned on:':
            arp_list = 'ARP Learned on:<br>None'
        arp_tables.append(arp_list)

    edge_table = pd.DataFrame(data=edges_dict).to_html()
    for num, table in enumerate(interfaces_tables):
        edge_table = edge_table.replace(f'table{num}table', table)
    for num, table in enumerate(vrrp_tables):
        edge_table = edge_table.replace(f'vrrp{num}vrrp', table)
    for num, table in enumerate(omp_tables):
        edge_table = edge_table.replace(f'omp{num}omp', table)
    for num, table in enumerate(bfd_tables):
        edge_table = edge_table.replace(f'bfd{num}bfd', table)
    for num, table in enumerate(bgp_tables):
        edge_table = edge_table.replace(f'bgp{num}bgp', table)
    for num, table in enumerate(arp_tables):
        edge_table = edge_table.replace(f'arp{num}arp', table)

    return render_template('sitereport.html', siteid=siteid, edge_table=Markup(edge_table))


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python38_app]
