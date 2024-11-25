/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.acceptSignButton = publicWidget.Widget.extend({
    selector: '#terms_conditions_checkbox', // Updated selector to match both buttons
    events: {
        'click': '_onClickAcceptSignButton'
    },

    start: function () {
        this._super.apply(this, arguments);
        const button = $('.accept_sign_button');
        button.attr('data-bs-target', '#modalalert');
    },

    _onClickAcceptSignButton: function (ev) {

        const checkbox = $(ev.currentTarget);
        const button = $('.accept_sign_button');

        if (!checkbox.prop('checked')) {
            button.attr('data-bs-target', '#modalalert');
        } else {
            button.attr('data-bs-target', '#modalaccept');
        }
    },
});
export default publicWidget.registry.acceptSignButton;