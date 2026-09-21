// Add-to-home-screen prompt. The browser's own install banner is not suppressed
// (no preventDefault), so the saved event is only re-prompted on window load when
// beforeinstallprompt fired before the page finished loading.

var deferredPrompt;

window.addEventListener('beforeinstallprompt', function(event) {
    console.log('beforeinstallprompt fired!');
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