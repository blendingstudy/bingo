// const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

// // Variables
// let countdownTime = 5; // 5 seconds countdown
// let countdownInterval = null;
// const readyButton = document.getElementById('ready-button');
// const countdownBar = document.getElementById('countdown-bar');
// const ownProfileBox = document.querySelector('.own-profile');
// const opponentProfileBox = document.querySelector('.opponent-profile');

// // Fetch own profile from local storage
// let userNickname = localStorage.getItem('nickname');
// initializeOwnProfile(userNickname, '0승 0패');

// // Fetch own record from server
// socket.emit('fetchRecord');

// socket.on('fetchRecordResponse', function(data) {
//     let win = data.record && data.record.win ? data.record.win : 0;
//     let lose = data.record && data.record.lose ? data.record.lose : 0;
//     let record = win + '승 ' + lose + '패';
//     initializeOwnProfile(userNickname, record);
// });

// // Join the matchmaking queue
// socket.emit('joinQueue');

// socket.on('matchFound', function(data) {
//     // Initialize opponent's profile
//     let win = data.record && data.record.win ? data.record.win : 0;
//     let lose = data.record && data.record.lose ? data.record.lose : 0;
//     let record = win + '승 ' + lose + '패';
//     initializeOpponentProfile(data.nickname, record);

//     // Start the countdown
//     startCountdown();
// });

// readyButton.addEventListener('click', () => {
//     // Stop the countdown
//     clearInterval(countdownInterval);
    
//     // Change the button state
//     readyButton.textContent = '준비완료';
//     readyButton.disabled = true;

//     // Notify the server that the user is ready to play
//     socket.emit('ready');
// });

// socket.on('startGame', function() {
//     window.location.href = '/game';
// });

// // Functions
// function initializeOwnProfile(nickname, record) {
//     ownProfileBox.innerHTML = generateProfileHTML(nickname, record);
// }

// function initializeOpponentProfile(nickname, record) {
//     // Replace the placeholder with the actual profile
//     opponentProfileBox.innerHTML = generateProfileHTML(nickname, record);
// }

// function generateProfileHTML(nickname, record) {
//     return `
//         <div class="profile-picture">
//             <!-- Profile picture will go here -->
//         </div>
//         <div class="profile-info">
//             <h2>${nickname}</h2>
//             <h3>전적</h3>
//             <p>${record}</p>
//         </div>
//     `;
// }

// function startCountdown() {
//     countdownInterval = setInterval(() => {
//         countdownTime -= 1;

//         // Update the countdown bar
//         countdownBar.style.width = `${(countdownTime / 5) * 100}%`;

//         // End of countdown
//         if (countdownTime === 0) {
//             clearInterval(countdownInterval);

//             // Notify the server that the user failed to ready up in time.
//             socket.emit('notReady');
//             // The server should handle matchmaking again.
//         }
//     }, 1000);
// }

console.log("대기방 입장")

let userNickname = localStorage.getItem('nickname');  // Retrieve nickname from local storage
let socket = io();

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

    const url = "http://localhost:5000/ready?nickname=" + userNickname 

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
        })
        .catch(error => {
            // 에러 처리
            alert("유저정보 요청 실패")
        });
}

socket.on('startGame', function() {
    // 상대방 화면에 표시
    // 3초후 게임 시작
    window.location.href = '/game';
});