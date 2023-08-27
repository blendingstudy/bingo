const nickname = localStorage.getItem("nickname")

getGameRoomList();

// 게임방 리스트 정보 얻기
function getGameRoomList(){
    const url = "http://localhost:5000/gameroom/list/info"

    fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json' // 요청 헤더에 JSON 형식을 명시적으로 지정
        },
    })
        .then(response => response.json()) // 응답을 JSON 형식으로 파싱
        .then(data => {
            // 응답 데이터 처리
            createGameRooms(data.gameRoomList)
            
        })
        .catch(error => {
            // 에러 처리
            console.error(error)
            alert("게임방 리스트 요청 실패")
        });

}

// 게임방 요소 만들어 화면에 뿌리기
function createGameRooms(dummyGameData) {
    console.log(dummyGameData)
    const gameRoomsContainer = document.getElementById("gameRoomsContainer");

    for(let gameData of dummyGameData){
        const gameRoomElement = document.createElement("div");
        gameRoomElement.classList.add("game-room");
        gameRoomElement.id = "game-room-id-" + gameData.gameRoomId;

        const gameInfoContainerElement = document.createElement("div");
        gameInfoContainerElement.classList.add("game-info-container");


        const gameIdElement = document.createElement("div");
        gameIdElement.classList.add("game-id");
        gameIdElement.textContent = "No. " + gameData.gameRoomId;

        const gamePlayerContainerElement = document.createElement("div");
        gamePlayerContainerElement.classList.add("game-player-container");

        const gameStatusElement = document.createElement("div");
        gameStatusElement.classList.add("game-status");
        gameStatusElement.textContent = gameData.status;

        const playersElement = document.createElement("div");
        playersElement.classList.add("players");
        playersElement.textContent = `${gameData.players.length}명 / 7명`;

        const profileImagesElement = document.createElement("div");
        profileImagesElement.classList.add("profile-images");
        for(let player of gameData.players){
            const imgElement = document.createElement("img");
            imgElement.classList.add("profile-image");
            imgElement.src = player.profileImg;
            imgElement.alt = "프로필 이미지";
            profileImagesElement.appendChild(imgElement);
        }

        gameInfoContainerElement.appendChild(gameIdElement);
        gameInfoContainerElement.appendChild(gameStatusElement);

        gamePlayerContainerElement.appendChild(playersElement);
        gamePlayerContainerElement.appendChild(profileImagesElement);

        gameRoomElement.appendChild(gameInfoContainerElement);
        gameRoomElement.appendChild(gamePlayerContainerElement);

        // 이벤트 리스너 등록
        gameRoomElement.addEventListener("click", () => {
            alert("클릭! " + gameData.gameRoomId)
            localStorage.setItem("gameMatchNum", gameData.gameRoomId)
            window.location.href = '/game2';
        })

        gameRoomsContainer.appendChild(gameRoomElement);
    }
}

// 새 게임방 만들기
function createNewGame(){
    const data = {
        "nickname": nickname
    };

    fetch("http://localhost:5000/gameroom", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json' // 요청 헤더에 JSON 형식을 명시적으로 지정
        },
        body: JSON.stringify(data) // 전송할 데이터를 JSON 문자열로 변환하여 요청 본문에 포함
    })
    .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        // 상태 코드 확인
        console.log('Status Code:', response.status);
        return response.json(); // JSON 파싱하여 반환
      })
    .then(data => {
        // 응답 데이터 처리
        console.log(data.gameMatchNum)
        localStorage.setItem("gameMatchNum", data.gameMatchNum)
        window.location.href = '/game';
    })
    .catch(error => {
        // 에러 처리
        alert("새 게임 생성 에러!");
    });
}