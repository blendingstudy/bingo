const nickname = localStorage.getItem("nickname")

getGameRoomList();

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
            createGameRooms(data.game_room_list)
            
        })
        .catch(error => {
            // 에러 처리
            console.error(error)
            alert("게임방 리스트 요청 실패")
        });

}

function createGameRooms(dummyGameData) {
    console.log(dummyGameData)
    const gameRoomsContainer = document.getElementById("gameRoomsContainer");

    for(let gameData of dummyGameData){
        const gameRoomElement = document.createElement("div");
        gameRoomElement.classList.add("game-room");
        gameRoomElement.id = "game-room-id-" + gameData.game_room_id;

        const gameInfoContainerElement = document.createElement("div");
        gameInfoContainerElement.classList.add("game-info-container");


        const gameIdElement = document.createElement("div");
        gameIdElement.classList.add("game-id");
        gameIdElement.textContent = "No. " + gameData.game_room_id;

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
            imgElement.src = player.profile_img;
            imgElement.alt = "프로필 이미지";
            profileImagesElement.appendChild(imgElement);
        }

        gameInfoContainerElement.appendChild(gameIdElement);
        gameInfoContainerElement.appendChild(gameStatusElement);

        gamePlayerContainerElement.appendChild(playersElement);
        gamePlayerContainerElement.appendChild(profileImagesElement);

        gameRoomElement.appendChild(gameInfoContainerElement);
        gameRoomElement.appendChild(gamePlayerContainerElement);

        gameRoomElement.addEventListener("click", () => {
            alert("클릭! " + gameData.game_room_id)
            localStorage.setItem("gameMatchNum", gameData.game_room_id)
            window.location.href = '/game2';
        })

        gameRoomsContainer.appendChild(gameRoomElement);
    }
}


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
        return response.text(); // JSON 파싱하여 반환
      })
    .then(data => {
        // 응답 데이터 처리
        console.log(data)
        localStorage.setItem("gameMatchNum", data.gameMatchNum)
        window.location.href = '/game2';
    })
    .catch(error => {
        // 에러 처리
        alert("새 게임 생성 에러!");
    });
}