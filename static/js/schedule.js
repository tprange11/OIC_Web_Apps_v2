var rinks = document.querySelectorAll(".rink");

rinks.forEach(element => {
    if (element.innerText == "South Rink") {
        element.style.color = "blue";
    } else if (element.innerText == "North Rink") {
        element.style.color = "red";
    }
});


// This was taken from w3schools.com and modified by Brian Christensen on 10-9-2019
// Set the date we're counting down to
var resurface_time = document.getElementById("resurface-time1").innerHTML;
var countDownDate = new Date(resurface_time.replace(/-/g, '/')).getTime();

// Update the count down every 1 second
var x = setInterval(function() {

  // Get today's date and time
  var now = new Date().getTime();
    
  // Find the distance between now and the count down date
  var distance = countDownDate - now;
    
  // Time calculations for days, hours, minutes and seconds
//  var days = Math.floor(distance / (1000 * 60 * 60 * 24));
  var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
  var seconds = Math.floor((distance % (1000 * 60)) / 1000);
    
  // Output the result in an element with id="demo"
  document.getElementById("resurface-timer").innerHTML = hours + " Hours "
  + minutes + " Mins " + seconds + " Secs";
    
    
  // If the count down is over, write some text 
  if (distance < 0) {
    clearInterval(x);
    document.getElementById("resurface-timer").innerHTML = "Refresh Page to Reset Resurface Countdown";
    // location.reload("true");
    window.location.href = window.location.href
  }
}, 1000);