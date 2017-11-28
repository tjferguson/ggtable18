
'use strict';

const AWS = require('aws-sdk');
const util = require('util');

var ses = new AWS.SES({
   region: 'us-east-1'
});

exports.handler = (event, context, callback) => {
    try {
        var my_event = JSON.parse(event.Records[0].Sns.Message);
        var my_message = `<p>${my_event.text}</p>`;

        console.log(`my_event: ${my_event}`);
        console.log(`Contact: ${my_event.contact}`);
        
        if (my_event.media != null) {
            if (util.isArray(my_event.media)) {
                for (var i = 0, len = my_event.media.length; i < len; i++) {
                    my_message = `${my_message}<p><img src="${my_event.media[i]}"></p>`;
                }
            } else {
                my_message = `${my_message}<p><img src="${my_event.media.toString()}"></p>`;
            }
        }

        var eParams = {
            Destination: {
                ToAddresses: [my_event.contact]
            },
            Message: {
                Body: {
                    Html: {
                        Data: my_message
                    }
                },
                Subject: {
                    Data: "Project update from GlobalGiving!"
                }
            },
            Source: "noreply@overwrittenstack.com"
        };
    
        console.log('===SENDING EMAIL===');
        var email = ses.sendEmail(eParams, function(err, data){
            if(err) console.log(err);
            else {
                console.log("===EMAIL SENT===");
                console.log(data);
                console.log("EMAIL CODE END");
                console.log('EMAIL: ', email);
                context.succeed(event);
            }
        });

    } catch (err) {
        callback(err);
    }
};
