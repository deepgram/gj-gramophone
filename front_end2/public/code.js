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
					const audioBlob = new Blob(audioChunks, {type: 'audio/webm;codecs=opus'});
					const audioUrl = URL.createObjectURL(audioBlob);
					const audio = new Audio(audioUrl);
					audio.play();
				});

				setTimeout(() => {
					mediaRecorder.stop();
					document.getElementById("send-message").style.backgroundColor = oldColor;

					renderMessage("my", {
						username: uname,
						text: "Insert Image"
					});
					socket.emit("chat", {
						username: uname,
						text: "Insert Image"
					});

					document.getElementById("send-message").disabled = false;

					
				}, 5000);
			});

		// app.querySelector(".chat-screen #message-input").value = "";
	});

	app.querySelector(".chat-screen #exit-chat").addEventListener("click", function () {
		socket.emit("exituser", uname);
		window.location.href = window.location.href;
	});

	socket.on("update", function (update) {
		renderMessage("update", update);
	});

	socket.on("chat", function (message) {
		renderMessage("other", message);
	});

	function renderMessage(type, message) {
		let messageContainer = app.querySelector(".chat-screen .messages");
		console.log(message);
		if (type == "my") {
			let el = document.createElement("div");
			el.setAttribute("class", "message my-message");
			el.innerHTML = `
				<div>
					<div class="name">You</div>
					<div class="text">${message.text}</div>
				</div>
			`;
			messageContainer.appendChild(el);
		} else if (type == "other") {
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
