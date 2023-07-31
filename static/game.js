const socket = io() // 웹소켓 초기화
const MAX_BALLS_DISPLAYED = 6;
let gameRoomNum; // 게임방 번호
const nickname = localStorage.getItem("nickname") // 닉네임
let myBingoCardCells;
let gameOver = false;
const WAITING_PAGE = 0;
const GAME_PAGE = 1;
let pageStatus = WAITING_PAGE;

console.log("닉네임: " + nickname)

let userNickname = localStorage.getItem('nickname');  // Retrieve nickname from local storage
let gameMatchNum;

resetSID();
setSID();
setTimeout(() => {
    waiting();
}, 1000)
getUserInfo();

// sid 다시 세팅
function resetSID(){
    const data = {
        "nickname" : nickname
    }
    
    socket.emit("resetSID", data)
}

function setSID(){
    const data = {
        "nickname" : nickname
    }
    
    socket.emit("setSID", data)
}

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
            
            const imgElement = document.createElement("img");
            imgElement.classList.add("profile-image");
            imgElement.src = data.profileIMG;
            imgElement.alt = "프로필 이미지";
            
            document.querySelector(".own-profile .profile-picture").appendChild(imgElement);

            document.getElementById('own-nickname').textContent = data.nickname;
            let record = data.record.win + '승 ' + data.record.lose + '패';
            document.getElementById('own-record').textContent = record;
        })
        .catch(error => {
            // 에러 처리
            alert("유저정보 요청 실패")
        });

}

function waiting(){
    const data = {"nickname" : userNickname}

    socket.emit('waiting', data)
}

let opp_player_idx = 0
// 이전 매칭된 플레이어의 정보
socket.on('gameMatchComplete', function(data) {

    console.log(data)

    // 상대 플레이어 화면에 표시
    opp_player = document.getElementsByClassName("profile-box opponent-profile")
    opp_player.item(opp_player_idx).innerHTML = `
        <div class="profile-picture">
            <img class="profile-image" src=${data.opp_profile_img} alt="프로필 이미지">
        </div>
        <div class="profile-info">
            <h2>${data.opp_nickname}</h2>
            <h3>전적</h3>
            <p>${data.opp_record.win}승 ${data.opp_record.lose}패</p>
        </div>
    `;
    opp_player_idx++

    if(data.leader){
        start_buttom = document.getElementById("ready-button")
        start_buttom.disabled  = false
    }

    gameMatchNum = Number(data.game_match_num)

    // 로컬에 게임방 번호 저장
    localStorage.setItem("gameMatchNum", gameMatchNum)
});

// 새로운 플레이어 정보
socket.on('newPlayerMatched', function(data) {
    console.log(data)

    // 상대 플레이어 화면에 표시
    opp_player = document.getElementsByClassName("profile-box opponent-profile")
    opp_player.item(data.idx-2).innerHTML = `
        <div class="profile-picture">
            <img class="profile-image" src=${data.opp_profile_img} alt="프로필 이미지">
        </div>
        <div class="profile-info">
            <h2>${data.opp_nickname}</h2>
            <h3>전적</h3>
            <p>${data.opp_record.win}승 ${data.opp_record.lose}패</p>
        </div>
    `;
    opp_player_idx++

    if(data.leader){
        start_buttom = document.getElementById("ready-button")
        start_buttom.disabled  = false
    }

    gameMatchNum = Number(data.game_match_num)

    // 로컬에 게임방 번호 저장
    localStorage.setItem("gameMatchNum", gameMatchNum)
})

// 어떤 플레이어가 나감
socket.on("playerOutOfMatch", function() {
    console.log("플레이어 나감")
    console.log(opp_player_idx)
    opp_players = document.getElementsByClassName("profile-box opponent-profile")
    for(let i=0; i<opp_player_idx; i++){
        opp_players.item(i).innerHTML = ``;
        console.log("플레이어 나가서 전체 삭제함!")
    }
    opp_player_idx = 0

    const data = {"game_match_num": gameMatchNum}
    socket.emit("resendPlayerMathcInfo", data)
})

// 게임 시작버튼 클릭
function startGame(){
    const data = {"game_match_num": gameMatchNum}
    socket.emit("startGame", data)
}

socket.on("moveGamePage", (data) => {
    localStorage.setItem("gameRoomNum", data.gameRoomNum)
    gameRoomNum = data.gameRoomNum

    startCountdown();
    setTimeout(() => {
        changePageFromWaitingToGame();
        pageStatus = GAME_PAGE;
    }, 3000);
    
})

// 5초 동안 카운트다운하는 함수
function startCountdown() {
    var bar = document.getElementById("countdown-bar");
    var width = 100; // 초기 너비 (100%)
    var decrement = (width / 3); // 3초 동안 감소해야하는 너비의 1/10
  
    var timer = setInterval(function() {
        width -= decrement; // 너비 감소
        bar.style.width = width + "%"; // 너비 적용
    
        if (width <= 0) {
            clearInterval(timer); // 카운트다운 종료
            document.getElementById("ready-button").disabled = false; // 버튼 활성화
        }
    }, 1000); // 0.1초마다 실행
}

// 대기페이지 -> 게임페이지로 화면 전환
function changePageFromWaitingToGame(){
    let gameBody = document.getElementById("game");
    let waitingBody = document.getElementById("waiting");

    gameBody.style.display = "flex";
    waitingBody.style.display = "none";

    enterGameRoom();
}

// 게임방 입장 알림
function enterGameRoom(){
    const data = {
        "gameRoomNum" : gameRoomNum,
        "nickname" : nickname
    }
    socket.emit("enterGameRoom", data)
}


// 상대방 유저정보와 내 유저정보, 내 빙고판 데이터 받기.
// 화면에 정보 띄움.
socket.on("bingoGameInfo", function(data) {
    // console.log(data)
    const myPlayer = data.player
    const oppPlayers = data.opp_players
    const bingoCard = data.bingo_card

    console.log(myPlayer)
    console.log(oppPlayers)
    console.log(bingoCard)

    // 내 정보
    const myRecord = `${myPlayer.record.win}승 ${myPlayer.record.lose}패`
    initializeOwnProfile(myPlayer.nickname, myRecord, myPlayer.profile_img)
    displayMyBoard('.user .bingo-board', bingoCard);
    myBingoCardCells = document.querySelectorAll(".user .bingo-board .cell")

    // 상대 플레이어들 정보
    for(let i=0; i<oppPlayers.length; i++){
        let oppPlayer = oppPlayers[i]
        const oppRecord = `${oppPlayer.record.win}승 ${oppPlayer.record.lose}패`
        initializeOpponentProfile(oppPlayer.nickname, oppRecord, oppPlayer.profile_img, i)
        displayOppBoard('.opponent .bingo-board', i, oppPlayer.id);
    }
})

// 랜덤 숫자 발표
// 내 빙고판에 빙고 체크
socket.on("generateRandomNumber", function(data) {
    if(!gameOver){
        console.log(data)
        const ball = data.num
        let ballColor = getRandomColor()
        displayBall('.ball-container', ball, ballColor);
        displayBall('.recent-balls', ball, ballColor);
    
        if(data.isChecked){
            checkBingo(data.x, data.y, myBingoCardCells)
        }
    }
})

// 상대방 빙고판에 빙고 체크
socket.on("oppCheckBingoCell", function(data) {
    console.log(data)
    let selector = "#bingo-board-"+data.playerId + " .cell"
    let oppBingoCardCells = document.querySelectorAll(selector)

    checkBingo(data.x, data.y, oppBingoCardCells)
})

// 빙고 버튼 클릭
function clickBingoButton() {
    console.log("빙고!!!!!!!");

    const data = {
        "gameRoomNum": gameRoomNum,
        "nickname": nickname
    };

    socket.emit("bingo", data);
}

// 빙고버튼 클릭 결과
socket.on("bingoGameResult", function(data) {
    console.log(data);
    const bingoButton = document.getElementById("my-bingo-button")

    if (data.result === false) {
        bingoButton.disabled = true; // 버튼 비활성화
        setTimeout(function() {
            bingoButton.disabled = false; // 5초 후 버튼 활성화
        }, 5000);
    }
});

// 게임 종료
socket.on("bingoGameOver", function(data) {
    gameOver = true

    const isWin = data.isWin

    openModal(isWin)
})

// 생성된 숫자가 내 빙고판에 있으면 체크하기
function checkBingo(x, y, bingoCardCells){
    const location = Number(x * 5) + Number(y)
    // console.log("체크! " + location)
    
    const cell = bingoCardCells[location]
    cell.classList.add('called');

    setTimeout(() => {
        cell.style.backgroundColor = '#5472b8';
        cell.style.color = '#ffffff';
    }, 2000);
}


function initializeOwnProfile(nickname, record, profile_img) {
    const ownProfileBox = document.querySelector('.user .profile-section');
    ownProfileBox.innerHTML = `
    <div class="profile-section-picture">
        <img class="profile-image" src=${profile_img} alt="프로필 이미지">
    </div>
    <div class="profile-info">
        <h2 class="nickname">${nickname}</h2>
        <h3>전적</h3>
        <p class="record">${record}</p>
    </div>
`;
}

function initializeOpponentProfile(nickname, record, profile_img, i) {
    const opponentProfileBox = document.querySelectorAll('.opponent .profile-section');
    opponentProfileBox.item(i).innerHTML = `
    <div class="profile-section-picture">
        <img class="profile-image" src=${profile_img} alt="프로필 이미지">
    </div>
    <div class="profile-info">
        <h2 class="nickname">${nickname}</h2>
    </div>
`;
}

// 내 빙고판 그리기
function displayMyBoard(selector, board) {
    let container = document.querySelector(selector);

    container.textContent = ''; // clear existing contents

    for (let row of board) {
        for (let num of row) {
            let cell = document.createElement('div');
            cell.classList.add('cell');
            cell.textContent = num;
            container.appendChild(cell);
        }
    }
}

// 상대방 빙고판 그리기
function displayOppBoard(selector, num, playerId) {
    let containers = document.querySelectorAll(selector);
    
    let container = containers.item(num)
    container.id = 'bingo-board-' + playerId;

    container.textContent = ''; // clear existing contents

    for(let i=0; i<5; i++){
        for(let j=0; j<5; j++){
            let cell = document.createElement('div');
            cell.classList.add('cell');
            container.appendChild(cell);
        }
    }
}

function displayBall(selector, ball, color) {
    let container = document.querySelector(selector);
    let ballElement = document.createElement('div');
    ballElement.classList.add('ball');
    ballElement.textContent = ball;

    // Give the ball a shape with a background color
    ballElement.style.backgroundColor = color;

    if (selector === '.recent-balls') {
        if (container.childElementCount >= MAX_BALLS_DISPLAYED) {
            setTimeout(() => {  // Add a delay before removing the oldest ball
                container.removeChild(container.lastElementChild);
            }, 2005);  // Delay time in milliseconds (505ms = 0.505s)
        }
        setTimeout(() => {
            ballElement.style.animation = "slideDown 0.5s ease-out";  // Make the animation faster
            container.insertBefore(ballElement, container.firstChild);
        }, 2000)
        
    } else {
        // If the container is for the ball-container, just replace the existing ball
        container.innerHTML = "";
        container.appendChild(ballElement);
        ballElement.style.animation = "scaleUp 2s ease-out";
    }
}

function getRandomColor() {
    const colors = ["#b5c4e0", "#879ebf", "#d6d1e0", "#aebfd9", "#c4ccd9"]; // Change these to your preferred colors
    return colors[Math.floor(Math.random() * colors.length)];
}

function openModal(isUserVictory) {
    let modal = document.getElementById("gameOverModal");
    let modalHeader = document.getElementById("gameOverModalHeader");
    let modalBody = document.getElementById("gameOverModalBody");

    modal.style.display = "block";

    if (isUserVictory) {
        modalHeader.textContent = "승리";
        modalBody.textContent = "오늘의 행운아는 바로 당신!";
    } else {
        modalHeader.textContent = "패배";
        modalBody.textContent = "괜찮아요, 다음에 이기면 되죠!";
    }
}

function moveMypage(){
    window.location.href = '/mypage';
}

// 페이지가 로드될 때 이벤트 리스너를 등록합니다.
window.onload = function() {
    // 페이지가 새로고침될 때 발생하는 이벤트 리스너를 등록합니다.
    if (pageStatus == GAME_PAGE){
        window.addEventListener('beforeunload', function(event) {
            // 이벤트가 발생할 때 Alert 창을 띄웁니다.
            event.preventDefault(); // 이벤트 기본 동작을 막습니다.
            event.returnValue = ''; // 이벤트 리스너에서 반환 값을 빈 문자열로 설정하여 브라우저가 경고 창을 표시하도록 합니다.
            alert('페이지를 떠나시겠습니까?');
        });
    }
};