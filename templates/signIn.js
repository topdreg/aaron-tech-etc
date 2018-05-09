function signInCallback(authResult) {
	if (authResult['code']) {
		console.log("HIIIIII");
		$('#signinButton').attr('style', 'display': none); 
	}

	$.ajax({
		type: 'POST',
		url: '/gconnect?state={{STATE}}',
		processdata: false,
		data: authResult['code'],
		contentType: 'application/octet-stream; charset=utf-8'
	});;
}
