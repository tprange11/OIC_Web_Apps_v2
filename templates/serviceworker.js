// Service worker (served at /serviceworker.js by a TemplateView). Precaches the app
// shell and answers from cache first, falling back to the network and then to
// /offline/. Bump STATIC_CACHE whenever a precached file changes; activate()
// deletes every other cache.
// Nothing is cached at runtime: dynamic caching was tried and dropped because it
// served logged-in pages to the wrong state (see the old handler at the bottom).

var STATIC_CACHE = 'oicwebapps-v26';

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(function(cache) {
                // addAll() fails as a whole if any one URL 404s, so keep this list current
                cache.addAll([
                    '/',
                    '/offline/',
                    '/static/js/app.js',
                    '/static/js/promise.js',
                    '/static/js/fetch.js',
                    '/static/css/main.css',
                    '/static/images/OIC_Logo_Small.jpg',
                    '/static/images/icons/android-chrome-192x192.png',
                    '/static/images/icons/android-chrome-512x512.png',
                    '/static/images/icons/favicon.ico',
                    '/static/images/icons/favicon-32x32.png',
                    '/static/images/icons/favicon-16x16.png',
                    '/static/images/icons/favicon-96x96.png',
                    '/static/manifest.json',
                    '/info/open_hockey/',
                    '/info/stick_and_puck/',
                    '/info/figure_skating/',
                    'https://code.jquery.com/jquery-3.4.1.slim.min.js',
                    'https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js',
                    'https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js',
                    'https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css',
                    'https://fonts.googleapis.com/css?family=Russo+One&display=swap',
                    'https://fonts.gstatic.com/s/russoone/v8/Z9XUDmZRWg6M1LvRYsHOz8mJvLuL9A.woff2'
                ]);
            })
        )
});

self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys()
            .then(function(keyList) {
                return Promise.all(keyList.map(function(key) {
                    if (key !== STATIC_CACHE) {
                        return caches.delete(key);
                    }
                }));
            })
    )
    return self.clients.claim();
});

// Cache first, then network, then the offline page. Applies to every request,
// including POSTs, which caches.match() simply never matches.
self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                } else {
                    return fetch(event.request);
                }
            })
            .catch(function(err) {
                return caches.open(STATIC_CACHE)
                    .then(function(cache) {
                        return cache.match('/offline/');
                    })
            })
    );
});

self.addEventListener('notificationclick', function(event) {
    var notification = event.notification;
    var action = event.action;

    // The "confirm" (Open App) action is not offered by the resurface notification at
    // the moment (see static/js/schedule*.js); the handler below is parked for when it is.
    if (action === 'confirm') {
        // event.waitUntil(
        //     clients.matchAll()
        //         .then(function(clis) {
        //             var client = clis.find(function(c) {
        //                 return c.visibilityState === 'visible';
        //             });

        //             if (client !== undefined) {
        //                 client.navigate('/web_apps/schedule/rink/both');
        //                 client.focus();
        //             } else {
        //                 clients.openWindow('/web_apps/schedule/rink/both');
        //             }
        //             notification.close();
        //         })
        // )
    } else {
        notification.close();
    }
});

// Parked: runtime (dynamic) caching. Disabled because cached responses leaked
// logged-in pages between sessions. Kept for reference only.
// self.addEventListener('fetch', function(event) {
//     event.respondWith(
//         caches.match(event.request)
//             .then(function(response) {
//                 if (response) {
//                     return response;
//                 } else {
//                     return fetch(event.request)
//                         .then(function(res) {
//                             caches.open(DYNAMIC_CACHE)
//                             .then(function(cache) {
//                                 cache.put(event.request.url, res.clone());
//                                 return res;
//                             })
//                         })
//                         .catch(function(err) {
//                             // Do nothing
//                         });
//                 }
//             })
//     );
// });
