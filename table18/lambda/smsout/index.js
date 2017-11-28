exports.handler = (event, context, callback) => {
	const accountSid = 'AC81c53e774e3c9a1e5c40ac3260cdad5b';
	const authToken = 'e394cabc5efd8f453fce80d849fe4ba4';
	const client = require('twilio')(accountSid, authToken);

	/*
	{"notifications_id": "f4e1fdbc-384d-4cb1-8480-4d4d89ae277e", "text": "How are you", "media": null, "sent": false, "name": "Daniel Soromou", "from": "Joshua Adeyemi", "method": "number", "contact": "+18655563386"}
	*/
	var msgData = JSON.parse(event.Records[0].Sns.Message);
	console.log("Event", event);
	console.log("msgData:", msgData);
	var toAdd = msgData.contact;
	//statically set toAdd since we have a trial of twilio
	toAdd = "+16783506160";
	var params = {
	  body: msgData.text,
	  to: toAdd,
	  from: '+16785046552'
	};

	if(msgData.media != null && msgData.media != undefined) {
		params['mediaUrl'] = msgData.media;
	}
	console.log("Message out:", params);

	client.messages.create(params)
	.then(
		(message) => console.log("SID:",message));

    callback(null, 'Cool Kid Return Value');
}
