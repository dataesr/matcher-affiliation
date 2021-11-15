$(document).on('change', '#input_type', function() {
    type = $('#input_type option:selected').val().toLowerCase();
    if(type == 'rnsr') {
        $('#select_year').removeClass('d-none');
    } else {
        $('#select_year').addClass('d-none');
    }
});

$('.submit').on('click', function() {
    $('#logs').html('... en cours ...');
    input_json = { 
	    type: $('#input_type option:selected').val(),
	    year: $('#input_year option:selected').val(),
	    query: $('#input_query').val(),
	    verbose: true
    }
    $.ajax({
        url: '/match_api',
        data: JSON.stringify(input_json),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        method: 'POST'
    })
    .done(result => {
        $('#logs').html(result.logs);
    })
    .fail(error => {
        console.log(error);
    });
});

