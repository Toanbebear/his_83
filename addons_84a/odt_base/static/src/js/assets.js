$(document).ready(function () {
    var observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                // element added to DOM
                var hasClass = [].some.call(mutation.addedNodes, function (el) {
                    return el.classList.contains('modal')
                });
                if (hasClass) {
                    if ($('h4.modal-title').text().substring(0, "Odoo Server Error".length) == 'Odoo Server Error') {
                        $('h4.modal-title').html("Thông báo");
                    }
                }
            }
        });
    });

    var config = {
        attributes: true,
        childList: true,
        characterData: true
    };

    observer.observe(document.body, config);
    console.log('oke');
});
	
