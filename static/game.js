const MAX_BALLS_DISPLAYED = 6;
const MAX_TICKET_NUM = 10

const socket = io() // 웹소켓 초기화

const nickname = localStorage.getItem("nickname") // 닉네임
let gameRoomNum = Number(localStorage.getItem("gameRoomNum")); // 게임매칭 번호
let gameOver = false;
let opp_player_idx = 0
let oppPlayerAndBingoBoardMatching = {} // 플레이어id : 빙고판 번호

const tickets = document.getElementsByClassName('ticket'); // 티켓
let myBingoBoard; // 내 빙고판
let oppPlayerBingoBoards; // 상대 빙고판들

const countDownBarSection = document.getElementById("count-down-section") // 카운트다운바 섹션
const ballSection = document.getElementById("ball-drawing-section") // 공 섹션
const ticketSection = document.getElementById("ticket-list-section"); // 티켓 섹션

console.log("닉네임: " + nickname)
console.log("게임룸 넘버: " + gameRoomNum)

setSID();

getUserInfo();

enterGameRoom();

addClickEventToTicket();

// ---티켓 관련 소켓 코드 시작---

// 티켓 구매 성공
socket.on("successTicketBuy", (data) => {
    console.log(data)

    const ticket = tickets.item(data.ticketId)
    
    ticket.classList.add('sold');
    ticket.disabled = true;

    const purchaseTicketContainer = document.getElementById("purchase-ticket-container");
    let ticketElement = document.createElement("img");
    ticketElement.classList.add("purchase-ticket");
    ticketElement.src = "/img/ticket"
    purchaseTicketContainer.appendChild(ticketElement);
})

// 티켓 구매 실패
socket.on("failTicketBuy", () => {
    alert("티켓 구매 실패!")
})

// 타 플레이어가 티켓 구매 성공
socket.on("ticketSold", (data) => {
    console.log(data)

    const ticket = tickets.item(data.ticketId)
    
    ticket.classList.add('sold');
    ticket.disabled = true;
})

// 판매된 티켓 리스트
socket.on("soldTicketList", (data) => {
    const soldTicketList = data.ticket_list

    for(let i=0; i<MAX_TICKET_NUM; i++){
        if(soldTicketList[i]){ // 판매된 티켓이면
            const ticket = tickets.item(i)
            ticket.classList.add('sold');
            ticket.disabled = true;
        }
    }
})

// ---티켓 관련 소켓 코드 끝---

// ---새로운 플레이어가 들어왔을 때에 관한 소켓 코드 시작---

// 새로운 플레이어 정보
socket.on('newPlayerMatched', function(data) {
    console.log(data)

    // 상대 플레이어 화면에 표시
    opp_player = document.getElementsByClassName("player opponent")
    opp_player.item(data.idx-2).innerHTML = `
        <div class="profile-section"> 
            <div class="profile-img">
                <img class="profile-image" src=${data.oppProfileImg} alt="프로필 이미지">
            </div>
            <div class="nickname">${data.oppNickname}</div>
        </div>
        <div class="bingo-container">
            <div class="bingo-board">
            </div>
        </div>
    `;
    opp_player_idx++
})

// 새로운 플레이어에게 이전 매칭된 플레이어의 정보 전달
socket.on('MatchedGamePlayerInfo', function(data) {

    console.log(data)

    // 상대 플레이어 화면에 표시
    oppPlayersElement = document.getElementsByClassName("player opponent")

    const oppPlayersInfo = data.oppPlayersInfo
    for(let i=0; i<oppPlayersInfo.length; i++){
        let oppPlayerInfo = oppPlayersInfo[i];
        let oppPlayerElement = oppPlayersElement.item(i);

        oppPlayerElement.innerHTML = `
            <div class="profile-section"> 
                <div class="profile-img">
                    <img class="profile-image" src=${oppPlayerInfo.oppProfileImg} alt="프로필 이미지">
                </div>
                <div class="nickname">${oppPlayerInfo.oppNickname}</div>
            </div>
            <div class="bingo-container">
                <div class="bingo-board">
                </div>
            </div>
        `;
    }

    opp_player_idx = oppPlayersInfo.length
});

// ---새로운 플레이어가 들어왔을 때에 관한 소켓 코드 끝---

// 카운트 다운
socket.on("gameCountDownStart", () => {

    // 티켓 숨기기
    ticketSection.style.display = "none";

    console.log("카운트다운 start")

    countDownBarSection.style.display = "flex"

    startCountdown();
})

// 게임 시작 세팅
// 빙고판 세팅세팅
socket.on("gameStartInfo", (data) => {
    countDownBarSection.style.display = "none";
    ballSection.style.display = "flex";

    console.log(data)

    myBingoCards = data.myBingoCard
    oppPlayersInfo = data.oppInfo

    setMyBingoCard(myBingoCards);
    setOppPlayersBingoCard(oppPlayersInfo);
})

// ---숫자 발표와 체크에 관한 소켓 코드 시작---

// 랜덤 숫자 발표
socket.on("announceRandomNumber", (data) => {
    const ball_num = data.num
    let ballColor = getRandomColor()
    displayBall('.ball-container', ball_num, ballColor);
    displayBall('.recent-balls', ball_num, ballColor);
})


// 랜덤 숫자 일치!
socket.on("checkRandomNumber", (data) => {
    console.log(data)

    const x = data.x;
    const y = data.y;

    cards = myBingoBoard.childNodes;

    cell = cards.item(x).childNodes.item(y) //x는 카드, y는 그 카드에서 몇번째 셀인지

    cell.classList.add("check")
    setTimeout(() => { // 셀 색깔 변경
        cell.style.backgroundColor = '#5472b8';
        cell.style.color = '#ffffff';
    }, 1000);
    
})

// 상대방 랜덤 숫자 일치
socket.on("checkOppRandomNumber", (data) => {
    console.log(data)

    bingoBoardIdx = oppPlayerAndBingoBoardMatching[data.oppId]

    oppBingoBoard = oppPlayerBingoBoards.item(bingoBoardIdx);

    console.log(oppBingoBoard)

    cards = oppBingoBoard.childNodes;

    cell = cards.item(data.x).childNodes.item(data.y) //x는 카드, y는 그 카드에서 몇번째 셀인지

    cell.classList.add("check")
    setTimeout(() => { // 셀 색깔 변경
        cell.style.backgroundColor = '#5472b8';
        cell.style.color = '#ffffff';
    }, 1000);
})

// ---숫자 발표와 체크에 관한 소켓 코드 끝---

// 게임 종료
socket.on("gameOver", (data) => {
    console.log("게임 종료")
    console.log(data)
    openModal(data.winner)
})


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

// 게임룸 입장
function enterGameRoom(){
    const data = {
        "game_room_num" : gameRoomNum
    }

    console.log("게임룸 입장!")

    socket.emit("enterGameRoom", data)
}

// 티켓에 클릭 이벤트 리스너 등록
function addClickEventToTicket(){
    for(let i=0; i<tickets.length; i++){
        let ticket = tickets.item(i)
        ticket.addEventListener('click', (event) => {
            // 티켓 사기
            if(!event.target.classList.contains('sold')){
                const data = {
                    "game_room_num" : gameRoomNum,
                    "ticket_id" : i
                }
    
                socket.emit('buyTicket', data)
            } 
        });
    }
}


// 카운트다운 관련 함수
function startCountdown() {
    var bar = document.getElementById("countdown-progress");
    var height = bar.clientHeight; // 초기 너비
    var decrement = (height / 3); // 3초 동안 감소해야하는 너비의 1/3

    var timer = setInterval(function() {
        height -= decrement; // 너비 감소
        console.log(height)
        bar.style.height = height + "px"; // 너비 적용
    
        if (height <= 0) {
            clearInterval(timer); // 카운트다운 종료            
        }
    }, 1000); // 1초마다 실행
}

// 내 빙고판 세팅
function setMyBingoCard(bingoCards){
    myBingoBoard = document.querySelector("#user-player-section .bingo-board")
    myBingoBoard.textContent = ''; // clear existing contents
    console.log(myBingoBoard)

    for(let card of bingoCards){
        let bingoCard = document.createElement('div');
        bingoCard.classList.add('bingo-card');

        for(let i=0; i<5; i++){
            let cell = document.createElement('div');
            cell.classList.add('bingo-cell');
            cell.textContent = card[i];
            bingoCard.appendChild(cell);
        }

        myBingoBoard.appendChild(bingoCard)
    }
}

// 상대 플레이어 빙고판 세팅
function setOppPlayersBingoCard(oppsInfo){
    oppPlayerBingoBoards = document.querySelectorAll('#opponent-player-section .bingo-board')

    for(let i=0; i<oppsInfo.length; i++){
        const oppInfo = oppsInfo[i];

        oppPlayerAndBingoBoardMatching[oppInfo.oppId] = i

        board = oppPlayerBingoBoards.item(i)
        board.textContent = ''; // clear existing contents

        for(let card of oppInfo.oppBingoCard){
            let bingoCard = document.createElement('div');
            bingoCard.classList.add('bingo-card');

            for(let i=0; i<5; i++){
                let cell = document.createElement('div');
                cell.classList.add('bingo-cell');
                cell.textContent = card[i];
                bingoCard.appendChild(cell);
            }

            board.appendChild(bingoCard)
        }
    }
}

// 랜덤 색상 생성
function getRandomColor() {
    const colors = ["#FFB6C1", "#FFD700", "#FFFFE0", "#98FB98", "#87CEEB", "#E6E6FA", "#FFC0CB"]; // Change these to your preferred colors
    return colors[Math.floor(Math.random() * colors.length)];
}

// 화면에 공 표시
function displayBall(selector, ball, color) {
    let container = document.querySelector(selector);
    let ballElement = document.createElement('div');
    ballElement.classList.add('ball');
    ballElement.textContent = ball;

    // Give the ball a shape with a background color
    ballElement.style.backgroundColor = color;

    if (selector === '.recent-balls') {
        if (container.childElementCount >= MAX_BALLS_DISPLAYED) {
            for(let i=0; i<container.childElementCount-MAX_BALLS_DISPLAYED; i++){ // 넘치게 있었으면 다 삭제
                container.removeChild(container.lastElementChild);
            }
            setTimeout(() => {  // Add a delay before removing the oldest ball
                container.removeChild(container.lastElementChild);
            }, 2000);  // Delay time in milliseconds (505ms = 0.505s)
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


// 모달창 열기
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

// 게임 오버 이후 마이페이지 이동 버튼
document.getElementById("gameOverModalButton").addEventListener("click", () => {
    window.location.href = '/mypage';
})

