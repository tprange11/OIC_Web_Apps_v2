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

// This was taken from w3schools.com and modified by Brian Christensen
// Set the date we're counting down to
// var resurface_time = document.getElementById("resurface-time1").innerHTML;
// If the end time and the next start time are the same, use the next resurface time (There is no resurface between events)
// Only checking three consecutive events
if ( north_start_times.length == north_resurface_times.length ) {
    if ( north_resurface_times[0] == north_start_times[1] ) {
        if ( north_resurface_times[1] == north_start_times[2] ) {
            var north_resurface_time = north_resurface_times[2];
        } else {
            var north_resurface_time = north_resurface_times[1];
        }
    } else {
        var north_resurface_time = north_resurface_times[0];
    }
} else if ( north_start_times.length < north_resurface_times.length ) {
    if ( north_resurface_times[0] == north_start_times[0] ) {
        if ( north_resurface_times[1] == north_start_times[1] ) {
            var north_resurface_time = north_resurface_times[2];
        } else {
        var north_resurface_time = north_resurface_times[1];
        }
    } else {
        var north_resurface_time = north_resurface_times[0];
    }
}

if ( south_start_times.length == south_resurface_times.length ) {
    if ( south_resurface_times[0] == south_start_times[1] ) {
        if ( south_resurface_times[1] == south_start_times[2] ) {
            var south_resurface_time = south_resurface_times[2];
        } else {
            var south_resurface_time = south_resurface_times[1];
        }
    } else {
        var south_resurface_time = south_resurface_times[0];
    }
} else if ( south_start_times.length < south_resurface_times.length ) {
    if ( south_resurface_times[0] == south_start_times[0] ) {
        if ( south_resurface_times[1] == south_start_times[1] ) {
            var south_resurface_time = south_resurface_times[2];
        } else {
        var south_resurface_time = south_resurface_times[1];
        }
    } else {
        var south_resurface_time = south_resurface_times[0];
    }
}

var south = true;
if ( south_resurface_times.length === 0 && south_start_times.length === 0 ){
    south = false;
}
var north = true;
if ( north_resurface_times.length === 0 && north_resurface_times.length === 0 ) {
    var north = false;
}

if (south) {
    var southCountDownDate = new Date(south_resurface_time.replace(/-/g, '/')).getTime();
}

if (north) {
    var northCountDownDate = new Date (north_resurface_time.replace(/-/g, '/')).getTime();
}

// Update the count down every 1 second
var x = setInterval(function() {

  // Get today's date and time
  var now = new Date().getTime();
    
  
if (south) {
    // Find the distance between now and the count down date
    var southDistance = southCountDownDate - now;
    // Time calculations for days, hours, minutes and seconds
    //  var days = Math.floor(distance / (1000 * 60 * 60 * 24));
    var southHours = Math.floor((southDistance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var southMinutes = Math.floor((southDistance % (1000 * 60 * 60)) / (1000 * 60));
    var southSeconds = Math.floor((southDistance % (1000 * 60)) / 1000);
    // Output the result in an element with id="resurface"
    document.getElementById("south-resurface-timer").innerHTML = southHours + " Hours "
    + southMinutes + " Mins " + southSeconds + " Secs";
    // 10 minutes prior to the next resurface, send notification to device
    if (southHours == 0 && southMinutes == 10 && southSeconds == 0) {
        sendNotification();
    }
    if (southHours == 0 && southMinutes <= 9 && southSeconds <= 59) {
        document.getElementById("south-schedule-row1").style.backgroundColor = "lightgray";
        document.getElementById("south-schedule-row1").style.color = "black";
    }
}

if (north) {
    var northDistance = northCountDownDate - now;
    var northHours = Math.floor((northDistance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var northMinutes = Math.floor((northDistance % (1000 * 60 * 60)) / (1000 * 60));
    var northSeconds = Math.floor((northDistance % (1000 * 60)) / 1000);
    document.getElementById("north-resurface-timer").innerHTML = northHours + " Hours "
    + northMinutes + " Mins " + northSeconds + " Secs";
    if (northHours == 0 && northMinutes == 10 && northSeconds == 0) {
        sendNotification();
    }
    if (northHours == 0 && northMinutes <= 9 && northSeconds <= 59) {
        document.getElementById("north-schedule-row1").style.backgroundColor = "black";
    }
}
    
  // If the count down is over, write some text and reload the page
  if (southDistance < 0 || northDistance < 0) {
    clearInterval(x);
    document.getElementById("south-resurface-timer").innerHTML = "Refresh Page to Reset Resurface Countdown";
    document.getElementById("north-resurface-timer").innerHTML = "Refresh Page to Reset Resurface Countdown";
    // Reload the page to update the count down
    window.location.href = window.location.href
  }
}, 1000);
