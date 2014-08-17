var global = {};
global.team_colors = {};

function pad(n, width, z) {
  z = z || '0';
  n = n + '';
  return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
}

function formatDate(d) {
    //getMonth starts at 0 for some reason..
    if (d === null) {
        return null;
    }
    else {
        return d.getFullYear()+'-'+pad(d.getMonth()+1,2)+'-'+pad(d.getDate(),2);
    }
}

function modify_event_by_id(event_id) {
    $.post('/'+global.team+'/event/'+event_id,
           {'user_username': $('div#menu_content #user option:selected').attr('id'),
            'role': $('div#menu_content #role option:selected').val()});
    $('#calendar').fullCalendar('refetchEvents');
}

function delete_event_by_id(event_id) {
    $.post('/'+global.team+'/event/delete/'+event_id);
    $('#calendar').fullCalendar('refetchEvents');
    global.menu.hide();
}

function updateAndRefetch(event, delta) {
    $.post('/'+global.team+'/event/'+event.id,
           {'start': formatDate(event.start),
            'end': formatDate(event.end),
            'username': $(this).attr('id')});
    $('#calendar').fullCalendar('refetchEvents');
}

function updateOncall() {
    var primary = [];
    var secondary = [];
    //var team_id = $('select#team option:selected').attr('id');

    $('ul#primary_oncall li').each(function(k, v) { primary.push($(v).attr('id')); });
    $('ul#secondary_oncall li').each(function(k, v) { secondary.push($(v).attr('id')); });
    $.ajax({
        type: 'post',
        url: '/'+global.team+'/oncallOrder',
        data: {'Primary': primary,
               'Secondary': secondary},

        success: function(data, status) {
            $('#oncallOrderModal').modal('hide');
            get_flashes();
        }
    });

}

/* Can handle either a array of values or
   an array of arrays of key, val pairs
*/
function make_select_options(options, selected) {
    var html_opts = [];
    $(options).each(function (key, value) {
        var opt = $('<option/>');
        if (typeof(value) == "string") {
            opt.html(value);
            opt.attr('id', value);
            if (value == selected)
                opt.attr('selected', 'selected');
        }
        else {
            // we must have a [key, val] array
            opt.html(value[1]);
            opt.attr('id', value[0]);
            if (value[0] == selected)
                opt.attr('selected', 'selected');
        }
        html_opts.push(opt);
    });
    return html_opts;
}

function get_color(username) {
    if (global.team_colors[username] !== undefined) { return global.team_colors[username]; }
    var offset = Object.keys(global.team_colors).length;
    var color = offset*220;
    global.team_colors[username] = color;
    return color;
}

function update_calendar_team() {
    if(typeof global.team=="undefined") {
        setTimeout(update_calendar_team, 200);
    }
    else {
        // now that things are loaded...
        //var team_id = $('select#team option:selected').attr('id');

        // Set up team
        $.getJSON( '/'+global.team+'/members', function( data ) {
            var items = [];
            var team = [];
            $.each( data, function( key, val ) {
                var background = get_color(val['id']);
                var member = $("<div/>", {
                               "class": "team_member",
                               "id": val['id'],
                               text: val['name']
                              });
                $(member).draggable({
                    zIndex: 999,
                    revert: true,      // will cause the event to go back to its
                    revertDuration: 0  //  original position after the drag
                });
                items.push(member);

                $(member).css('background-color', 'hsl('+background+', 70%, 50%)');
                team.push([val['id'],val['name']]);
            });
            $("#team_members").html(items);
            global.team_members = team;
        });

        // remove old event source and add the current one, this causes a refetch 
        // of events
        $('#calendar').fullCalendar( 'removeEventSource',global.event_source);
        $('#calendar').fullCalendar( 'removeEventSource',global.predict_event_source);

        event_source = {
            url: '/'+global.team+'/events',
            type: 'GET',
            // TODO: Better than alert() is needed...
            error: function() {
                //alert('there was an error while fetching events!');
            },
        };
        global.event_source = event_source;
        $('#calendar').fullCalendar( 'addEventSource', event_source);

        predict_event_source = {
            url: '/'+global.team+'/predict_events',
            type: 'GET',
            // TODO: Better than alert() is needed...
            error: function() {
                //alert('there was an error while fetching events!');
            },
        };
        global.predict_event_source = predict_event_source;
        $('#calendar').fullCalendar( 'addEventSource', predict_event_source);
    }
}

function set_up_oncall_order(role, oncall_html, notoncall_html) {
    $(oncall_html).empty();
    $(oncall_html).text(role);
    $(notoncall_html).empty();
    $(notoncall_html).text("Not in rotation");

    $.getJSON('/'+global.team+'/oncallOrder/'+role, function( data ) {
        var oncall = [];
        var not_oncall = [];
        var team = [];
        $.each( data['oncall'], function( key, val ) {
            var background = get_color(val['user']['id']);
            var member = $("<li/>", {
                           "class": "team_member",
                           "id": val['user']['id'],
                           text: val['user']['name']
                          });
            oncall.push(member);

            $(member).css('background-color', 'hsl('+background+', 70%, 50%)');
            team.push([val['user']['id'],val['user']['name']]);
        });
        $.each( data['not_oncall'], function( key, val ) {
            var background = get_color(val['id']);
            var member = $("<li/>", {
                           "class": "team_member",
                           "id": val['id'],
                           text: val['name']
                          });
            not_oncall.push(member);

            $(member).css('background-color', 'hsl('+background+', 70%, 50%)');
            team.push([val['id'],val['name']]);
        });
        $(oncall_html).append(oncall);
        $(notoncall_html).append(not_oncall);
    });

    $(oncall_html).sortable({
      connectWith: notoncall_html,
      placeholder: "ui-state-highlight"
    }).disableSelection();
    $(notoncall_html).sortable({
      connectWith: oncall_html,
      placeholder: "ui-state-highlight"
    }).disableSelection();
}

function open_oncall_order_dialog() {
    set_up_oncall_order('Primary',
                        "#primary_oncall",
                        "#primary_notoncall");
    set_up_oncall_order('Secondary',
                        "#secondary_oncall",
                        "#secondary_notoncall");

    $('#oncallOrderModal').modal('show');
}

function open_profile_dialog() {
    // TODO: Update data then show modal
    $('#profileModal').modal('show');
}

function select_team(slug, update_calendar) {
    // set default val
    update_calendar =  typeof update_calendar !== 'undefined' ? update_calendar : true;

    var team = false;
    $.each( global.teams, function( key, val ) {
        if (slug == val['id']) {
            team = val;
            return false; // break loop
        }
    });
    if (team) {
        global.team = team['id'];
        $('.selected-team').html(team['name']);
    }
    else {
        console.log('Error: team id did not work');
    }

    if (update_calendar) {
        update_calendar_team();
    }

}


function get_flashes() {
    // get flashes and put in #flash-drawer
    $('#flash-drawer').html('');
    $.getJSON( "/user/getFlashes", function( data ) {
        $.each(data, function( key, val ) {
            var category = val[0] == 'message' ? 'info' :  val[0];
            var message = val[1];
            var alert = $('<div data-dismiss="alert" role="alert"/>')
                .attr('class', 'alert alert-'+category+' alert-dismissible')
                .append($('<button type="button" class="close"/>')
                    .html('<span aria-hidden="true">&times;</span><span class="sr-only">Close</span>'))
                .append(message);

            $('#flash-drawer').append(alert);
        });
    });
}


$(document).ready(function() {
    $('#oncallOrderModal').on('hide.bs.modal', function (e) {
        update_calendar_team();
    });

    var menu = $('<div/>').qtip({
        //id: 'calendar',
        prerender: true,
        content: {
            text: ' ',
            title: {
                button: true
            }
        },
        position: {
            my: 'bottom center',
            at: 'top center',
            target: 'mouse',
            //viewport: $('#calendar'),
            adjust: {
                mouse: false,
                scroll: false
            }
        },
        show: false,
        hide: false,
        style: 'qtip-light qtip-rounded'
    }).qtip('api');
    global.menu = menu;

    // get teams
    $.getJSON( "/teams", function( data ) {
        global.teams = [];
        $.each( data['teams'], function( key, val ) {
            global.teams.push(val);

            if (data['primary'] === null) {
                select_team(val['id'], false);
            }
            else {
                select_team(data['primary'], false);
            }

            var onclick = "select_team('"+val['id']+"')";
            $('.team-list').append($('<li/>')
                                 .append($('<a/>')
                                     .attr('onclick', onclick)
                                     .attr('href', '#')
                                     .html(val['name'])));
        });
    });

    // get roles and add to global variable
    $.getJSON( "/roles", function( data ) {
        global.roles = data;
    });

    // Set up calendar
    $('#calendar').fullCalendar({
        firstDay: 1,
        editable: true,
        droppable: true,
        eventSources: [],
        
        eventDrop: updateAndRefetch,

        eventResize: updateAndRefetch,

        drop: function(date, allDay) { // this function is called when something is dropped
            $.post('/'+global.team+'/event',
                   {'start': formatDate(date),
                    'username': $(this).attr('id')});

            $('#calendar').fullCalendar('refetchEvents');
        },
        
        loading: function(bool) {
            if (bool) $('#loading').show();
            else $('#loading').hide();
        },

        eventDragStart: function() { global.menu.hide(); },
        eventResizeStart: function() { global.menu.hide(); },
        dayClick: function() { global.menu.hide(); },
        viewDisplay: function() { global.menu.hide(); },

        eventClick: function(data, event, view) {
            if (data.projection !== true) {
                var content = $('<div/>')
                              .attr('id', 'menu_content');
                content.append($('<input/>')
                               .attr('type', 'hidden')
                               .attr('value', data.id));
                content.append($('<br/>'))
                               .append($('<span/>').html('Role:'))
                               .append($('<select/>')
                                      .attr('id', 'role')
                                      .attr('onchange', 'modify_event_by_id('+data.id+')')
                                      .append(make_select_options(global.roles, data.role)))
                               .append($('<br/>'))
                               .append($('<span/>').html('Person:'))
                               .append($('<select/>')
                                      .attr('id', 'user')
                                      .attr('onchange', 'modify_event_by_id('+data.id+')')
                                      .append(make_select_options(global.team_members, data.user_username)))
                               .append($('<br/>'));
                content.append($('<button/>').
                               attr('onclick', 'delete_event_by_id('+data.id+')').
                               html('Delete'));
                menu.set({
                    'content.text': content
                })
                .reposition(event).show(event);
            }
        },

        dayRender: function (date, cell) {
            var today = new Date();
            if ((date.getDay() == 6 || date.getDay() === 0) &&
                 date.getDate() != today.getDate()) {
                $(cell).css('background-color', '#f8f8f8');
            }
        },

        eventRender: function (event, element, view) {
            var opacity = "50%";
            if (event.projection === true) {
                opacity = "75%";
            }
            $(element).css('background-color', 'hsl('+get_color(event.user_username)+', 70%, '+opacity+')');
            $(element).css('border', '1px solid hsl('+get_color(event.user_username)+', 70%, '+opacity+')');
        }
    });

    update_calendar_team();
    // google_cal = {
    //     url: 'https://www.google.com/calendar/feeds/en.usa%23holiday%40group.v.calendar.google.com/public/basic',
    //     className: 'gcal-event',
    //     // TODO: Better than alert() is needed...
    //     error: function() {
    //         //alert('there was an error while fetching events!');
    //     },
    // };
    // $('#calendar').fullCalendar( 'addEventSource', google_cal);

    $('form[data-async]').on('submit', function(event) {
        var $form = $(this);
        var $target = $($form.attr('data-target'));

        $.ajax({
            type: $form.attr('method'),
            url: $form.attr('action'),
            data: $form.serialize(),

            success: function(data, status) {
                $('#profileModal').modal('hide');
                get_flashes();

            }
        });

        event.preventDefault();
    });

    get_flashes();
});