let isCheckPasswordDuplicate = false;

// 회원가입 input validate
function validateAndSubmit() {
    var nickname = document.getElementById('nickname').value;
    var password = document.getElementById('password').value;
    var confirmPassword = document.getElementById('confirmPassword').value;
    var referral = document.getElementById('referral').value;

    var errorMessageForNickname = document.getElementById('errorMessage-nickname');
    var errorMessageForPW = document.getElementById('errorMessage-pw');
    var errorMessageForPW2 = document.getElementById('errorMessage-pw2');

    var errorMessages = document.getElementsByClassName('errorMessage');
    for(let i=0; i<errorMessages.length; i++){
        errorMessages.item(i).children[0].textContent = "";
    }


    if (nickname === "") {
        errorMessageForNickname.textContent = "필수 입력 사항입니다.";
        return;
    }
    if (password === "") {
        errorMessageForPW.textContent = "필수 입력 사항입니다.";
        return;
    }
    if (confirmPassword === "") {
        errorMessageForPW2.textContent = "필수 입력 사항입니다.";
        return;
    }

    if (password.length < 6) {
        errorMessageForPW.textContent = "비밀번호는 6자리 이상이어야 합니다.";
        return;
    }

    if (password !== confirmPassword) {
        errorMessageForPW2.textContent = "비밀번호가 일치하지 않습니다.";
        return;
    }

    if(!isCheckPasswordDuplicate){
        errorMessageForNickname.textContent = "닉네임 중복 확인은 필수입니다.";
        return;
    }

    // 여기에 회원가입 처리 로직을 추가하면 됩니다. (예: 서버로 데이터 전송 등)
    signup(nickname, password, referral)
}

// 회원가입
function signup(nickname, password, referral){

    const data = {
        "nickname": nickname,
        "password": password,
        "referral": referral
    };

    fetch("http://localhost:5000/signup", {
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
        localStorage.setItem('nickname', nickname);  // Now userNickname is accessible here
        localStorage.setItem('userId', data.userId);

        window.location.href = '/mypage';
    })
    .catch(error => {
        // 에러 처리
        alert("회원가입 에러!");
    });
}

// 닉네임 중복 확인
function checkNicknameDuplicate(){
    let errorMessageForNickname = document.getElementById('errorMessage-nickname');
    let nickname = document.getElementById('nickname').value;

    if (nickname === "") {
        errorMessageForNickname.textContent = "필수 입력 사항입니다.";
        return;
    }

    fetch(`http://localhost:5000//user/duplicate?nickname=${nickname}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json' // 요청 헤더에 JSON 형식을 명시적으로 지정
        }
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
        console.log(data)
        if(data.isDuplicate){
            errorMessageForNickname.textContent = "중복된 닉네임 입니다."
            isCheckPasswordDuplicate = false;
        }
        else{
            errorMessageForNickname.textContent = "사용 가능한 닉네임 입니다."
            isCheckPasswordDuplicate = true;
        }
    })
    .catch(error => {
        // 에러 처리
        alert("회원가입 에러!");
    });
}