document.addEventListener('DOMContentLoaded', function () {
    // Constants
    const MAX_NUM = 30;
    const BINGO_SIZE = 5;
    const MAX_BALLS_DISPLAYED = 5;
    const BOARD_SIZE = BINGO_SIZE * BINGO_SIZE;
    const MIN_BINGO_LINES = 2;

    // Server-side: User and opponent profile data will be fetched from the server.
    let user = { nickname: 'Nickname', wins: 0, losses: 0 };
    let opponent = { nickname: 'Opponent', wins: 0, losses: 0 };

    // Server-side: Initial bingo boards will be generated on the server.
    let userBoard = generateBoard();
    let opponentBoard = generateBoard();

    // Server-side: The order of the drawn balls will be determined by the server.
    let balls = shuffle([...Array(MAX_NUM).keys()].map(n => n + 1));

    // Server-side: The server will maintain the index of the next ball to be drawn.
    let nextBallIndex = 0;

    // Server-side: The server will maintain the state of the game (if it's over or not).
    let gameOver = false;

    // Socket IO setup
    var socket = io();

    // Fetch nickname and record from server
    socket.on('fetchNicknameResponse', function(data) {
        user.nickname = data.nickname;
        initializeOwnProfile(user.nickname, `${user.wins}승 ${user.losses}패`);
    });

    socket.on('fetchRecordResponse', function(data) {
        user.wins = data.record.win;
        user.losses = data.record.lose;
        initializeOwnProfile(user.nickname, `${user.wins}승 ${user.losses}패`);
    });

    // Initialize game
    initializeOpponentProfile(opponent.nickname, `${opponent.wins}승 ${opponent.losses}패`);
    displayBoard('.user .bingo-board', userBoard);
    displayBoard('.opponent .bingo-board', opponentBoard);
    setTimeout(drawBall, 2000);

    // Event listener for bingo buttons
    document.querySelectorAll('.user-button').forEach(button =>
        button.addEventListener('click', function () {
            if (!gameOver && checkBingo(this.closest('.player-section').querySelector('.bingo-board'))) {
                gameOver = true;
                let winner = this.closest('.player-section').querySelector('.profile-section1 .nickname').textContent;
                openModal(winner === user.nickname);
                socket.emit('gameOver', {'isUserVictory': winner === user.nickname});  // Send the result to the server
            }
        })
    );

    // Function definitions
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

    // 여기!! 여기가 빙고판 입력하는데임!
    function displayBoard(selector, board) {
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

    function drawBall() {
        if (nextBallIndex < balls.length) {
            let ball = balls[nextBallIndex++];
            document.querySelectorAll('.bingo-board .cell').forEach(cell => {
                if (cell.textContent == ball) {
                    cell.classList.add('called');
                }
            });
            let ballColor = getRandomColor();
            displayBall('.ball-container', ball, ballColor);
            displayBall('.recent-balls', ball, ballColor);
            document.querySelectorAll('.bingo-button').forEach(button => {
                button.disabled = !checkBingo(button.closest('.player-section').querySelector('.bingo-board'));
                button.style.backgroundColor = button.disabled ? '#ccc' : '#2c4681';
            });
            if (!gameOver) {
                setTimeout(drawBall, 2000);
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

    function generateBoard() {
        let nums = shuffle([...Array(MAX_NUM).keys()].map(n => n + 1)).slice(0, BOARD_SIZE);
        return [...Array(BINGO_SIZE)].map((_, i) => nums.slice(i * BINGO_SIZE, (i + 1) * BINGO_SIZE));
    }

    function shuffle(array) {
        let currentIndex = array.length, temporaryValue, randomIndex;
        while (0 !== currentIndex) {
            randomIndex = Math.floor(Math.random() * currentIndex);
            currentIndex -= 1;
            temporaryValue = array[currentIndex];
            array[currentIndex] = array[randomIndex];
            array[randomIndex] = temporaryValue;
        }
        return array;
    }
    
    function checkBingo(container) {
        let board = [...container.querySelectorAll('.cell')].map(cell => cell.classList.contains('called'));
        let bingoCount = 0;
        for (let i = 0; i < BINGO_SIZE; i++) {
            if ([...Array(BINGO_SIZE)].every((_, j) => board[i * BINGO_SIZE + j])) bingoCount++; // check row
            if ([...Array(BINGO_SIZE)].every((_, j) => board[i + j * BINGO_SIZE])) bingoCount++; // check column
        }
        if ([...Array(BINGO_SIZE)].every((_, i) => board[i * (BINGO_SIZE + 1)])) bingoCount++; // check main diagonal
        if ([...Array(BINGO_SIZE)].every((_, i) => board[(i + 1) * (BINGO_SIZE - 1)])) bingoCount++; // check other diagonal

        return bingoCount >= MIN_BINGO_LINES;
    }

    // Socket IO setup
    var socket = io();

    // Event listener for bingo buttons
    document.querySelectorAll('.user-button').forEach(button =>
        button.addEventListener('click', function () {
            if (!gameOver && checkBingo(this.closest('.player-section').querySelector('.bingo-board'))) {
                gameOver = true;
                let winner = this.closest('.player-section').querySelector('.profile-section1 .nickname').textContent;
                openModal(winner === user.nickname);
                socket.emit('gameOver', { 'isUserVictory': winner === user.nickname });  // Send the result to the server
            }
        })
    );

    // Fetch nickname and record from server
    socket.on('fetchNicknameResponse', function (data) {
        user.nickname = data.nickname;
        initializeOwnProfile(user.nickname, `${user.wins}승 ${user.losses}패`);
    });

    socket.on('fetchRecordResponse', function (data) {
        user.wins = data.record.win;
        user.losses = data.record.lose;
        initializeOwnProfile(user.nickname, `${user.wins}승 ${user.losses}패`);
    });

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

    // On page load, fetch the nickname and record from the server
    socket.emit('fetchNickname');
    socket.emit('fetchRecord');
});

document.getElementById("gameOverModalButton").addEventListener('click', function () {
    // Redirect to mypage.html
    window.location.href = "/mypage";
});
