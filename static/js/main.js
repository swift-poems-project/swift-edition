/**
 * jQuery widget integration and behavior
 *
 */

'use strict';

(function($) {

    $(document).ready(function(e) {

	    /**
	     * Widgets for the collation viewing interface
	     *
	     */
	    $('#reset-scroll').click(function(event) {
		    event.preventDefault();
		    $('html, body').animate({ scrollTop: 0 }, 500);
		    return false;
		});

	    $('#toggle-line-variation').click(function(e) {
		    e.preventDefault();
		    $($(this).data('target')).toggleClass('hidden');
		    if( $(this).text() == 'Show Line Variation' ) {
			$(this).text('Hide Line Variation');
		    } else {
			$(this).text('Show Line Variation');
		    }
		});

	    function formatData (data) {
		var markup = "" + data + "";

		return markup;
	    };

	    /**
	     * Format the data selected within the widget
	     *
	     */
	    function formatDataSelection (data) {
		return data;
	    };
	});
}(jQuery));
