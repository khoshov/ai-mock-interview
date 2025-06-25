

// let socket = new WebSocket('ws://localhost:8000/ws/chat/');

// socket.onmessage = function(event) {
//     let djangodata = JSON.parse(event.data)
//     console.log(djangodata)

//     document.querySelector('#text').innerText = djangodata.value
// }

const chatSocket = new WebSocket(
    'ws://localhost:8000/ws/chat/'
);

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    document.querySelector('#chat-log').innerHTML += `<b>${data.sender}:</b> ${data.message}<br>`;
};

document.querySelector('#chat-message-submit').onclick = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    chatSocket.send(JSON.stringify({
        'message': message
    }));
    messageInputDom.value = '';
};