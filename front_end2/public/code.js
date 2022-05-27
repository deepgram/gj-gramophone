(function () {

	const app = document.querySelector(".app");
	const socket = io();

	let uname;

	app.querySelector(".join-screen #join-user").addEventListener("click", function () {
		let username = app.querySelector(".join-screen #username").value;
		if (username.length == 0) {
			return;
		}
		socket.emit("newuser", username);
		uname = username;
		app.querySelector(".join-screen").classList.remove("active");
		app.querySelector(".chat-screen").classList.add("active");
	});

	app.querySelector(".chat-screen #send-message").addEventListener("click", function () {

		document.getElementById("send-message").disabled = true;
		const oldColor = document.getElementById("send-message").style.backgroundColor;
		document.getElementById("send-message").style.backgroundColor = "#FF0000";
		// record audio
		navigator.mediaDevices.getUserMedia({ audio: true })
			.then(stream => {
				console.log("has stream")
				const mediaRecorder = new MediaRecorder(stream);
				mediaRecorder.start();

				const audioChunks = [];

				mediaRecorder.addEventListener("dataavailable", event => {
					audioChunks.push(event.data);
				});

				mediaRecorder.addEventListener("stop", () => {
					const audioBlob = new Blob(audioChunks, { type: 'audio/webm;codecs=opus' });
					const audioUrl = URL.createObjectURL(audioBlob);
					const audio = new Audio(audioUrl);
					// audio.play();

					// postData();
					postData(audioBlob).then(data => {
						// console.log(data); // JSON data parsed by `data.json()` call
						const img = data[data.length-1]['img'];
						renderMessage("my", {
							username: uname,
							image: img
						});
						socket.emit("chat", {
							username: uname,
							image: img
						});
					});

				});

				setTimeout(() => {
					mediaRecorder.stop();
					document.getElementById("send-message").style.backgroundColor = oldColor;
					document.getElementById("send-message").disabled = false;
				}, 3000);
			});

		// app.querySelector(".chat-screen #message-input").value = "";
	});

	// app.querySelector(".chat-screen #exit-chat").addEventListener("click", function () {
	// 	socket.emit("exituser", uname);
	// 	window.location.href = window.location.href;
	// });

	socket.on("update", function (update) {
		renderMessage("update", update);
	});

	socket.on("chat", function (message) {
		console.log('hi1');
		renderMessage("other", message);
	});

	async function postData(audioData) {
		// Default options are marked with *

		// const response = fetch('http://sv1-j.node.sv1.consul:8094/text2img', {
		const response = await fetch('http://127.0.0.1:8080/speech2img', {
			method: 'POST', // *GET, POST, PUT, DELETE, etc.
			// mode: 'no-cors', // no-cors, *cors, same-origin
			headers: {
				// 'Content-Type': 'application/json'
				'Content-Type': 'audio/webm',
				'Authorization': 'Token b1c4bc5158fcad129d1d2412cf461e88bab70321'
				// 'Content-Type': 'application/x-www-form-urlencoded',
			},
			// redirect: 'follow', // manual, *follow, error
			// referrerPolicy: 'no-referrer', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
			// body: "{\"text\": \"party\"}" // body data type must match "Content-Type" header
			// body: `{\"url\": \"${audioData}\"}`
			body: audioData
		});
		// .then(res => {
		// 	console.log(res.json());
			
		// });
		// console.log(response.json())
		return response.json(); // parses JSON response into native JavaScript objects
	}

	function renderMessage(type, message) {
		let messageContainer = app.querySelector(".chat-screen .messages");
		console.log(message);
		if (type == "my") {
			let el = document.createElement("div");
			el.setAttribute("class", "message my-message");
			el.innerHTML = `
				<div>
					<div class="name">You</div>
					<div> <img src="data:image/png;base64,${message.image}" width="90%" height="90%"/> </div>
				</div>
			`;
			messageContainer.appendChild(el);
		} else if (type == "other") {
			console.log('yoyoy');
			let el = document.createElement("div");
			el.setAttribute("class", "message other-message");
			el.innerHTML = `
				<div>
					<div class="name">${message.username}</div>
					<div> <img src="data:image/png;base64,${message.image}" width="90%" height="90%"/> </div>
				</div>
			`;
			messageContainer.appendChild(el);
		} else if (type == "update") {
			let el = document.createElement("div");
			el.setAttribute("class", "update");
			el.innerText = message;
			messageContainer.appendChild(el);
		}
		// scroll chat to end
		messageContainer.scrollTop = messageContainer.scrollHeight - messageContainer.clientHeight;
	}

})();
