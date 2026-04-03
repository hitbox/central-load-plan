"use strict";

function getHREF(el) {
    /* walk up parents to get data-href attribute's value */
    let href;
    while (!(href = el.getAttribute("data-href"))) {
        el = el.parentElement;
    }
    return href
}

addEventListener("DOMContentLoaded", function() {
    for (const el of document.querySelectorAll("[data-href]")) {
        el.addEventListener("click", function(event) {
            /* left click */
            document.location = getHREF(event.target);
        });
        el.addEventListener("auxclick", function(event) {
            /* right or middle click */
            if (event.button == 1) {
                /* middle click */
                window.open(getHREF(event.target), "_blank");
            }
        });
    }
});
