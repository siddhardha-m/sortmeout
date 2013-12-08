$(function(){

    $('#id_category').keyup(function() {
    
        $.ajax({
            type: "POST",
            url: "/lookup/",
            data: { 
                'lookup_text' : $('#id_category').val(),
                'csrfmiddlewaretoken' : $("input[name=csrfmiddlewaretoken]").val()
            },
            success: lookupSuccess,
            dataType: 'html'
        });
        
    });

});

function lookupSuccess(data, textStatus, jqXHR)
{
    $('#lookup-results').html(data);
}

$(function(){

    $('#lookup-results').on('click','li', function (){
    
    	var catsncommas = $('#id_category').val();
    	
        var cats = catsncommas.split(", ");
        
        $('#id_category').val("")
        if (cats.length > 1) {
        	$('#id_category').val(cats[0]);
            for (var i = 1; i < cats.length-1; i++) {
                $('#id_category').val($('#id_category').val() + ', ' + cats[i]);
            };
            $('#id_category').val($('#id_category').val() + ', ' + $(this).text() + ", ");
        }
        else{
        	$('#id_category').val($(this).text() + ", ");
        }
        
        $('#lookup-results').empty()
        
        $.ajax({
            type: "POST",
            url: "/expertise/",
            data: { 
                'csrfmiddlewaretoken' : $("input[name=csrfmiddlewaretoken]").val()
            },
            success: expertiseSuccess,
            dataType: 'html'
        });
        
    });

});

function expertiseSuccess(data, textStatus, jqXHR)
{
    $('#expertise-level-choices').html(data);
    
}

$(function(){

    $('#expertise-level-choices').on('click','li', function (){
    
    	var levelntext = $(this).text();
    	
        var level = levelntext.split(".");
        
        if (level.length > 1) {
            $('#id_category').val($('#id_category').val() + level[0] + ", ");
        }
        
        $('#expertise-level-choices').empty()
        
    });

});
