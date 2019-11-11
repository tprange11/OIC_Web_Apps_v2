// THIS JS IS USED IF VIEWING BOTH RINKS TOGETHER //

var rinks = document.querySelectorAll(".rink");

rinks.forEach(element => {
    if (element.innerText == "South Rink") {
        element.style.color = "blue";
    } else if (element.innerHTML.indexOf("North") !== -1) {
        element.style.color = "red";
    }
});


// This was taken from w3schools.com and modified by Brian Christensen
// Set the date we're counting down to
// var resurface_time = document.getElementById("resurface-time1").innerHTML;
var resurface_time = resurface_times[0];

// if ( start_time[0] == resurface_time[0] ) {
//     var resurface_time = resurface_time[1];
// } else {
//     var resurface_time = resurface_time[0];
// }
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
    // Reload the page to update the count down
    window.location.href = window.location.href
  }
}, 1000);