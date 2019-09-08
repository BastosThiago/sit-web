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

});