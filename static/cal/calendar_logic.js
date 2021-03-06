function initializeCalendar(calendarData) {

    function loggedOutWarning() {
	n = noty({
	    text: "You must log in to make reservations.",
	    type: 'error',
	    dismissQueue: true,
	    layout: 'topRight',
	    timeout: 3800,
	    onCloseClick: function () { window.location = calendarData.login_url; }
	});
    }

    function onDayClick(date, allDay, jsEvent, view) {
	if (calendarData.logged_in == "False")
	    return loggedOutWarning();

	var theData = {};
	theData['timestamp'] = date.getTime()/1000;
	theData['resource_id'] = calendarData.resource_id;
	$.ajax({
	    url: calendarData.reservation_url,
	    type: "POST",
	    dataType: "json",
	    data: theData,
	}).done(function() {
	    $('#' + calendarData.element_id).fullCalendar('refetchEvents');
	}).fail(showAjaxFailure);
    }

    var open_delete_dialogs = [];
    function close_delete_dialogs() {
	for (var i=0; i<open_delete_dialogs.length; i++) {
	    open_delete_dialogs[i].close();
	}
	open_delete_dialogs = [];
    }
    function deleteEvent(eventId) {
	// Can sadly not use $.noty.closeAll() here because of BUGS:
	// Spamming dialogs will cause all to close on open until refresh.
	n = noty({
	    text: "Do you want to remove event #" + eventId,
	    type: 'error',
	    dismissQueue: true,
	    layout: 'center',
	    buttons: [{
		addClass: 'btn btn-danger', text: 'Delete', onClick: function($noty) {
		    $noty.close();
		    $.ajax({
			url: calendarData.delete_url,
			type: "POST",
			dataType: "json",
			data: {id: eventId},
		    }).done(function() {
			$('#' + calendarData.element_id).fullCalendar('refetchEvents');
		    }).fail(showAjaxFailure);}}, {
		addClass: 'btn btn-primary', text: 'Cancel', onClick: function($noty) {
		    $noty.close();
		    $('#' + calendarData.element_id).fullCalendar('refetchEvents');
		}
	    }]
	});
	close_delete_dialogs();
	open_delete_dialogs.push(n);
    }

    function overwriteEvent(calEvent) {
	n = noty({
	    text: "Do you want to overwrite event #" + calEvent.id,
	    type: 'error',
	    dismissQueue: true,
	    layout: 'center',
	    buttons: [{
		addClass: 'btn btn-danger', text: 'Overwrite', onClick: function($noty) {
		    $noty.close();
		    $.ajax({
			url: calendarData.overwrite_url,
			type: "POST",
			dataType: "json",
			data: {id: calEvent.id},
		    }).done(function() {
			$('#' + calendarData.element_id).fullCalendar('refetchEvents');
		    }).fail(showAjaxFailure);}}, {
		addClass: 'btn btn-primary', text: 'Cancel', onClick: function($noty) {
		    $noty.close();
		    $('#' + calendarData.element_id).fullCalendar('refetchEvents');
		}
	    }]
	});
    }

    function onEventClick(calEvent, jsEvent, view) {
	if (calendarData.logged_in == "False")
	    return loggedOutWarning();

	if (calEvent.is_own) {
	    deleteEvent(calEvent.id);
	} else if (calEvent.solidity == "preliminary"){
	    overwriteEvent(calEvent);
	} else {
	    n = noty({
		text: "You cannot overwrite a solid reservation.",
		type: 'error',
		dismissQueue: true,
		layout: 'topRight',
		timeout: 3800
	    });
	}
    }

    calData = {
	firstDay: 1,
	defaultView: calendarData.view,
	editable: true,
	disableResizing: true,
	disableDragging: true,
	allDayDefault: false,
	allDaySlot: false,
	defaultEventMinutes: 60,
	firstHour: 10,
	height: 500,
	columnFormat: 'ddd d/M',
	titleFormat: {
	    month: 'MMMM yyyy',                             // September 2009
	    week: "MMM d[',' yyyy]{ '&#8212;'[ MMM] d',' yyyy}", // Sep 7 - 13 2009
	    day: 'dddd, MMM d, yyyy'                  // Tuesday, Sep 8, 2009
	},
	eventSources: [{url: calendarData.resource_event_url}],
	dayClick: onDayClick,
	eventClick: onEventClick
    };
    if (calendarData.hasOwnProperty('header')) {
	calData.header = calendarData.header;
    }
    $('#' + calendarData.element_id).fullCalendar(calData);
}
