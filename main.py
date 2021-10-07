#!/usr/bin/python38


from flask import Flask, request, make_response, render_template, redirect, url_for, session
from markupsafe import Markup
from includes import *
from json2html import *
import json

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
    if vmanage == None:
        vmanage = userid = password = 'not set'
    return render_template('getsettings.html', vmanage=vmanage, userid=userid, password=password, secret='*****'+password[-2:])

###########################################################################
#  Read and save settings
###########################################################################
@app.route('/savesettings')
def savesettings():

    resp = make_response(redirect(url_for('menu')))

    # Save vManage settings in a cookie:
    for arg in request.args:
        resp.set_cookie(arg, request.args.get(arg), secure=True, httponly=True)

    return resp

###########################################################################
#  Read and save settings
###########################################################################

@app.route('/menu')
def menu():

    ### Clear user session variables from previous tasks
    session.clear()
    return render_template('menu.html', vmanage=request.cookies.get('vmanage'))


@app.route('/listedges')
def listedges():

    model = request.args.get('model') or 'all'
    mode = request.args.get('mode') or 'all'

    vmanage = login()
    data = list_edges(vmanage, mode = mode, model = model)
    vmanage.logout()
    data.insert(0, ['UUID','Hostname', 'Model','Mode'])
    output = buildtable(data)

    return render_template('table.html', title='List Edges', instructions='List of all edge devices',
                           data=Markup(output))

@app.route('/rmaedge')
def rmaedge():

    try:
        oldedge = request.args.get('oldedge') or session['oldedge']
        session['oldedge'] = oldedge
    except:
        vmanage = login()
        data = list_edges(vmanage, mode='vmanage')
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        output = buildtable(data, link='/rmaedge?oldedge=')
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Pick Old Edge',
                               instructions=Markup('Select the Edge device to replace:<br><br>'))
    try:
        newedge = request.args.get('newedge') or session['newedge']
        session['newedge'] = newedge
    except:
        vmanage = login()
        model = vmanage.get_request(f'device/models/{oldedge}')['name']
        session['model'] = model
        data = list_edges(vmanage, mode='cli', model=model)
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        output = buildtable(data, link='/rmaedge?newedge=')
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Pick New Edge',
                               instructions=Markup('Select the replacement Edge:<br><br>'))
    vmanage = login()
    template = get_device_template_variables(vmanage, oldedge)
    session['template'] = template
    vmanage.logout()
    jtemplate = Markup(json2html.convert(template))
    return render_template('rmaconfirm.html',template=jtemplate, oldedge=oldedge, newedge=newedge)

@app.route('/rmaconfirm')
def rmaconfirm():

    #
    ### Deletes oldedge, attaches template to newedge, returns job result
    #

    ### Invalidate Device Certificate
    vmanage = login()
    cert_status = set_certificate(vmanage, session['oldedge'], session['model'], 'invalid')
    output = '<b>Invalidate Certificate:</b><br>'
    output += str(cert_status)

    ### Delete old device
    delete_status = vmanage.delete_request(f'system/device/{session["oldedge"]}')
    output += '<br><b>Delete Edge:</b><br>'
    output += str(delete_status)

    ### Create template variables JSON object with new UUID
    template = session['template']
    template['device'][0]['csv-deviceId'] = session['newedge']
    payload = {"deviceTemplateList":[
        template
    ]
    }
    output += '<br><b>Build template payload</b><br>'
    output += (json.dumps(payload,indent=2))

    ### Attach template to new edge
    attach_job = vmanage.post_request('template/device/config/attachment', payload = payload)
    output += '<br><b>Attach Template:</b><br>'
    output += str(attach_job)
    output += action_status(vmanage, attach_job['id'])

    vmanage.logout()
    output += '<br><br><a href="/">Return to main menu</a>'
    return Markup(output)

@app.route('/deployedge')
def deployedge():

    ### Clear user session variables from previous tasks
    session.clear()
    return render_template('menu.html', vmanage=request.cookies.get('vmanage'))

@app.route('/editedge')
def editedge():

    #
    # Build a table of edges for user to select from.
    # If edge has already been set, move to next step.
    #

    try:
        edge = request.args.get('edge') or session['edge']
        session['edge'] = edge
    except:
        vmanage = login()
        data = list_edges(vmanage, mode='vmanage')
        data.insert(0, ['UUID', 'Hostname', 'Model', 'Mode'])
        output = buildtable(data, link='/editedge?edge=')
        vmanage.logout()
        return render_template('table.html', data=Markup(output), title='Edit Edge Values',
                               instructions=Markup('Select the Edge device to edit:<br><br>'))

    #
    # Build a form of variables for user to edit.
    # Post form to update template
    #

    try:
        variable = request.args.get('variable') or session['variable']
        session['variable'] = variable
    except:
        vmanage = login()
        template = get_device_template_variables(vmanage, edge)
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
                               instructions=Markup('Edit any values below and submit to update the device configuration:<br><br>'))

@app.route('/updatetemp', methods=['POST'])
def updatetemp():

    #
    # Retrieve variables and modify template
    #

    template = session['template']
    output = '<A HREF="/menu">Return to Main Menu.</A><BR>'
    output += 'Old Template:<BR>' + json2html.convert(template)

    ### Create template variables JSON object with new UUID

    variables = request.form
    for value in variables:
        template['device'][0][value] = variables[value]
    payload = {"deviceTemplateList":[
        template
    ]
    }
    output += "<BR>New Template:<BR>" + json2html.convert(payload)

    ### Attach template to new edge
    vmanage = login()
    attach_job = vmanage.post_request('template/device/config/attachment', payload = payload)
    output += '<br><b>Attach Template:</b><br>'
    output += str(attach_job)
    output += action_status(vmanage, attach_job['id'])
    vmanage.logout()

    output += '<br><br><a href="/menu">Return to main menu</a>'

    return Markup(output)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python38_app]