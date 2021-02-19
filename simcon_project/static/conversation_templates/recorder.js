// webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

let gumStream; 						//stream from getUserMedia()
let rec; 							//Recorder.js object
let input; 							//MediaStreamAudioSourceNode we'll be recording
let recordAttempts;					//Count of record response attempts

// shim for AudioContext when it's not avb.
let AudioContext = window.AudioContext || window.webkitAudioContext;
let audioContext;

let recordButton = document.getElementById("recordButton");
let stopButton = document.getElementById("stopButton");
let nextButton = document.getElementById("nextButton");
let info = document.getElementById("info");
let recording = document.getElementById("recording");

recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);

function startRecording() {
	/*
		Simple constraints object, for more advanced audio features see
		https://addpipe.com/blog/audio-constraints-getusermedia/
	*/
    let constraints = { audio: true, video:false }
	toggleAudioControls(true, false, true);
    // remove previous recording
	if (recording.children.length > 0) {
		recording.removeChild(recording.firstChild);
	}

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

		/* assign to gumStream for later use */
		gumStream = stream;

		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);

		/*
			Create the Recorder object and configure to record mono sound (1 channel)
			Recording 2 channels  will double the file size
		*/
		rec = new Recorder(input,{numChannels:1});
		rec.record();
		info.innerText = "Recording...";

	}).catch(function(err) {
	  	// enable the record button if getUserMedia() fails
		toggleAudioControls(false, true, true);
		info.innerText = "";
	});
}

function stopRecording() {
	recordAttempts = JSON.parse(sessionStorage.getItem('recordAttempts'));
	recordAttempts++;
	let attemptsLeft = hasAttempts();
	if (attemptsLeft > 1) {
		toggleAudioControls(false, true, false);
		info.innerText = recordAttempts + " attempts left to record";
	} else if (attemptsLeft === 1) {
		toggleAudioControls(false, true, false);
		info.innerText = recordAttempts + " attempt left to record";
	} else {
		toggleAudioControls(true, true, false);
		info.innerText = "No attempts left to record";
	}
	sessionStorage.setItem('recordAttempts', JSON.stringify(recordAttempts));
	rec.stop();

	// stop microphone access
	gumStream.getAudioTracks()[0].stop();
	rec.exportWAV(createDownloadLink);
}

function createDownloadLink(blob) {
	let url = URL.createObjectURL(blob);
	let au = document.createElement('audio');
	let p = document.createElement('p');
	let link = document.createElement('a');

	// name of .wav file for browser download
	let filename = new Date().toISOString();
	au.controls = true;
	au.src = url;
	link.href = url;
	link.download = filename+".wav"; //forces the browser to download the file using the filename

    // Check for old recording
	if (p.children.length > 0) {
		p.removeChild(p.firstChild);
	}
	p.appendChild(au);
	recording.appendChild(p);
	saveRecording(blob);
}

function toggleAudioControls(record, stop, next) {
	recordButton.disabled = record;
	stopButton.disabled = stop;
	nextButton.disabled = next;
}
