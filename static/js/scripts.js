$( document ).ready(function() {

    var deleteBtn  = $('.delete-btn');
    var searchBtn  = $('#search-btn');
    var searchForm = $('#search-form');
    var filter     = $('#filter')

    $(deleteBtn).on('click', function(e) {

        e.preventDefault();

        var delLink = $(this).attr('href');
        var result = confirm('Deseja remover o registro?');

        if(result) {
            window.location.href = delLink;
        }
    });

    $(searchBtn).on('click', function(e) {

        searchForm.submit();
    });

    $("input[name='search']").on('input' , function(e) {
        console.log("teste")

        var $formData = searchForm.serialize()

        var $thisURL = window.location.href

        $.ajax({
            method: "GET",
            url: $thisURL,
            data: $formData,
            success: function (data, textStatus, jqXHR) {
                $(".container-pesquisa")[0].innerHTML = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {


            }
        })
    })

});