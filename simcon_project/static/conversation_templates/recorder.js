//webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

let gumStream; 						//stream from getUserMedia()
let rec; 							//Recorder.js object
let input; 							//MediaStreamAudioSourceNode we'll be recording
let recordAttempts = 0;				//Count of record response attempts
let blob;							//Audio blob

// shim for AudioContext when it's not avb.
let AudioContext = window.AudioContext || window.webkitAudioContext;
let audioContext;

let recordButton = document.getElementById("recordButton");
let stopButton = document.getElementById("stopButton");
let nextButton = document.getElementById("nextButton");

recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);
nextButton.addEventListener("click", acceptRecording);

function startRecording() {
	/*
		Simple constraints object, for more advanced audio features see
		https://addpipe.com/blog/audio-constraints-getusermedia/
	*/
    let constraints = { audio: true, video:false }
	toggleAudioControls(true, false, true);

	/*
    	We're using the standard promise based getUserMedia()
    	https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
	*/
	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		/*
			create an audio context after getUserMedia is called
			sampleRate might change after getUserMedia is called, like it does on macOS when recording through AirPods
			the sampleRate defaults to the one set in your OS for your playback device
		*/
		audioContext = new AudioContext();

		/*  assign to gumStream for later use  */
		gumStream = stream;

		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);

		/*
			Create the Recorder object and configure to record mono sound (1 channel)
			Recording 2 channels  will double the file size
		*/
		rec = new Recorder(input,{numChannels:1});
		rec.record();

	}).catch(function(err) {
	  	//enable the record button if getUserMedia() fails
		toggleAudioControls(false, true, true);
	});
}

function stopRecording() {
	recordAttempts++;
	if (hasAttempts()) {
		toggleAudioControls(false, true, false);
	}
	else {
		toggleAudioControls(true, true, false);
	}
	rec.stop();

	//stop microphone access
	gumStream.getAudioTracks()[0].stop();
	rec.exportWAV(createDownloadLink);
}

function acceptRecording() {
	toggleAudioControls(true, true, true);
	toggleElementDisplay();
	saveRecording();
}

function createDownloadLink(audioBlob) {
    blob = audioBlob;
	let url = URL.createObjectURL(blob);
	let au = document.createElement('audio');
	let p = document.createElement('p');
	let link = document.createElement('a');

	//name of .wav file for browser download
	let filename = new Date().toISOString();
	au.controls = true;
	au.src = url;
	link.href = url;
	link.download = filename+".wav"; //forces the browser to download the file using the filename

    //Check for old recording
	if (p.children.length > 0) {
		p.removeChild(p.firstChild);
	}
	p.appendChild(au);

	if (recording.children.length > 0) {
		recording.removeChild(recording.firstChild);
	}
	recording.appendChild(p);
}

function toggleElementDisplay() {
	document.getElementById("choice-form").style.display = "block";
	document.getElementById("embedded-video").style.display = "none";
	recordButton.style.display = "none";
	stopButton.style.display = "none";
	nextButton.style.display = "none";
}

function toggleAudioControls(record, stop, next) {
	recordButton.disabled = record;
	stopButton.disabled = stop;
	nextButton.disabled = next;
}
