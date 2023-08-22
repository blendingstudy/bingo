// 게임방 정보를 API 통신으로 받아오는 코드를 추가해야 합니다.
// 여기서는 임의로 예시 데이터를 사용합니다.
const dummyGameData = [
    { status: "대기 중", playerCount: 3, maxPlayers: 4, profileImages: ["https://mblogthumb-phinf.pstatic.net/MjAyMTAzMDhfMTky/MDAxNjE1MTg3MDkzMzQ5.LF_wRgeqp0svkxCRWSCxh0GLmSTPPXoY7Y6CpNzY1icg.mKeYJaQmfYcAFLZL_TBpxZZ2PQkYFfju_7hbj5rHnEYg.PNG.aksen244/30fa75cf-0027-4396-8b32-e1d362bc7c57.png?type=w800", "https://mblogthumb-phinf.pstatic.net/MjAyMTAzMDhfMjA3/MDAxNjE1MTg3MTQwODAx.gJOd2XftU9uZQED8X2XqnFV6tSIdoIccmk_fe1dfoQUg.rlT8ctFjTpiWSM6yDxUMdS-QEs76ZdDSQXF12Ehh5gYg.JPEG.aksen244/TikTok%EC%9D%98_%EB%8F%84%EC%97%B0.jpg?type=w800", "https://mblogthumb-phinf.pstatic.net/MjAyMTAzMDhfMjIy/MDAxNjE1MTg3MTQxMDIz.weRl0_E89fxb-Hr_htbmKmlJkAv3mhtUYSBlD7k5iPUg.YZ3jFh50iqZEjCTdpupUcecyLb6JnrSI1A4Euz1l2agg.JPEG.aksen244/Twitter.jpg?type=w800"] },
    { status: "게임 중", playerCount: 2, maxPlayers: 4, profileImages: ["https://i.pinimg.com/236x/e3/cb/8e/e3cb8eeb33d7d8f7a5ac65a08bc255ed.jpg", "https://i.pinimg.com/236x/d6/6b/7b/d66b7bc6d790cee508541fe1f80a3a2a.jpg"] },
    { status: "대기 중", playerCount: 3, maxPlayers: 4, profileImages: ["https://mblogthumb-phinf.pstatic.net/MjAyMTAzMDhfMTky/MDAxNjE1MTg3MDkzMzQ5.LF_wRgeqp0svkxCRWSCxh0GLmSTPPXoY7Y6CpNzY1icg.mKeYJaQmfYcAFLZL_TBpxZZ2PQkYFfju_7hbj5rHnEYg.PNG.aksen244/30fa75cf-0027-4396-8b32-e1d362bc7c57.png?type=w800", "https://mblogthumb-phinf.pstatic.net/MjAyMTAzMDhfMjA3/MDAxNjE1MTg3MTQwODAx.gJOd2XftU9uZQED8X2XqnFV6tSIdoIccmk_fe1dfoQUg.rlT8ctFjTpiWSM6yDxUMdS-QEs76ZdDSQXF12Ehh5gYg.JPEG.aksen244/TikTok%EC%9D%98_%EB%8F%84%EC%97%B0.jpg?type=w800", "https://mblogthumb-phinf.pstatic.net/MjAyMTAzMDhfMjIy/MDAxNjE1MTg3MTQxMDIz.weRl0_E89fxb-Hr_htbmKmlJkAv3mhtUYSBlD7k5iPUg.YZ3jFh50iqZEjCTdpupUcecyLb6JnrSI1A4Euz1l2agg.JPEG.aksen244/Twitter.jpg?type=w800"] },
    { status: "게임 중", playerCount: 2, maxPlayers: 4, profileImages: ["https://i.pinimg.com/236x/e3/cb/8e/e3cb8eeb33d7d8f7a5ac65a08bc255ed.jpg", "https://i.pinimg.com/236x/d6/6b/7b/d66b7bc6d790cee508541fe1f80a3a2a.jpg"] },
    // 추가적인 게임방 데이터를 이곳에 추가할 수 있습니다.
];

// 게임방 정보를 동적으로 생성하여 웹페이지에 표시하는 함수
// function createGameRooms() {
//     const gameRoomsContainer = document.getElementById("gameRoomsContainer");

//     dummyGameData.forEach((gameData) => {
//         const gameRoomElement = document.createElement("div");
//         gameRoomElement.classList.add("game-room");

//         const gameStatusElement = document.createElement("div");
//         gameStatusElement.classList.add("game-status");
//         gameStatusElement.textContent = gameData.status;

//         const playersElement = document.createElement("div");
//         playersElement.classList.add("players");
//         playersElement.textContent = `${gameData.playerCount}명 / ${gameData.maxPlayers}명`;

//         const profileImagesElement = document.createElement("div");
//         profileImagesElement.classList.add("profile-images");
//         gameData.profileImages.forEach((profileImage) => {
//             const imgElement = document.createElement("img");
//             imgElement.classList.add("profile-image");
//             imgElement.src = profileImage;
//             imgElement.alt = "프로필 이미지";
//             profileImagesElement.appendChild(imgElement);
//         });

//         gameRoomElement.appendChild(gameStatusElement);
//         gameRoomElement.appendChild(playersElement);
//         gameRoomElement.appendChild(profileImagesElement);

//         gameRoomsContainer.appendChild(gameRoomElement);
//     });
// }


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

        gameRoomsContainer.appendChild(gameRoomElement);
    }
}