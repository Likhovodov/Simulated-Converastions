//webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

var gumStream; 						//stream from getUserMedia()
var rec; 							//Recorder.js object
var input; 							//MediaStreamAudioSourceNode we'll be recording
var blob;

// shim for AudioContext when it's not avb.
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext //audio context to help us record

var recordButton = document.getElementById("recordButton");
var stopButton = document.getElementById("stopButton");

//add events to those 2 buttons
recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);

function startRecording() {
	console.log("recordButton clicked");

	/*
		Simple constraints object, for more advanced audio features see
		https://addpipe.com/blog/audio-constraints-getusermedia/
	*/
    var constraints = { audio: true, video:false }

 	/*
    	Disable the record button until we get a success or fail from getUserMedia()
	*/
	recordButton.disabled = true;
	stopButton.disabled = false;

	/*
    	We're using the standard promise based getUserMedia()
    	https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
	*/
	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		console.log("getUserMedia() success, stream created, initializing Recorder.js ...");

		/*
			create an audio context after getUserMedia is called
			sampleRate might change after getUserMedia is called, like it does on macOS when recording through AirPods
			the sampleRate defaults to the one set in your OS for your playback device
		*/
		audioContext = new AudioContext();

		//update the format
		// document.getElementById("formats").innerHTML="Format: 1 channel pcm @ "+audioContext.sampleRate/1000+"kHz"

		/*  assign to gumStream for later use  */
		gumStream = stream;

		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);

		/*
			Create the Recorder object and configure to record mono sound (1 channel)
			Recording 2 channels  will double the file size
		*/
		rec = new Recorder(input,{numChannels:1})

		//start the recording process
		rec.record()

		console.log("Recording started");

	}).catch(function(err) {
	  	//enable the record button if getUserMedia() fails
    	recordButton.disabled = false;
    	stopButton.disabled = true;
	});
}

function stopRecording() {
	console.log("stopButton clicked");

	//disable the record and stop button so user can't re-record
	stopButton.disabled = true;
	recordButton.disabled = true;

	//hide and show elements
	document.getElementById("choice-form").style.display = "block";
	document.getElementById("embedded-video").style.display = "none";
	document.getElementById("recordButton").style.display = "none";
	document.getElementById("stopButton").style.display = "none";

	//tell the recorder to stop the recording
	rec.stop();

	//stop microphone access
	gumStream.getAudioTracks()[0].stop();

	//create the wav blob and pass it on to createDownloadLink
	rec.exportWAV(createDownloadLink);
	//  var blob = rec.exportWAV(createDownloadLink);
}

function createDownloadLink(blob) {

	var url = URL.createObjectURL(blob);
	var au = document.createElement('audio');
	var p = document.createElement('p');
	var link = document.createElement('a');

	//name of .wav file to use during upload and download (without extension)
	//Need to change this to fit the format of how we're storing audio files
    //Maybe filename is uuid of TemplateNodeResponse?
    //Or student email/current date
	var filename = new Date().toISOString();

	//add controls to the <audio> element
	au.controls = true;
	au.src = url;

	//save to disk link
	link.href = url;
	link.download = filename+".wav"; //download forces the browser to download the file using the  filename

	//add the new audio element to p
	p.appendChild(au);

	//add the filename to the p
	//Save this for debugging filename
	// p.appendChild(document.createTextNode(filename+".wav "))

	//upload link
	//I want to do this functionality without clicking the link
	// var upload = document.createElement('a');
	// upload.href="#";
	// upload.innerHTML = "Upload";
	// upload.addEventListener("click", function(event){
	// 	  var xhr=new XMLHttpRequest();
	// 	  xhr.onload=function(e) {
	// 	      if(this.readyState === 4) {
	// 	          console.log("Server returned: ",e.target.responseText);
	// 	      }
	// 	  };
	// 	  var fd=new FormData();
	// 	  fd.append("audio_data",blob, filename);
	// 	  xhr.open("POST","upload.php",true);
	// 	  xhr.send(fd);
	// })
	//p.appendChild(upload)//add the upload link to li

	//add the p element to the page
	recording.appendChild(p);
}

$(document).on('submit', '#choice-form', (form) => {
		console.log('submitted.')
    	sendData(blob)
});


function sendData(blob, filename) {
	$.ajax({
		type: 'POST',
		url: '{{ ct_node.get_absolute_url }}',
		dataType: 'json',
		data: {
			name: "audio_data",
			blob: blob,
			filename: filename,
			csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
		},
		success: res => {
			console.log('Success.')
			// result = res[res.compute];
			// document.getElementById(`input-text-${res.compute}`).value = result;
			// document.getElementById('graph-container').style = 'width: 100%; display: block;';
		}
	});
}