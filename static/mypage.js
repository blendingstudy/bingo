
console.log("마이페이지 입장")

let userNickname = localStorage.getItem('nickname');  // Retrieve nickname from local storage


getUserInfo()

function getUserInfo(){
    console.log("유저정보 요청 시도:", userNickname)

    const url = "http://prgstudy.com:5000/user?nickname=" + userNickname 

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
            
            document.getElementById("profile-picture").appendChild(imgElement);

            document.getElementById('user-nickname').textContent = data.nickname;
            let record = data.record.win + '승 ' + data.record.lose + '패';
            document.getElementById('record').textContent = record;
        })
        .catch(error => {
            // 에러 처리
            alert("유저정보 요청 실패")
        });

}


// Redirect to waiting.html when start button is clicked
document.getElementById('start-button').addEventListener('click', function() {
    window.location.href = '/game';
});
