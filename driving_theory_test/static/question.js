
function confirmSubmit() {
  if (confirm("All progress will be lost. Are you sure?") == true) {
        return true
  }
  else { return false }
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

