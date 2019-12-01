
if (!window.Promise) {
    window.Promise = Promise;
}

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register("/serviceworker.js")
        .then(function() {
            console.log('Service Worker registered!');
        }).catch(function(err) {
            console.log(err);
        });
}



