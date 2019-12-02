// THIS JS IS USED IF EITHER NORTH OR SOUTH RINKS ARE BEING VIEWED //

// resurfaceNotificationPermission() requests user permission to send resurface
// notifications
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

// If the browser supports notifications, send permission request
if ('Notification' in window) {
    resurfaceNotificationPermission();
}

// sendNotification utilizes the service worker to send the resurface notification
// to the device
function sendNotification() {
    if ('serviceWorker' in navigator) {
    var options = {
        body: '10 minutes till next resurface!',
        icon: '/static/images/icons/favicon-96x96.png',
        dir: 'ltr',
        lang: 'en-US',
        vibrate: [100, 50, 200],
        badge: '/static/images/icons/oicwebapps-badge-96x96.png',
        tag: 'confirm-notification',
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

// This was taken from w3schools.com and modified by Brian Christensen
// Set the date we're counting down to
// var resurface_time = document.getElementById("resurface-time1").innerHTML;
// If the end time and the next start time are the same, use the next resurface time (There is no resurface between events)
// Only checking three consecutive events
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
    
  // Output the result in an element with id="resurface"
  document.getElementById("resurface-timer").innerHTML = hours + " Hours "
  + minutes + " Mins " + seconds + " Secs";
    
  // 10 minutes prior to the next resurface, send notification to device
  if (hours == 0 && minutes == 10 && seconds == 0) {
    sendNotification();
}
    
  // If the count down is over, write some text 
  if (distance < 0) {
    clearInterval(x);
    document.getElementById("resurface-timer").innerHTML = "Refresh Page to Reset Resurface Countdown";
    // Reload the page to update the count down
    window.location.href = window.location.href
  }
}, 1000);