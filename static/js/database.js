$(document).ready(function() {
//############ Post-load Setup: #########################################

//############ Dependent Functions: ####################################
//Sort from greatest to least.
function sortNumbers(smallNum,bigNum) {
	return smallNum - bigNum;
}

//Refresh screen.
function refreshScreen(rememberPage) {
	rememberPage = rememberPage !== undefined ? rememberPage : true
	if (rememberPage) { 
		setPageCookie(); 
	}
	window.setTimeout('location.reload()', 300);
}

//Set the current_page cookie.
function setPageCookie() {
	$.cookie("current_page", $("#pagesCurrent").html().trim(),
		{expires: 7}); //Set cookie to expire after one week.
}

//Refresh the data container classes. (NOTE: Does not perform server request for new data.)
function restyleData() {
	//Fade out units if the amount is also faded out.
	$(".type_unit").each(function() {
		if ($(this).prev().is(":empty")) {
			$(this).css({"opacity":"0.3"});
		}
	});
	//Keep selected data highlighted even if on page changes.
	$(".dataIndex").each(function() {
		dataID = Number($(this).html().trim())
		if (selectedData.indexOf(dataID) != -1) {
			$(this).parent().addClass("dataSelected");
		}
	});
}

function showRibbon(message, color, location) {
	//Default location is the dataContainer.
	location = location !== undefined ? location : "#dataContainer"
	
	$(location).append(
		"<div class=ribbonMessage style=\"background-color:" + color + 
			";\">" + message + "</div>"
	);
	setTimeout(function() {
		$(".ribbonMessage").fadeOut(1000);
	},500);
}


//############ Variable Setup: #########################################
var selectedData = Array();
var changesMade = {
	del:[],
	edit:[],
	dupl:[],
	add:[],
	};
	
//############ Popup Management: #######################################
//Activate specified popup:
$(document).on("click", ".popupActivator", function() {
	//Display a loading message if the request takes a visible amount of time.
	$("#popupContainer_inner").html("<center>Loading. Please wait.</center>");
	activatorID = $(this).attr("id");
	switch ($(this).attr("id")) {
		case "dbMenu_addNew":
			$("#popupContainer").attr("for", activatorID);
			$.get("/data_form/", function(response) {
				$("#popupContainer_inner").html(response);
			});
			break;
		case "dbMenu_uploadCSV":
			$("#popupContainer").attr("for", activatorID);
			$.get("/upload_CSV/", function(response) {
				$("#popupContainer_inner").html(response);
			});
			break;
		case "userLogin":
			$("#popupContainer").attr("for", activatorID);
			$.get("/user_login/", function(response) {
				$("#popupContainer_inner").html(response);
			});
			break;
		case "registrationPrompt": //###REPLACE WITH DROP-DOWN PRELOADED?
			$("#popupContainer").attr("for", activatorID);
			$.get("/registration_prompt/", function(response) {
				$("#popupContainer_inner").html(response);
			});
			break;
		case "userRegistration":
			$("#popupContainer").attr("for", activatorID);
			$.get("/user_registration/", function(response) {
				$("#popupContainer_inner").html(response);
			});
			break;
		case "labRegistration":
			$("#popupContainer").attr("for", activatorID);
			$.get("/user_registration/", function(response) {
				$("#labRegistration").html(response);
			});
			break;
		case "dbMenu_downloadCSV"://###
			$("#popupContainer_inner").html("DIFF!");
			break;
		default: 
			return false; //If a popup is not recognized, don't l
	}
	
	$("#popupGlobal").fadeIn("fast");
	
});

// Fade the popup when the mask is clicked.
$(document).on("click", "#mask", function() {
	$("#popupGlobal").fadeOut("fast");
	
	//Reload the screen if requested.
	if ($(".reloadActivator").length) {
		refreshScreen();
		$(".reloadActivator").remove();
	};
});

//Close popups on close-button click.
$(document).on("click", ".closeButton", function() {
	//Close the global container if the main container is closed.
	if ($(this).parent().attr("id")=="popupContainer") {
		$(this).parent().parent().fadeOut("fast"); 
	} else {
		$(this).parent().fadeOut("fast");
	}
});

//Show the CSV title to be displayed on the visible element.
$(document).on("change", "#uploadCSV_hiddenInput", function() {
	if (!$("#uploadCSV_hiddenInput").val()) {
		$("#uploadCSV_display").children("div").html("None Selected");
	} else {
		$("#uploadCSV_display").children("div").html($(this).val().split('\\').pop());
	}
});

//############ Form Interactions: ######################################
$(document).on("submit", "form", function() {
	var form = $(this); //Keep a reference to the form inside the POST request.
	$.post($(form).attr("action"), $(form).serialize(), function(response) {
		//Recreate the popup window with the server response.
		$("#popupContainer_inner").html(response);
		$(".subPopup").draggable();
		
		//Show the ribbon message if applicable.
		if ($(".successActivator").length) {
			showRibbon("Data added!", "green", "#popupContainer_inner");
			$(".successActivator").remove();
		}
		
		//Reload the page if applicable.
		if ($(".reloadActivator").length) {
			refreshScreen(false); //Do not remember the log-in page.
		}
		
	});
	
	return false; //Do not continue or else the form will post again. 
});



//############ Data Selection: #########################################
//Click Group to Select:
$(document).on("click", ".dataGroup", function() {
	$(this).toggleClass("dataSelected");
	
	//Get Index of Selected Data by Number
	var dataID = parseInt($(this).children(".dataIndex").html());
	
	var indexOfData = selectedData.indexOf(dataID);
	if (indexOfData >= 0) { //Data is already selected (thus, deselect)
		selectedData.splice(indexOfData,1);	
	} else { //Select data
		selectedData.push(dataID);
		selectedData.sort(sortNumbers); //###Necessary? Probably
	}
});

//Select Page (Button)
$("#dbMenu_selectPage").click(function() { 
	var selectedOnPage = [];
	
	//Select data
	$(".dataIndex").each(function() {
		var dataID = parseInt($(this).html());
		if (selectedData.indexOf(dataID) < 0){ //If the item is not in the list yet.
			$(this).parent().addClass("dataSelected");
			selectedData.push(dataID);
		} else {
			//Count the element as selected.
			selectedOnPage.push(dataID);
		} 
	}); 
	
	//Deselect data (if all elements were already selected; ie, "toggle")
	if (selectedOnPage.length == $(".dataGroup").length){
		for (i in selectedOnPage) {
			var indexOfData = selectedData.indexOf(selectedOnPage[i]);
			selectedData.splice(indexOfData,1);	
		}
		$(".dataGroup").removeClass("dataSelected");
	}
	selectedData.sort(sortNumbers); //Sort data once selection is complete.
});

//Select All (Button)
$("#dbMenu_selectAll").click(function() { 
	//If all data is selected, deselect everything.
	var totalDataSize = $("#pagesTotal").attr("total_data_size");
	if (selectedData.length == totalDataSize) {
		selectedData = [];
		$(".dataGroup").each(function() {
			$(this).removeClass("dataSelected");
		});
	} else {
		selectedData = [] //Clear selection to avoid duplicates.
		for(i = 1; i <= totalDataSize; i++) { 
			selectedData.push(i);
		}
		//Data will already be sorted from least to greatest after loop. 
		$(".dataGroup").addClass("dataSelected");
	}
});

//############ Data Manipulation: #########################################
//Duplicate Button
$("#dbMenu_duplicate").click(function() {  
	//Assume data that is selected is already correct.
	for (var i in selectedData) {
		changesMade.dupl.push(selectedData[i]);
	}
	
	showRibbon("Selection duplicated!", "green");
	
	//Upload updated data
	//updateData();###
});

//Delete Button
$("#dbMenu_delete").click(function() {  
	for (var i in selectedData) {
		changesMade.del.push(selectedData[i]);
		//Immediately delete the data from the client's view ("#g_x" represents group ID).
		$("#g_"+String(selectedData[i])).remove()
	}
	selectedData = [];
	
	showRibbon("Selection deleted!", "red");
	
	//Upload updated data
	//updateData(); ###
});

//############ User Authentication: ####################################
$("#userLogOut").click( function() {
	//Send the log-out signal.
	$.get("/user_logout/", function() {});
	
	//Reload the screen to verify log-out.
	refreshScreen()
});

//############## Change Pages: #########################################
$(document).on("click", "#pagesInputButton", function() {
	var pageLink = $("#pagesInputText").val().trim();
	
	if (pageLink == $("#pageLinkCurrent").html().trim()) {
		showRibbon("Already here!", "green");
		return false //Don't do anything else if page already is active.
	} else if ($.isNumeric(pageLink)
		&& parseInt(pageLink) <= parseInt($("#pagesTotal").html().trim())
		&& parseInt(pageLink) > 0) {
		//Create a CSRF Token for Django authorization.
		var csrftoken = $.cookie("csrftoken");
		
		//Request the information about a page.
		pageDestination = "/data_transmit/" + pageLink;
		$.get(pageDestination, function(dataResponse) {
			var newDataContainer = dataResponse;
			$("#dataContainer").html(newDataContainer);
			restyleData();
		});
	} else {
		showRibbon("Page does not exist", "red");
	}
});

$(document).on("click", ".pageLink", function() {
	//If a valid page link has been clicked.
	var pageLink = $(this).html().trim();
	//If the link is a number (not an ellipsis) and not the current page:
	if ($.isNumeric(pageLink) && pageLink != $("#pageLinkCurrent").html().trim()) {
		//Request the information about a page.
		pageDestination = "/data_transmit/" + pageLink;
		$.get(pageDestination, function(dataResponse) {
			var newDataContainer = dataResponse;
			$("#dataContainer").html(newDataContainer);
			restyleData();
		});
	}
});


//######################################################################
//alert("All loaded!");//###
});
