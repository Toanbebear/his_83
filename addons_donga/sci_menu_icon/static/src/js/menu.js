odoo.define('sci.MenuExtend', function (require) {
"use strict";

var Menu = require('web.Menu');
var core = require('web.core');

var MenuExtend = Menu.include({
    change_menu_section: function (primary_menu_id) {
        if (!this.$menu_sections[primary_menu_id]) {
            this._updateMenuBrand();
            return; // unknown menu_id
        }

        if (this.current_primary_menu === primary_menu_id) {
            return; // already in that menu
        }

        if (this.current_primary_menu) {
            this.$menu_sections[this.current_primary_menu].detach();
        }

        // Get back the application name
        for (var i = 0; i < this.menu_data.children.length; i++) {
            if (this.menu_data.children[i].id === primary_menu_id) {
                this._updateMenuBrand(this.menu_data.children[i].name,this.menu_data.children[i].web_icon_class);
                break;
            }
        }

        this.$menu_sections[primary_menu_id].appendTo(this.$section_placeholder);
        this.current_primary_menu = primary_menu_id;

        core.bus.trigger('resize');
    },
    /**
     * Updates the name of the app in the menu to the value of brandName.
     * If brandName is falsy, hides the menu and its sections.
     *
     * @private
     * @param {brandName} string
     */
    _updateMenuBrand: function (brandName,icon) {
        if (brandName) {
            //view icon & hide name
            if(icon){
                brandName = '<i class="'+icon+'"></i>';
            }

            this.$menu_brand_placeholder.html(brandName).show();
            this.$section_placeholder.show();
        } else {
            this.$menu_brand_placeholder.hide()
            this.$section_placeholder.hide();
        }
    }
});

return MenuExtend;

});
