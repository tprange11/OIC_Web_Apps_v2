
var STATIC_CACHE = 'oicwebapps-v16';
// var DYNAMIC_CACHE = 'oicwebapps-dyn-v1';

self.addEventListener('install', function(event) {
    console.log('[Service Worker] Installing Service Worker....');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(function(cache) {
                console.log('[Service Worker] Precaching App Shell!');
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
    console.log('[Service Worker] Activating Service Worker....');
    event.waitUntil(
        caches.keys()
            .then(function(keyList) {
                return Promise.all(keyList.map(function(key) {
                    if (key !== STATIC_CACHE) {
                        console.log('[Service Worker] Removing old cache.', key);
                        return caches.delete(key);
                    }
                }));
            })
    )
    return self.clients.claim();
});

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

    console.log(notification);

    if (action === 'confirm') {
        console.log('Open App pressed.')
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
        console.log('Dismiss pressed.');
        notification.close();
    }
});

// self.addEventListener('notificationclose', function(event) {
//     console.log('Notification was closed!', event);
// })

// BELOW IS WITH DYNAMIC CACHING, NOT GOOD WHEN LOGGED IN
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
