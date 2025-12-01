
var deferredPrompt;

window.addEventListener('beforeinstallprompt', function(event) {
    console.log('beforeinstallprompt fired!');
    // event.preventDefault();
    deferredPrompt = event;
    return false;
});

window.addEventListener('load', function(event) {

    if (deferredPrompt) {
        deferredPrompt.prompt();

        deferredPrompt.userChoice.then(function(choiceResult) {
            console.log(choiceResult.outcome);

            if (choiceResult.outcome === 'dismissed') {
                console.log('User cancelled installation.');
            } else {
                console.log('User added to home screen.')
            }
        });

        deferredPrompt = null;
    }
});

window.addEventListener('appinstalled', function(event) {
    console.log('OIC Web Apps Installed!');
});