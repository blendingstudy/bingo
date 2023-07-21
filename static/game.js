const socket = io() // 웹소켓 초기화
const MAX_BALLS_DISPLAYED = 6;
const gameRoomNum = Number(localStorage.getItem("gameRoomNum")) // 게임방 번호
const nickname = localStorage.getItem("nickname") // 닉네임
let myBingoCardCells;
let gameOver = false;

console.log("게임방 번호: " + gameRoomNum)
console.log("닉네임: " + nickname)

resetSID()
enterGameRoom()
  
// sid 다시 세팅
function resetSID(){
    const data = {
        "nickname" : nickname
    }
    
    socket.emit("resetSID", data)
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
    initializeOwnProfile(myPlayer.nickname, myRecord)
    displayMyBoard('.user .bingo-board', bingoCard);
    myBingoCardCells = document.querySelectorAll(".user .bingo-board .cell")

    // 상대 플레이어들 정보
    for(let i=0; i<oppPlayers.length; i++){
        let oppPlayer = oppPlayers[i]
        const oppRecord = `${oppPlayer.record.win}승 ${oppPlayer.record.lose}패`
        initializeOpponentProfile(oppPlayer.nickname, oppRecord, i)
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


function initializeOwnProfile(nickname, record) {
    const ownProfileBox = document.querySelector('.user .profile-section');
    ownProfileBox.innerHTML = `
    <div class="profile-section-picture">
        <!-- Profile picture will go here -->
    </div>
    <div class="profile-info">
        <h2 class="nickname">${nickname}</h2>
        <h3>전적</h3>
        <p class="record">${record}</p>
    </div>
`;
}

function initializeOpponentProfile(nickname, record, i) {
    const opponentProfileBox = document.querySelectorAll('.opponent .profile-section');
    opponentProfileBox.item(i).innerHTML = `
    <div class="profile-section-picture">
        <!-- Profile picture will go here -->
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