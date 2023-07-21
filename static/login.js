let inputNickname;  // Declare userNickname variable here
let inputPW;

document.getElementById('login-button').addEventListener('click', function() {
    inputNickname = document.getElementById('nickname-input').value;  // Assign value to userNickname here
    document.getElementById('nickname-input').value = "";
    inputPW = document.getElementById('password-input').value;  // Assign value to userNickname here
    document.getElementById('password-input').value = "";

    console.log("입장 버튼 누름!")
    
    // Emit 'login' event to server with the entered nickname
    // socket.emit('login', {nickname: userNickname});

    const data = {
        "nickname": inputNickname,
        "password": inputPW
    };

    fetch("http://localhost:5000/login", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json' // 요청 헤더에 JSON 형식을 명시적으로 지정
        },
        body: JSON.stringify(data) // 전송할 데이터를 JSON 문자열로 변환하여 요청 본문에 포함
    })
        .then(response => response.json()) // 응답을 JSON 형식으로 파싱
        .then(data => {
            // 응답 데이터 처리
            console.log(data)
            localStorage.setItem('nickname', inputNickname);  // Now userNickname is accessible here
            localStorage.setItem('userId', data.user_id);
            window.location.href = '/mypage';
        })
        .catch(error => {
            // 에러 처리
            alert("로그인 에러!");
        });
      
});