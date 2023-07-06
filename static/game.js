const MAX_NUM = 99;
const BINGO_SIZE = 5;
const MAX_BALLS_DISPLAYED = 5;
const BOARD_SIZE = BINGO_SIZE * BINGO_SIZE;
const MIN_BINGO_LINES = 2;

let myBingoCardCells;
let oppBingoCardCells;
let gameOver = false;

const bingoButton = document.getElementById("my-bingo-button")
console.log(bingoButton)

const socket = io() // 웹소켓 초기화
const gameRoomNum = Number(localStorage.getItem("gameRoomNum")) // 게임방 번호
const nickname = localStorage.getItem("nickname") // 닉네임

console.log("게임방 번호: " + gameRoomNum)
console.log("닉네임: " + nickname)

// sid 다시 세팅
resetSID()
// 게임방 입장 알림
enterGameRoom()

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
    const oppPlayer = data.opp_player
    const bingoCard = data.bingo_card

    console.log(myPlayer)
    console.log(oppPlayer)
    console.log(bingoCard)

    const myRecord = `${myPlayer.record.win}승 ${myPlayer.record.lose}패`
    initializeOwnProfile(myPlayer.nickname, myRecord)

    const oppRecord = `${oppPlayer.record.win}승 ${oppPlayer.record.lose}패`
    initializeOpponentProfile(oppPlayer.nickname, oppRecord)

    displayBoard('.user .bingo-board', bingoCard);
    displayBoard('.opponent .bingo-board', null);

    myBingoCardCells = document.querySelectorAll(".user .bingo-board .cell")
    oppBingoCardCells = document.querySelectorAll(".opponent .bingo-board .cell")
    // console.log(myBingoCardCells)
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
    // console.log(data)
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

    if (data.result === false) {
        bingoButton.disabled = true; // 버튼 비활성화
        bingoButton.classList.add('disabled');
        setTimeout(function() {
            bingoButton.disabled = false; // 5초 후 버튼 활성화
            bingoButton.classList.remove('disabled');
        }, 5000);
    }
});

// 게임 종료
socket.on("bingoGameOver", function(data) {
    gameOver = true

    console.log(data)

    const isWin = data.isWin

    openModal(isWin)
})



function checkBingo(x, y, bingoCardCells){
    const location = Number(x * 5) + Number(y)
    // console.log("체크! " + location)
    
    // console.log(bingoCardCells[location])
    const cell = bingoCardCells[location]
    cell.classList.add('called');
}


function initializeOwnProfile(nickname, record) {
    const ownProfileBox = document.querySelector('.user .profile-section1');
    ownProfileBox.innerHTML = generateProfileHTML(nickname, record);
}

function initializeOpponentProfile(nickname, record) {
    const opponentProfileBox = document.querySelector('.opponent .profile-section1');
    opponentProfileBox.innerHTML = generateProfileHTML(nickname, record);
}

function generateProfileHTML(nickname, record) {
    return `
        <div class="profile-section1-picture">
            <!-- Profile picture will go here -->
        </div>
        <div class="profile-info">
            <h2 class="nickname">${nickname}</h2>
            <h3>전적</h3>
            <p class="record">${record}</p>
        </div>
    `;
}

function displayBoard(selector, board) {
    let container = document.querySelector(selector);
    container.textContent = ''; // clear existing contents

    if(board == null) {
        for(let i=0; i<5; i++){

            for(let j=0; j<5; j++){
                let cell = document.createElement('div');
                cell.classList.add('cell');
                container.appendChild(cell);
            }
        }
    }
    else{
        for (let row of board) {
            for (let num of row) {
                let cell = document.createElement('div');
                cell.classList.add('cell');
                cell.textContent = num;
                container.appendChild(cell);
            }
        }
    }
}

function displayBall(selector, ball, color) {
    let container = document.querySelector(selector);
    let ballElement = document.createElement('div');
    ballElement.classList.add('ball');
    ballElement.textContent = ball;

    // Give the ball a shape with a background color
    ballElement.style.width = "40px";
    ballElement.style.height = "40px";
    ballElement.style.borderRadius = "50%";
    ballElement.style.display = "inline-block";
    ballElement.style.textAlign = "center";
    ballElement.style.lineHeight = "40px";
    ballElement.style.backgroundColor = color;

    if (selector === '.recent-balls') {
        if (container.childElementCount === MAX_BALLS_DISPLAYED) {
            setTimeout(() => {  // Add a delay before removing the oldest ball
                container.removeChild(container.lastElementChild);
            }, 505);  // Delay time in milliseconds (505ms = 0.505s)
        }
        ballElement.style.animation = "rollIn 0.5s ease-out";  // Make the animation faster
        container.insertBefore(ballElement, container.firstChild);
    } else {
        // If the container is for the ball-container, just replace the existing ball
        container.innerHTML = "";
        container.appendChild(ballElement);
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

// function checkBingo(container) {
//     let board = [...container.querySelectorAll('.cell')].map(cell => cell.classList.contains('called'));
//     let bingoCount = 0;
//     for (let i = 0; i < BINGO_SIZE; i++) {
//         if ([...Array(BINGO_SIZE)].every((_, j) => board[i * BINGO_SIZE + j])) bingoCount++; // check row
//         if ([...Array(BINGO_SIZE)].every((_, j) => board[i + j * BINGO_SIZE])) bingoCount++; // check column
//     }
//     if ([...Array(BINGO_SIZE)].every((_, i) => board[i * (BINGO_SIZE + 1)])) bingoCount++; // check main diagonal
//     if ([...Array(BINGO_SIZE)].every((_, i) => board[(i + 1) * (BINGO_SIZE - 1)])) bingoCount++; // check other diagonal

//     return bingoCount >= MIN_BINGO_LINES;
// }

// function drawBall() {
//     if (nextBallIndex < balls.length) {
//         let ball = balls[nextBallIndex++];
//         document.querySelectorAll('.bingo-board .cell').forEach(cell => {
//             if (cell.textContent == ball) {
//                 cell.classList.add('called');
//             }
//         });
//         let ballColor = getRandomColor();
//         displayBall('.ball-container', ball, ballColor);
//         displayBall('.recent-balls', ball, ballColor);
//         document.querySelectorAll('.bingo-button').forEach(button => {
//             button.disabled = !checkBingo(button.closest('.player-section').querySelector('.bingo-board'));
//             button.style.backgroundColor = button.disabled ? '#ccc' : '#2c4681';
//         });
//         if (!gameOver) {
//             setTimeout(drawBall, 2000);
//         }
//     }
// }


// 모든 플레이어가 입장하면 그때부터 게임 시작.

// document.addEventListener('DOMContentLoaded', function () {
//     // Constants
//     const MAX_NUM = 30;
//     const BINGO_SIZE = 5;
//     const MAX_BALLS_DISPLAYED = 5;
//     const BOARD_SIZE = BINGO_SIZE * BINGO_SIZE;
//     const MIN_BINGO_LINES = 2;

//     // Server-side: User and opponent profile data will be fetched from the server.
//     let user = { nickname: 'Nickname', wins: 0, losses: 0 };
//     let opponent = { nickname: 'Opponent', wins: 0, losses: 0 };

//     // Server-side: Initial bingo boards will be generated on the server.
//     let userBoard = generateBoard();
//     let opponentBoard = generateBoard();

//     // Server-side: The order of the drawn balls will be determined by the server.
//     let balls = shuffle([...Array(MAX_NUM).keys()].map(n => n + 1));

//     // Server-side: The server will maintain the index of the next ball to be drawn.
//     let nextBallIndex = 0;

//     // Server-side: The server will maintain the state of the game (if it's over or not).
//     let gameOver = false;

//     // Socket IO setup
//     var socket = io();

//     // Fetch nickname and record from server
//     socket.on('fetchNicknameResponse', function(data) {
//         user.nickname = data.nickname;
//         initializeOwnProfile(user.nickname, `${user.wins}승 ${user.losses}패`);
//     });

//     socket.on('fetchRecordResponse', function(data) {
//         user.wins = data.record.win;
//         user.losses = data.record.lose;
//         initializeOwnProfile(user.nickname, `${user.wins}승 ${user.losses}패`);
//     });

//     // Initialize game
//     initializeOpponentProfile(opponent.nickname, `${opponent.wins}승 ${opponent.losses}패`);
//     displayBoard('.user .bingo-board', userBoard);
//     displayBoard('.opponent .bingo-board', opponentBoard);
//     setTimeout(drawBall, 2000);

//     // Event listener for bingo buttons
//     document.querySelectorAll('.user-button').forEach(button =>
//         button.addEventListener('click', function () {
//             if (!gameOver && checkBingo(this.closest('.player-section').querySelector('.bingo-board'))) {
//                 gameOver = true;
//                 let winner = this.closest('.player-section').querySelector('.profile-section1 .nickname').textContent;
//                 openModal(winner === user.nickname);
//                 socket.emit('gameOver', {'isUserVictory': winner === user.nickname});  // Send the result to the server
//             }
//         })
//     );

//     // Function definitions
//     function initializeOwnProfile(nickname, record) {
//         const ownProfileBox = document.querySelector('.user .profile-section1');
//         ownProfileBox.innerHTML = generateProfileHTML(nickname, record);
//     }

//     function initializeOpponentProfile(nickname, record) {
//         const opponentProfileBox = document.querySelector('.opponent .profile-section1');
//         opponentProfileBox.innerHTML = generateProfileHTML(nickname, record);
//     }

//     function generateProfileHTML(nickname, record) {
//         return `
//             <div class="profile-section1-picture">
//                 <!-- Profile picture will go here -->
//             </div>
//             <div class="profile-info">
//                 <h2 class="nickname">${nickname}</h2>
//                 <h3>전적</h3>
//                 <p class="record">${record}</p>
//             </div>
//         `;
//     }

//     // 여기!! 여기가 빙고판 입력하는데임!
//     function displayBoard(selector, board) {
//         let container = document.querySelector(selector);
//         container.textContent = ''; // clear existing contents
//         for (let row of board) {
//             for (let num of row) {
//                 let cell = document.createElement('div');
//                 cell.classList.add('cell');
//                 cell.textContent = num;
//                 container.appendChild(cell);
//             }
//         }
//     }

//     function drawBall() {
//         if (nextBallIndex < balls.length) {
//             let ball = balls[nextBallIndex++];
//             document.querySelectorAll('.bingo-board .cell').forEach(cell => {
//                 if (cell.textContent == ball) {
//                     cell.classList.add('called');
//                 }
//             });
//             let ballColor = getRandomColor();
//             displayBall('.ball-container', ball, ballColor);
//             displayBall('.recent-balls', ball, ballColor);
//             document.querySelectorAll('.bingo-button').forEach(button => {
//                 button.disabled = !checkBingo(button.closest('.player-section').querySelector('.bingo-board'));
//                 button.style.backgroundColor = button.disabled ? '#ccc' : '#2c4681';
//             });
//             if (!gameOver) {
//                 setTimeout(drawBall, 2000);
//             }
//         }
//     }

//     function displayBall(selector, ball, color) {
//         let container = document.querySelector(selector);
//         let ballElement = document.createElement('div');
//         ballElement.classList.add('ball');
//         ballElement.textContent = ball;

//         // Give the ball a shape with a background color
//         ballElement.style.width = "40px";
//         ballElement.style.height = "40px";
//         ballElement.style.borderRadius = "50%";
//         ballElement.style.display = "inline-block";
//         ballElement.style.textAlign = "center";
//         ballElement.style.lineHeight = "40px";
//         ballElement.style.backgroundColor = color;

//         if (selector === '.recent-balls') {
//             if (container.childElementCount === MAX_BALLS_DISPLAYED) {
//                 setTimeout(() => {  // Add a delay before removing the oldest ball
//                     container.removeChild(container.lastElementChild);
//                 }, 505);  // Delay time in milliseconds (505ms = 0.505s)
//             }
//             ballElement.style.animation = "rollIn 0.5s ease-out";  // Make the animation faster
//             container.insertBefore(ballElement, container.firstChild);
//         } else {
//             // If the container is for the ball-container, just replace the existing ball
//             container.innerHTML = "";
//             container.appendChild(ballElement);
//         }
//     }

//     function getRandomColor() {
//         const colors = ["#b5c4e0", "#879ebf", "#d6d1e0", "#aebfd9", "#c4ccd9"]; // Change these to your preferred colors
//         return colors[Math.floor(Math.random() * colors.length)];
//     }

//     function generateBoard() {
//         let nums = shuffle([...Array(MAX_NUM).keys()].map(n => n + 1)).slice(0, BOARD_SIZE);
//         return [...Array(BINGO_SIZE)].map((_, i) => nums.slice(i * BINGO_SIZE, (i + 1) * BINGO_SIZE));
//     }

//     function shuffle(array) {
//         let currentIndex = array.length, temporaryValue, randomIndex;
//         while (0 !== currentIndex) {
//             randomIndex = Math.floor(Math.random() * currentIndex);
//             currentIndex -= 1;
//             temporaryValue = array[currentIndex];
//             array[currentIndex] = array[randomIndex];
//             array[randomIndex] = temporaryValue;
//         }
//         return array;
//     }
    
//     function checkBingo(container) {
//         let board = [...container.querySelectorAll('.cell')].map(cell => cell.classList.contains('called'));
//         let bingoCount = 0;
//         for (let i = 0; i < BINGO_SIZE; i++) {
//             if ([...Array(BINGO_SIZE)].every((_, j) => board[i * BINGO_SIZE + j])) bingoCount++; // check row
//             if ([...Array(BINGO_SIZE)].every((_, j) => board[i + j * BINGO_SIZE])) bingoCount++; // check column
//         }
//         if ([...Array(BINGO_SIZE)].every((_, i) => board[i * (BINGO_SIZE + 1)])) bingoCount++; // check main diagonal
//         if ([...Array(BINGO_SIZE)].every((_, i) => board[(i + 1) * (BINGO_SIZE - 1)])) bingoCount++; // check other diagonal

//         return bingoCount >= MIN_BINGO_LINES;
//     }

//     // Socket IO setup
//     var socket = io();

//     // Event listener for bingo buttons
//     document.querySelectorAll('.user-button').forEach(button =>
//         button.addEventListener('click', function () {
//             if (!gameOver && checkBingo(this.closest('.player-section').querySelector('.bingo-board'))) {
//                 gameOver = true;
//                 let winner = this.closest('.player-section').querySelector('.profile-section1 .nickname').textContent;
//                 openModal(winner === user.nickname);
//                 socket.emit('gameOver', { 'isUserVictory': winner === user.nickname });  // Send the result to the server
//             }
//         })
//     );

//     // Fetch nickname and record from server
//     socket.on('fetchNicknameResponse', function (data) {
//         user.nickname = data.nickname;
//         initializeOwnProfile(user.nickname, `${user.wins}승 ${user.losses}패`);
//     });

//     socket.on('fetchRecordResponse', function (data) {
//         user.wins = data.record.win;
//         user.losses = data.record.lose;
//         initializeOwnProfile(user.nickname, `${user.wins}승 ${user.losses}패`);
//     });

//     function openModal(isUserVictory) {
//         let modal = document.getElementById("gameOverModal");
//         let modalHeader = document.getElementById("gameOverModalHeader");
//         let modalBody = document.getElementById("gameOverModalBody");

//         modal.style.display = "block";

//         if (isUserVictory) {
//             modalHeader.textContent = "승리";
//             modalBody.textContent = "오늘의 행운아는 바로 당신!";
//         } else {
//             modalHeader.textContent = "패배";
//             modalBody.textContent = "괜찮아요, 다음에 이기면 되죠!";
//         }
//     }

//     // On page load, fetch the nickname and record from the server
//     socket.emit('fetchNickname');
//     socket.emit('fetchRecord');
// });

// document.getElementById("gameOverModalButton").addEventListener('click', function () {
//     // Redirect to mypage.html
//     window.location.href = "/mypage";
// });
