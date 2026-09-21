// PWA bootstrap: registers the service worker served from /serviceworker.js.
// promise.js and fetch.js (polyfills, loaded before this) cover old browsers.

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



