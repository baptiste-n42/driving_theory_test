
function confirmSubmit() {
  const toggleInput = document.getElementById('toggleInput');
  if (toggleInput.checked) {
    return confirm('Are you sure you want to submit with the toggle button on?');
  }
  return true;
}

function setTime(timer) {
            minutes = parseInt(timer / 60, 10);
            seconds = parseInt(timer % 60, 10);

            minutes = minutes < 10 ? "0" + minutes : minutes;
            seconds = seconds < 10 ? "0" + seconds : seconds;

            display.textContent = minutes + ":" + seconds;
}


function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    setTime(timer);
    var intervalId =  setInterval(function () {
            setTime(timer);

            if (--timer < 0) {
                clearInterval(intervalId); // Stop the timer
                display.textContent = "Times up !";
            }
        }, 1000);
}

function isResponseValid() {


}

