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
    $.ajax({
        type: 'PUT',
        async: false,
        url: '/api/v1/teams/'+global.team+'/events/'+event_id,
        contentType: 'application/json',
        data: JSON.stringify({'user_username': $('div#menu_content #user option:selected').attr('id'),
                              'role': $('div#menu_content #role option:selected').val()}),
        error: handle_ajax_error
    });
    $('#calendar').fullCalendar('refetchEvents');
}

function delete_event_by_id(event_id) {
    $.ajax({
        type: 'DELETE',
        async: false,
        url: '/api/v1/teams/'+global.team+'/events/'+event_id,
        error: handle_ajax_error
    });
    $('#calendar').fullCalendar('refetchEvents');
    global.menu.hide();
}

function updateAndRefetch(event, delta) {
    $.ajax({
        type: 'PUT',
        async: false,
        url: '/api/v1/teams/'+global.team+'/events/'+event.id,
        contentType: 'application/json',
        data: JSON.stringify({'start': formatDate(event.start),
                              'end': formatDate(event.end),
                              'username': $(this).attr('id')}),
        error: handle_ajax_error
    });
    $('#calendar').fullCalendar('refetchEvents');
}

function update_schedule() {
    var primary = [];
    var secondary = [];
    //var team_id = $('select#team option:selected').attr('id');

    $('ul#Primary_rotation li:not(.team_member_placeholder)').each(function(k, v) { primary.push([k,$(v).attr('id')]); });
    $('ul#Secondary_rotation li:not(.team_member_placeholder)').each(function(k, v) { secondary.push([k,$(v).attr('id')]); });
    $.ajax({
        type: 'PUT',
        async: false,
        url: '/api/v1/teams/'+global.team+'/schedule',
        contentType: 'application/json',
        data: JSON.stringify({'schedule': {'Primary': primary,
                                           'Secondary': secondary}}),
        complete: function(data, status) {
            $('#oncallOrderModal').modal('hide');
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
    var color = offset*219;
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
        $.getJSON( '/api/v1/teams/'+global.team+'/members', function( data ) {
            var items = [];
            var usernames = [];
            var team = [];
            $.each( data['members'], function( key, val ) {
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
                usernames.push(val['id']);

                $(member).css('background-color', 'hsl('+background+', 70%, 50%)');
                team.push([val['id'],val['name']]);
            });
            $("#team_members").html(items);
            global.team_members = team;
            global.team_usernames = usernames;
        });

        // remove old event source and add the current one, this causes a refetch
        // of events
        $('#calendar').fullCalendar( 'removeEventSource',global.event_source);

        event_source = {
            url: '/api/v1/teams/'+global.team+'/events',
            type: 'GET',
            // TODO: Better than alert() is needed...
            error: function() {
                //alert('there was an error while fetching events!');
            },
            data: {
                minimal: 'true'
            },
        };
        global.event_source = event_source;
        $('#calendar').fullCalendar( 'addEventSource', event_source);
    }
}

/*
set up schedule
- pull primary,secondary for team
- pull team member
- as building rotation schedule for each role, mark off team member
- put rest of team in not in rotation
*/
function make_schedule_member(user) {
    /*create list element for each member in oncall*/

    var background = get_color(user['id']);
    var member = $("<li/>", {
        "class": "team_member",
        "id": user['id'],
        text: user['name']
    });
    $(member).css('background-color', 'hsl('+background+', 70%, 50%)');
    return member;
}

function set_up_schedule() {
    /* TODO: Update team members? */
    $.getJSON('/api/v1/teams/'+global.team+'/schedule', function( data ) {
        var schedule = data['schedule'];

        /*make a hash of usernames*/
        var team_hash = {};
        $.each(global.team_members, function(num, member) { team_hash[member[0]] = {id:member[0], name:member[1]} });

        $.each( global.roles, function(num, role) {
            /*copy team members for each role*/
            var role_team_members = $.extend({}, team_hash);
            var in_rotation = [];
            var not_rotation = [];

            /*generate member list for team members in rotation*/
            $.each (schedule[role], function(sch_num, sch) {
                var user = sch['user'];
                delete role_team_members[user['id']]; /*mark user as oncall*/
                in_rotation.push(make_schedule_member(user));

            });
            /*generate member list for not in rotation*/
            $.each (role_team_members, function(id, user) {
                not_rotation.push(make_schedule_member(user));
            });
            // console.log(role_team_members);
            // console.log(in_rotation);
            // console.log(not_rotation);

            /*selection CSS*/
            var rotation_sel = '#'+role+'_rotation';
            var notoncall_sel = '#'+role+'_notoncall';

            $(rotation_sel).text(role);
            $(notoncall_sel).text("Not in rotation");
            $(rotation_sel).append(in_rotation);
            $(notoncall_sel).append(not_rotation);

            /*set up jquery sortable*/
            $(rotation_sel).sortable({
                connectWith: notoncall_sel,
                placeholder: "ui-state-highlight",
                items: "li:not(.team_member_placeholder)",
                containment: $(rotation_sel).parent()
            }).disableSelection();
            $(notoncall_sel).sortable({
                connectWith: rotation_sel,
                placeholder: "ui-state-highlight",
                containment: $(notoncall_sel).parent()
            }).disableSelection();
        });
    });
}

function open_oncall_order_dialog() {
    set_up_schedule();
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
    //$('#flash-drawer').html('');
    $.ajax({
        url: "/user/getFlashes",
        dataType: "json",
        async: false, /*Needs to be synchronous so browser properly sets cookie*/
        success: function( data ) {
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
        }
    });
}

function handle_ajax_error(xhr, status, error) {
  var resp = JSON.parse(xhr.responseText);
  var alert = $('<div data-dismiss="alert" role="alert"/>')
      .attr('class', 'alert alert-'+resp['category']+' alert-dismissible')
      .append($('<button type="button" class="close"/>')
          .html('<span aria-hidden="true">&times;</span><span class="sr-only">Close</span>'))
      .append(resp['message']);

  $('#flash-drawer').append(alert);
}


$(document).ready(function() {

    // when oncall schedule modal is re-hidden, refresh the calendar
    $('#oncallOrderModal').on('hide.bs.modal', function (e) {
        update_calendar_team();
    });

    // set up the qtip div element that will be used when event is clicked
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
    $.getJSON( "/api/v1/teams", function( data ) {
        global.teams = [];
        $.each( data['teams'], function( key, val ) {
            global.teams.push(val);

            var onclick = "select_team('"+val['id']+"')";
            $('.team-list').append($('<li/>')
                                 .append($('<a/>')
                                     .attr('onclick', onclick)
                                     .attr('href', '#')
                                     .html(val['name'])));
        });
    });

    // set user state
    $.getJSON( "/user/current_state", function( data ) {
        select_team(data['primary_team'], false);
    });

    // get roles and add to global variable
    $.getJSON( "/api/v1/roles", function( data ) {
        global.roles = data['roles'];
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
            $.ajax({
                type: 'POST',
                url: '/api/v1/teams/'+global.team+'/events',
                async: false,
                contentType: 'application/json',
                data: JSON.stringify({'start': formatDate(date),
                                      'username': $(this).attr('id')}),
                error: handle_ajax_error
            });

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
            if (data.editable !== false) {
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
            // show events for users who are not in the team as noneditable
            // if (global.team_usernames.indexOf(event.user_username) === -1) {
            //     event.editable = false;
            //     event.projection = true;
            // }

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
            }
        });

        event.preventDefault();
    });


    $('#primary_team').multiselect();
    $('#teams').multiselect();
});
