
from __future__ import print_function # Python 2/3 compatibility
import sys
import boto3
import json
import decimal
import uuid
import logging
import pymysql

logger = logging.getLogger()
logger.setLevel(logging.INFO)
sqs = boto3.resource('sqs', region_name='us-east-1')
sns = boto3.client('sns')



method_queue = {
    "SMS" : "sms.fifo",
    "Email" : "email.fifo",
    "twitter": "twitter.fifo",
    "facebook": "facebook.fifo"
}


method_arn = {
    "SMS" : "arn:aws:sns:us-east-1:103562472237:gg-sms",
    "Email" : "arn:aws:sns:us-east-1:103562472237:email",
    "twitter": "twitter.fifo",
    "facebook": "facebook.fifo"
}

#rds settings
rds_host  = "globalgiving18.ctkgbnpsh2jn.us-east-1.rds.amazonaws.com"
name = "admin18"
password = "z7aZsNzZj8onr6fqWDo9"
db_name = "globalgiving"

try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except:
    logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
    sys.exit()
    
# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


# Get donor informations
def get_donor_information(project_id):
    query  = ("select do.name as donor_name, do.email as donor_email, " +
    "do.phone as donor_phone, do.contact_preference as donor_contact_preference " +
    " from (select * from project where id = {}) pj inner join (select * from projectsdonors where notify=1) pd " +
    " on pj.id = pd.project_id inner join donor do on do.id = pd.donor_id  group "+
    " by donor_name, donor_email, donor_phone, donor_contact_preference").format(project_id)
    
    print(query)
    
    with conn.cursor() as cur:
        cur.execute(query)
        data = []
        for row in cur:
            data.append(row)
        return data
  
# Get project information
def get_project_information(project_id):
    query  = ("select * from project where id = {}").format(project_id)
    
    with conn.cursor() as cur:
        cur.execute(query)
        data = []
        for row in cur:
            data.append(row)
        return data

# Get project leader information
def get_project_leader_information(pl_source):
    query  = ("select * from pl where phone = '{}' or email = '{}'").format(pl_source, pl_source)
    with conn.cursor() as cur:
        cur.execute(query)
        data = []
        for row in cur:
            data.append(row)
        return data
    
# Save processed data in Notification table
def save_notification(data):
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
    table = dynamodb.Table('Notifications')
    table.put_item(Item = data)
   
    
def is_valide_data(data):
    return len(data) > 0


def get_project_id(project_leader_id):
    query  = ("select * from (select * from project where pl_id = {}) pj " +
              " inner join (select * from projectsdonors where notify=1)  "+
              " pd on pd.project_id = pj.id").format(project_leader_id)
    with conn.cursor() as cur:
        cur.execute(query)
        for row in cur:
            return row[0]
        

def dispatch_notification(data):
    method = data['method']
    print("The method is  : ", method)
    print("The message is publish in with queue ",method_queue[method])
    queue = sqs.get_queue_by_name(QueueName=method_queue[method])
    print(queue)
    response = queue.send_message(MessageBody=json.dumps(data), MessageGroupId='1', MessageDeduplicationId='2')

def dispatch_notification_sns(data):
    method = data['method']
    response = sns.publish(
        TargetArn=method_arn[method],
        Message=json.dumps({'default': json.dumps(data)}),
        MessageStructure='json')

    
def lambda_handler(event, context):
#if __name__ == '__main__' :
    # TODO implement
    """
    event ={
              "pl_source": "foromodanielsoromou@gmail.com",
              "pl_source_type": "text",
              "content" : "Hello it is very good",
              "media": None,
              }
    """
    
    
    project_leader_information = get_project_leader_information(event['pl_source'])
    print(project_leader_information)
    
    if is_valide_data(project_leader_information):
        project_leader_id = project_leader_information[0][0]
        project_id = get_project_id(project_leader_id)
        
        project_information = get_project_information(project_id)
        donor_information = get_donor_information(project_id)
        
        
        if (is_valide_data(project_information) and 
            is_valide_data(donor_information) ) :
            
            print("the donors list is : ", donor_information)
            for donor in donor_information:
                media_data = None
                if 'media' in event:
                    media_data = event['media'] 
                else: 
                    media_data = None
                
                contact = donor[1] if donor[3] == "Email" else  donor[2]
                notification = {
                    "notifications_id" : str(uuid.uuid4()),
                    "text" : event['content'],
                    "media" : media_data,
                    "sent" : True,
                    "name" : donor[0],
                    "from" : project_leader_information[0][1] ,
                    "method" : donor[3],
                    "contact": str(contact)
                }
                
                print(notification)
                
                
                save_notification(notification)
                
                dispatch_notification(notification)
                dispatch_notification_sns(notification)
                
                print("all is done")
            
            return True