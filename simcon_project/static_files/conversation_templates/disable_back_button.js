window.onunload = function () { null };
function preventBack() {
    window.history.forward();
}
Promise.resolve('hello').then(function() {
    return setTimeout("preventBack()", 0);
}).then(console.log.bind(console))
