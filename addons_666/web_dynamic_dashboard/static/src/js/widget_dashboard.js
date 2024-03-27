odoo.define('web_dynamic_dashboard.web_widget_colorpicker', function(require) {
    "use strict";

    var field_registry = require('web.field_registry');
    var Field = field_registry.get('char');


    var FieldColorPicker = Field.extend({

        template: 'FieldColorPicker',
        widget_class: 'oe_form_field_color',

        _getValue: function () {
            var $input = this.$el.find('input');
            return $input.val();
        },

        _renderReadonly: function () {
            var show_value = this.value;
            var $input = this.$el.find('input');
            $input.val(show_value || '');
            this.$el.colorpicker({format: 'rgba'});
            $input.attr('readonly', true);
        },

        _renderEdit: function () {
            var show_value = this.value ;
            var $input = this.$el.find('input');
            $input.val(show_value);
            this.$el.colorpicker({format: 'rgba'});
            this.$input = $input;
        }

    });

    field_registry
    .add('colorpicker', FieldColorPicker);

    return {
        FieldColorPicker: FieldColorPicker
    };
});

odoo.define('web_dynamic_dashboard.web_widget_iconpicker', function(require) {
    "use strict";

    var field_registry = require('web.field_registry');
    var Field = field_registry.get('char');


    var FieldIconPicker = Field.extend({

        template: 'FieldIconPicker',
        widget_class: 'oe_form_field_icon',

        _getValue: function () {
            var $input = this.$el.find('input');
            return $input.val();
        },

        _renderReadonly: function () {
            var show_value = this.value;
            this.$el.text(show_value || '');
        },

        _renderEdit: function () {
            var self = this;
            var show_value = this.value;
            var $input = this.$el.find('input');
            $input.val(show_value);
            setTimeout(function() {
                $input.iconpicker();
                $input.on('iconpickerSelected', function(event){
                    this.value = $input.val();
                    self._setValue($input.val());
                });
            }, 300);
            this.$input = $input;
        }

    });

    field_registry
    .add('iconpicker', FieldIconPicker);

    return {
        FieldIconPicker: FieldIconPicker
    };
});

