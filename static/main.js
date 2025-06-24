

let socket = new WebSocket('ws://localhost:8000/ws/chat/');

socket.onmessage = function(event) {
    let djangodata = JSON.parse(event.data)
    console.log(djangodata)

    document.querySelector('#text').innerText = djangodata.value
}