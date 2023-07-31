console.log("대기방 입장")

let userNickname = localStorage.getItem('nickname');  // Retrieve nickname from local storage
let socket = io();

let gameRoomNum;
let gameMatchNum;

resetSID()
getUserInfo()
waiting()

function resetSID(){
    const data = {
        "nickname" : userNickname
    }
    
    socket.emit("resetSID", data)
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

// 게임 시작버튼 클릭
function startGame(){
    const data = {"game_match_num": gameMatchNum}
    socket.emit("startGame", data)
}

socket.on("moveGamePage", (data) => {
    localStorage.setItem("gameRoomNum", data.gameRoomNum)

    startCountdown();
    setTimeout(() => {changePageFromWaitingToGame();}, 3000);
    
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
    let body = document.getElementsByTagName("body");
    console.log(body);

    body.innerHTML = ""

    body.innerHTML = `
    <div id="game">
        <div id="game-container">
            <div id="temp">
                <!-- Section 1: Opponent's profile and bingo board -->
                <div class="player-section-1 opponent">
                    <div class="player-section opponent">
                        <div class="profile-section">
                            <!-- Profile related code here -->
                            <div class="profile-section-picture">
                                <!-- Profile picture will go here -->
                            </div>
                            <div class="nickname"></div>
                            <div class="record"></div>
                        </div>
                        <div class="bingo-container">
                            <div class="bingo-board">
                                <!-- Bingo board will be filled dynamically -->
                            </div>
                            <!-- <button disabled class="bingo-button opponent-button" disabled>B<br>I<br>N<br>G<br>O</button> -->
                        </div>
                    </div>
                    <div class="player-section opponent">
                        <div class="profile-section">
                            <!-- Profile related code here -->
                            <div class="profile-section-picture">
                                <!-- Profile picture will go here -->
                            </div>
                            <div class="nickname"></div>
                            <div class="record"></div>
                        </div>
                        <div class="bingo-container">
                            <div class="bingo-board">
                                <!-- Bingo board will be filled dynamically -->
                            </div>
                            <!-- <button disabled class="bingo-button opponent-button" disabled>B<br>I<br>N<br>G<br>O</button> -->
                        </div>
                    </div>
                    <div class="player-section opponent">
                        <div class="profile-section">
                            <!-- Profile related code here -->
                            <div class="profile-section-picture">
                                <!-- Profile picture will go here -->
                            </div>
                            <div class="nickname"></div>
                            <div class="record"></div>
                        </div>
                        <div class="bingo-container">
                            <div class="bingo-board">
                                <!-- Bingo board will be filled dynamically -->
                            </div>
                            <!-- <button disabled class="bingo-button opponent-button" disabled>B<br>I<br>N<br>G<br>O</button> -->
                        </div>
                    </div>
                </div>


                <!-- Ball drawing section -->
                <div id="ball-drawing-section">
                    <div class="ball-container">
                        <!-- Balls will be filled dynamically -->
                    </div>
                    <div class="recent-balls">
                        <!-- Recent balls will be filled dynamically -->
                    </div>
                </div>

                
                <!-- Section 2: Opponent's profile and bingo board -->
                <div class="player-section-2 opponent">
                    <div class="player-section opponent">
                        <div class="bingo-container">
                            <div class="bingo-board">
                                <!-- Bingo board will be filled dynamically -->
                            </div>
                            <!-- <button disabled class="bingo-button opponent-button" disabled>B<br>I<br>N<br>G<br>O</button> -->
                        </div>
                        <div class="profile-section">
                            <!-- Profile related code here -->
                            <div class="profile-section-picture">
                                <!-- Profile picture will go here -->
                            </div>
                            <div class="nickname"></div>
                            <div class="record"></div>
                        </div>
                    </div>
                    <div class="player-section opponent">
                        <div class="bingo-container">
                            <div class="bingo-board">
                                <!-- Bingo board will be filled dynamically -->
                            </div>
                            <!-- <button disabled class="bingo-button opponent-button" disabled>B<br>I<br>N<br>G<br>O</button> -->
                        </div>
                        <div class="profile-section">
                            <!-- Profile related code here -->
                            <div class="profile-section-picture">
                                <!-- Profile picture will go here -->
                            </div>
                            <div class="nickname"></div>
                            <div class="record"></div>
                        </div>
                    </div>
                    <div class="player-section opponent">
                        <div class="bingo-container">
                            <div class="bingo-board">
                                <!-- Bingo board will be filled dynamically -->
                            </div>
                            <!-- <button disabled class="bingo-button opponent-button" disabled>B<br>I<br>N<br>G<br>O</button> -->
                        </div>
                        <div class="profile-section">
                            <!-- Profile related code here -->
                            <div class="profile-section-picture">
                                <!-- Profile picture will go here -->
                            </div>
                            <div class="nickname"></div>
                            <div class="record"></div>
                        </div>
                    </div>
                </div>
            </div>
            

            <!-- Section 3: User's profile and bingo board -->
            <div class="player-section-3 user">
                <div class="bingo-container">
                    <div class="bingo-board">
                        <!-- Bingo board will be filled dynamically -->
                    </div>
                    <button id="my-bingo-button" class="bingo-button user-button" onclick="clickBingoButton()">B<br>I<br>N<br>G<br>O</button>
                </div>
                <div class="profile-section">
                    <!-- Profile related code here -->
                    <div class="profile-section-picture">
                        <!-- Profile picture will go here -->
                    </div>
                    <div class="nickname"></div>
                    <div class="record"></div>
                </div>
            </div>
            
            <div id="gameOverModal">
                <div id="gameOverModalContent">
                    <div class="modal-header" id="gameOverModalHeader">
                        <!-- Victory or Defeat will be inserted here -->
                    </div>
                    <div class="modal-body" id="gameOverModalBody">
                        <!-- A custom message will be inserted here -->
                    </div>
                    <div class="modal-footer">
                        <button id="gameOverModalButton" onclick="moveMypage()">마이페이지로 돌아가기</button>
                    </div>
                </div>
            </div> 
            
        </div>
    </div>
    `
}