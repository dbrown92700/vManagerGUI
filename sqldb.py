from dotenv import load_dotenv
import os
# Fake PyMySQL's version and install as MySQLdb
# https://adamj.eu/tech/2020/02/04/how-to-use-pymysql-with-django/
import pymysql
pymysql.version_info = (1, 4, 2, "final", 0)
pymysql.install_as_MySQLdb()
import MySQLdb
load_dotenv()


class MyDb:
    def __init__(self, org):
        load_dotenv()
        print(os.getenv('HOST'))
        self.mydb = MySQLdb.connect(
            host=os.getenv("SQLHOST"),
            user=os.getenv("SQLUSER"),
            passwd=os.getenv("SQLPASS"),
            db=os.getenv("DATABASE"),
            autocommit=True,
            ssl={"ca": os.getenv("SQLCERT")})
        self.my_cursor = self.mydb.cursor()
        self.my_cursor.execute('SHOW TABLES')
        self.org_id = org

        table_exists = False
        for tab in self.my_cursor:
            if self.org_id in tab:
                table_exists = True
                break
        if not table_exists:
            command = f'CREATE TABLE `{self.org_id}` (templateName VARCHAR(255), templateId VARCHAR(40))'
            self.my_cursor.execute(command)

    def template_exists(self, template_id):
        count = self.my_cursor.execute(f'SELECT * FROM `{self.org_id}` WHERE templateId="{template_id}"')
        if count == 0:
            return False
        else:
            return True

    def template_init(self, template_id, template_name, keys):
        # keys is a list of
        self.my_cursor.execute(f'INSERT INTO `{self.org_id}` VALUES ("{template_name}", "{template_id}")')
        cmd = f'CREATE TABLE `{template_id}` (' \
              f'property VARCHAR(255),' \
              f'description VARCHAR(255),' \
              f'type VARCHAR(10),' \
              f'category varchar(20))'
        self.my_cursor.execute(cmd)
        for key in keys:
            category = 'Other'
            if key[0:3] == '/0/':
                category = 'Transport'
            elif key[0:9] == '//system/':
                category = 'System'
            elif key[1:key[1:].find('/')+1].isdigit():
                category = 'LAN'
            description = keys[key]
            self.my_cursor.execute(f'INSERT INTO `{template_id}` (property, description, type, category) '
                                   f'VALUES ("{key}", "{description}", "text", "{category}")')

    # Template get function validates that database entry exists, initializes if necessary,
    # validates that the database fields matches the template fields, and returns the database as a dictionary.
    # If template name and keys are not specified, function returns database entry with no update.
    def template_get(self, template_id, template_name=None, vm_keys=()):
        # Validate if Template is initialized and initialize if necessary
        count = self.my_cursor.execute(f'SELECT * FROM `{self.org_id}` WHERE templateId="{template_id}"')
        if template_name and (count == 0):
            self.template_init(template_id, template_name, vm_keys)
        # Fetch all lines from the database template entry
        self.my_cursor.execute(f'SELECT * FROM `{template_id}`')
        properties = self.my_cursor.fetchall()
        properties_dict = {}
        for prop in properties:
            # Delete any fields that are no longer in the template
            if vm_keys and (prop[0] not in vm_keys):
                self.my_cursor.execute(f'DELETE FROM `{template_id}` WHERE property="{prop[0]}"')
                continue
            # Add relevant fields to the return data
            properties_dict[prop[0]] = [prop[1], prop[2], prop[3]]
        for key in vm_keys:
            # Add any new template fields that are not in the database
            if key not in list(properties_dict.keys()):
                properties_dict[key] = [key, "text", "New Template Value"]
                command = f'INSERT INTO `{template_id}` (property, description, type, category) VALUES ' \
                          f'("{key}", "{key}", "text", "New Template Value")'
                print(command)
                self.my_cursor.execute(command)
        return properties_dict

    # Updates the settings for each field in the template database
    def template_update(self, template_id, properties):
        for prop in properties:
            if not self.my_cursor.execute(f'UPDATE `{template_id}` SET '
                                          f'description="{prop[1]}",'
                                          f'type="{prop[2]}",'
                                          f'category="{prop[3]}" '
                                          f'WHERE property="{prop[0]}"'):
                self.my_cursor.execute(f'INSERT INTO `{template_id}` '
                                       f'VALUES ("{prop[0]}","{prop[1]}","{prop[2]}","{prop[3]}")')

    def close(self):
        self.my_cursor.close()
        self.mydb.close()
