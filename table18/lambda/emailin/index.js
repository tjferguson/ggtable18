exports.handler = (event, context, callback) => {
    var AWS = require('aws-sdk'); 
    var fs = require('fs');

    var s3 = new AWS.S3();
    var lambda = new AWS.Lambda({
      region: 'us-east-1'
    });
    const simpleParser = require('mailparser').simpleParser;
            
    var src_bkt = event.Records[0].s3.bucket.name;
    var src_key = event.Records[0].s3.object.key;
    console.log("Srckey: " + src_key);
    
    // Retrieve the object
    s3.getObject({
        Bucket: src_bkt,
        Key: src_key
    }, function(err, data) {
        if (err) {
            console.log(err, err.stack);
            callback(err);
        } else {
            var emailMessage = data.Body.toString('ascii');
            simpleParser(emailMessage, (err, mail)=>{
                var fromAddress = mail.from.text;
                if(fromAddress.indexOf("<") > 0) {
                    var start = fromAddress.indexOf("<");
                    var length = fromAddress.indexOf(">")-start-1;
                    fromAddress = fromAddress.substr(start+1, length);
                }

                var subject = mail.subject;
                var body = mail.text;
                var attachments = mail.attachments;
                var media = [];

                for(i = 0; i < attachments.length; i++) {
                    var attach = attachments[i];
                        console.log("Filename: " + attach.filename);
                        var fn = new Date().getTime() + attach.filename;

                        var params = {
                            Bucket : "t18pub",
                            Key : fn,
                            Body : attach.content
                        }
                        media[i] = "https://s3.amazonaws.com/t18pub/"+fn;

                        s3.putObject(params, function(err, data) {
                          if (err) {
                            console.log(err, err.stack); // an error occurred
                        }
                          else {     
                            console.log("res:" + data);
                          }     // successful response
                        });
                }
                console.log("From:" + fromAddress);
                console.log("Subject: "+ subject);
                console.log("Body: " + body);
                console.log("Attachments:", media);

                var params = {
                    "pl_source": fromAddress,
                    "pl_source_type": "email",
                    "content": subject+"\n\n"+body,
                    "media": media
                };

                var addToQueueParams = {
                  FunctionName: 'data_processing',
                  Payload: JSON.stringify(params, null, 2) 
                };

                lambda.invoke(addToQueueParams, function(err, data) {
                     if (err) {
                        console.log("ERROR", err);
                     } else {
                        console.log("Got back data from data_processing call: " + data);
                     }
                  });

                
            });

            callback(null, null);
        }
    });

    callback(null, 'Cool Kid Return Value');
};