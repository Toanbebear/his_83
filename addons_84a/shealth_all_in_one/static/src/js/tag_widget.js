odoo.define('new_crm.my_widget', function (require) {
    "use strict";

    var core  = require('web.core');
    var fieldRegistry  = require('web.field_registry');
    var common = require('web.view_dialogs');
    var FieldMany2ManyTags = require('web.relational_fields').FieldMany2ManyTags;
    var _t = core._t;

    var MyFieldMany2ManyTags = FieldMany2ManyTags.extend({
        get_badge_id: function(el){
            if ($(el).hasClass('badge')) return $(el).data('id');
            return $(el).closest('.badge').data('id');
        },
        events: {
            'click .o_delete': function(e) {
                e.stopPropagation();
                e.preventDefault();
                // this.remove_id(this.get_badge_id(e.target));
                this._removeTag($(event.target).parent().data('id'));
            },
            'click .badge': function(e) {
                e.stopPropagation();
                e.preventDefault();
                var self = this;
                var record_id = this.get_badge_id(e.target);
                new common.FormViewDialog(self, {
                    res_model: self.field.relation,
                    res_id: record_id,
                    // context: record_id.data.context,
                    // context: {'form_view_ref': 'new_crm.crm_attendance_calendar_event_form'},
                    title: _t('Open: ') + self.string,
                    // readonly: self.get('effective_readonly')
                }).on('write_completed', self, function() {
                    self.dataset.cache[record_id].from_read = {};
                    self.dataset.evict_record(record_id);
                    self.render_value();
                }).open();
            }
        }
    });
    fieldRegistry.add('my_many2many_tags', MyFieldMany2ManyTags);

    return {
        MyFieldMany2ManyTags: MyFieldMany2ManyTags
    };

});