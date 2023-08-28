// 로그인 버튼 클릭
document.getElementById("login-button").addEventListener("click", () => {
    inputNickname = document.getElementById('nickname-input').value;  // Assign value to userNickname here
    inputPW = document.getElementById('password-input').value;  // Assign value to userNickname here
    document.getElementById("errorMessage-login").textContent = ""

    console.log("입장 버튼 누름!")

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
    .then(response => {
        if(!response.ok){
            throw new Error("login fail")
        }
        return response.json(); // 응답을 JSON 형식으로 파싱
    }) 
    .then(data => {
        // 응답 데이터 처리
        console.log(data)
        localStorage.setItem('nickname', inputNickname);  // Now userNickname is accessible here
        localStorage.setItem('userId', data.userId);
        window.location.href = '/mypage';
    })
    .catch(error => {
        document.getElementById("errorMessage-login").textContent = "로그인에 실패했습니다."
    });
      
    document.getElementById('nickname-input').value = "";
    document.getElementById('password-input').value = "";
})

// 회원가입 페이지로 이동
document.getElementById("signup-link").addEventListener("click", () => {
    window.location.href = '/signup';
})