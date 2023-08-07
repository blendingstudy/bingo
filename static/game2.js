const MAX_BALLS_DISPLAYED = 6;
const nickname = localStorage.getItem("nickname") // 닉네임
let gameRoomNum; // 게임방 번호
let myBingoCardCells;
let gameOver = false;
let opp_player_idx = 0
let gameMatchNum;

console.log("닉네임: " + nickname)
const socket = io() // 웹소켓 초기화

setSID();

setTimeout(() => {
    waiting();
}, 1000)

getUserInfo();

// HTML 요소 선택
const tickets = document.getElementsByClassName('ticket');

// 클릭 이벤트 리스너 등록
for(let i=0; i<tickets.length; i++){
    let ticket = tickets.item(i)
    ticket.addEventListener('click', (event) => {
        // 클릭 이벤트 발생 시 실행될 코드
        if(!event.target.classList.contains('sold')){
            console.log('Button clicked!');
            event.target.classList.add('sold');
        }
        
    });
}




// sid 세팅
function setSID(){
    const data = {
        "nickname" : nickname
    }
    
    socket.emit("setSID", data)
}

function getUserInfo(){
    console.log("유저정보 요청 시도:", nickname)

    const url = "http://localhost:5000/user?nickname=" + nickname 

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
            
            const imgElement = document.createElement("img");
            imgElement.classList.add("profile-image");
            imgElement.src = data.profileIMG;
            imgElement.alt = "프로필 이미지";
            
            document.querySelector(".user .profile-img").appendChild(imgElement);

            document.getElementById('own-nickname').textContent = data.nickname;
        })
        .catch(error => {
            // 에러 처리
            alert("유저정보 요청 실패")
        });

}

function waiting(){
    const data = {"nickname" : nickname}

    socket.emit('waiting', data)
}


// 이전 매칭된 플레이어의 정보
socket.on('gameMatchComplete', function(data) {

    console.log(data)

    // 상대 플레이어 화면에 표시
    opp_player = document.getElementsByClassName("player opponent")
    document.get
    opp_player.item(opp_player_idx).innerHTML = `
        <div class="profile-section"> 
            <div class="profile-img">
                <img class="profile-image" src=${data.opp_profile_img} alt="프로필 이미지">
            </div>
            <div class="nickname">${data.opp_nickname}</div>
        </div>
        <div class="bingo-container">
            <div class="bingo-board">
                <div class="bingo-card"></div>
            </div>
        </div>
    `;
    opp_player_idx++

    gameMatchNum = Number(data.game_match_num)

    // 로컬에 게임방 번호 저장
    localStorage.setItem("gameMatchNum", gameMatchNum)
});

// 새로운 플레이어 정보
socket.on('newPlayerMatched', function(data) {
    console.log(data)

    // 상대 플레이어 화면에 표시
    opp_player = document.getElementsByClassName("player opponent")
    opp_player.item(data.idx-2).innerHTML = `
        <div class="profile-section"> 
            <div class="profile-img">
                <img class="profile-image" src=${data.opp_profile_img} alt="프로필 이미지">
            </div>
            <div class="nickname">${data.opp_nickname}</div>
        </div>
        <div class="bingo-container">
            <div class="bingo-board">
                <div class="bingo-card"></div>
            </div>
        </div>
    `;
    opp_player_idx++

    gameMatchNum = Number(data.game_match_num)

    // 로컬에 게임방 번호 저장
    localStorage.setItem("gameMatchNum", gameMatchNum)
})


// 어떤 플레이어가 나감
socket.on("playerOutOfMatch", function() {
    console.log("플레이어 나감")
    console.log(opp_player_idx)
    opp_players = document.getElementsByClassName("player opponent")
    for(let i=0; i<opp_player_idx; i++){
        opp_players.item(i).innerHTML = ``;
        console.log("플레이어 나가서 전체 삭제함!")
    }
    opp_player_idx = 0

    const data = {"game_match_num": gameMatchNum}
    socket.emit("resendPlayerMathcInfo", data)
})