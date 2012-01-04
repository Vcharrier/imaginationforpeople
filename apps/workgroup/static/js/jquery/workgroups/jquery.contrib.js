(function( $ ){

    $.fn.collapse = function() {  
        this.animate({ height: "100px" }, {duration : 400});
    };
    
    $.fn.uncollapse = function() {  
        this.animate({ height: "100%" }, {duration : 800});
    };

})( jQuery );
