console.log("대기방 입장")

let userNickname = localStorage.getItem('nickname');  // Retrieve nickname from local storage
let socket = io();

let gameRoomNum;

getUserInfo()
ready()

function getUserInfo(){
    console.log("유저정보 요청 시도:", userNickname)

    const url = "http://localhost:5000/user?nickname=" + userNickname 

    fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json' // 요청 헤더에 JSON 형식을 명시적으로 지정
        },
    })
        .then(response => response.json()) // 응답을 JSON 형식으로 파싱
        .then(data => {
            // 응답 데이터 처리
            console.log(data)
            document.getElementById('own-nickname').textContent = data.nickname;
            let record = data.record.win + '승 ' + data.record.lose + '패';
            document.getElementById('own-record').textContent = record;
        })
        .catch(error => {
            // 에러 처리
            alert("유저정보 요청 실패")
        });

}

function ready(){
    console.log("게임 준비 시도:", userNickname)

    const data = {"nickname" : userNickname}

    socket.emit('waiting', data)
}

socket.on('readyGame', function(data) {

    console.log(data)

    // 상대 플레이어 화면에 표시
    opp_player = document.getElementsByClassName("profile-box opponent-profile")
    opp_player.item(0).innerHTML = `
        <div class="profile-picture">
            <!-- Profile picture will go here -->
        </div>
        <div class="profile-info">
            <h2>${data.opp_nickname}</h2>
            <h3>전적</h3>
            <p>${data.opp_record.win}승 ${data.opp_record.lose}패</p>
        </div>
    `;

    if(data.reader){
        start_buttom = document.getElementById("ready-button")
        start_buttom.disabled  = false
    }

    gameRoomNum = data.game_room_num

    // 로컬에 게임방 번호 저장
    localStorage.setItem("gameRoomNum", gameRoomNum)
});

function startGame(){
    alert("게임 시작!")

    const data = {"game_room_num": gameRoomNum}
    socket.emit("startGame", data)
}

socket.on("createBingoCard", function(data) {
    console.log(data)

    // window.location.href = '/game';
})

socket.on("moveGamePage", function() {
    window.location.href = '/game';
})