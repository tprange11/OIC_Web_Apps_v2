// Resurface countdown for a single rink (north or south) and for "both" rinks on
// one list. Expects the template to define two arrays of "YYYY-MM-DD HH:MM:SS"
// strings: start_times (upcoming event starts) and resurface_times (event ends).

// Ask once for permission to show resurface notifications
function resurfaceNotificationPermission() {
    Notification.requestPermission(function(result) {
        console.log('Resurface Notification Choice: ', result);
        if (result !== 'granted') {
            console.log('Notification Permission Denied!');
        } else {
            console.log('Notification Permission Granted!');
        }
    });
}

if ('Notification' in window) {
    resurfaceNotificationPermission();
}

// Show the "10 minutes till next resurface" notification through the service worker
function sendNotification() {
    if ('serviceWorker' in navigator) {
    var options = {
        body: '10 minutes till next resurface!',
        icon: '/static/images/icons/favicon-96x96.png',
        dir: 'ltr',
        lang: 'en-US',
        vibrate: [100, 50, 200],
        badge: '/static/images/icons/oicwebapps-badge-96x96.png',
        tag: 'resurface-notification',
        renotify: true,
        actions: [
            // { action: 'confirm', title: 'Open App', icon: '' },
            { action: 'cancel', title: 'Got It', icon: '' }
        ]
    };

    navigator.serviceWorker.ready
        .then(function(swreg) {
            swreg.showNotification('Resurface Notification[SW]', options);
        })
    }
}

// Countdown adapted from w3schools.com by Brian Christensen.
// Pick the next resurface time. When an event ends exactly when the next one starts
// there is no resurface in between, so skip ahead; only three consecutive events are
// checked. If neither branch matches (more starts than ends, or no events at all)
// resurface_time stays undefined and the .replace() below throws.
if ( start_times.length == resurface_times.length ) {
    if ( resurface_times[0] == start_times[1] ) {
        if ( resurface_times[1] == start_times[2] ) {
            var resurface_time = resurface_times[2];
        } else {
            var resurface_time = resurface_times[1];
        }
    } else {
        var resurface_time = resurface_times[0];
    }
} else if ( start_times.length < resurface_times.length ) {
    if ( resurface_times[0] == start_times[0] ) {
        if ( resurface_times[1] == start_times[1] ) {
            var resurface_time = resurface_times[2];
        } else {
        var resurface_time = resurface_times[1];
        }
    } else {
        var resurface_time = resurface_times[0];
    }
}
var countDownDate = new Date(resurface_time.replace(/-/g, '/')).getTime();

// Update the count down every 1 second
var x = setInterval(function() {

  // Get today's date and time
  var now = new Date().getTime();
    
  // Find the distance between now and the count down date
  var distance = countDownDate - now;
    
  // Time calculations for hours, minutes and seconds
  var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
  var seconds = Math.floor((distance % (1000 * 60)) / 1000);
    
  document.getElementById("resurface-timer").innerHTML = hours + " Hours "
  + minutes + " Mins " + seconds + " Secs";
    
  // 10 minutes prior to the next resurface, send notification to device
  if (hours == 0 && minutes == 10 && seconds == 0) {
    sendNotification();
}

// Highlight the current event's row for the last ten minutes
if (hours == 0 && minutes <= 9 && seconds <= 59) {
    document.querySelectorAll(".schedule-row")[1].style.backgroundColor = "lightgreen";
}
    
  // Countdown over: reload so the view recomputes from the next event
  if (distance < 0) {
    clearInterval(x);
    document.getElementById("resurface-timer").innerHTML = "Refresh Page to Reset Resurface Countdown";
    window.location.href = window.location.href
  }
}, 1000);