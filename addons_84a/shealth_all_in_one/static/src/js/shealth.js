/**********************************************************************************
*
*    Copyright (c) 2017-2019 MuK IT GmbH.
*
*    This file is part of MuK Preview MS Office
*    (see https://mukit.at).
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Lesser General Public License as published by
*    the Free Software Foundation, either version 3 of the License, or
*    (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Lesser General Public License for more details.
*
*    You should have received a copy of the GNU Lesser General Public License
*    along with this program. If not, see <http://www.gnu.org/licenses/>.
*
**********************************************************************************/
// odoo.define('sHealth_all_in_one.sHFieldMany2Many', function (require) {
// "use strict";
// var core = require('web.core');
// var relational_fields = require('web.relational_fields');
//
// var _t = core._t;
// var QWeb = core.qweb;
//
// var FormRenderer = require('web.FormRenderer');
//
// FormRenderer.include({
//     init: function (parent,state) {
//         // console.log(state);
//         // console.log(state.data.imaging_type_ids.count);
//
//         return this._super.apply(this, arguments);
//     },
//      start: function() {
//          return this._super.apply(this, arguments);
//      }
// });
//
// relational_fields.FieldMany2Many.include({
//     /**
//      * @override
//      */
//     _onFieldChanged: function (ev) {
//         this._super.apply(this, arguments);
//
//         if(ev.data.changes.lab_type_ids){
//             var current_lab_type = this.value.data.length;
//             var lab_type_change = ev.data.changes.lab_type_ids.ids.length;
//             var total_lab_type = ev.data.changes.lab_type_ids.operation != 'FORGET'?(current_lab_type+lab_type_change):(current_lab_type-lab_type_change);
//             $('.sH_service_labtest a').text('Labtest Type('+total_lab_type+')');
//         }else if(ev.data.changes.imaging_type_ids){
//             var current_img_type = this.value.data.length;
//             var img_type_change = ev.data.changes.imaging_type_ids.ids.length;
//             var total_img_type = ev.data.changes.imaging_type_ids.operation != 'FORGET'?(current_img_type+img_type_change):(current_img_type-img_type_change);
//             $('.sH_service_imaging a').text('Imaging Type('+total_img_type+')');
//         }
//         //
//         // alert(JSON.stringify(ev.data));
//         // alert(JSON.stringify(ev.data.changes));
//     },
// });
//
// });