function signInCallback(authResult) {
  if (authResult['code']) {
	$('#signinButton').css("display", "none");
	$('#initialSignoutButton').css("display", "block");
	$('.buttonDisplay').css("display", "flex");
	$('.flashMessage').css("display", "block");
  }

  $.ajax({
	type: 'POST',
	url: '/gconnect?state={{STATE}}',
	processdata: false,
	data: authResult['code'],
	contentType: 'application/octet-stream; charset=utf-8'
  });
}

function APIErrorMessage() {
  alert("Google API is not available at the moment - please check back in again later");
}
