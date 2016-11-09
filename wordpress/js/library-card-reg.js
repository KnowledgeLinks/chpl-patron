/* Copy and paste the contents of this file into the wordpress cornerstone
custom </> js section */

function loadScript(url, callback)
{
    // Adding the script tag to the head as suggested before
    var head = document.getElementsByTagName('head')[0];
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = url;

    // Then bind the event to the callback function.
    // There are several events for cross browser compatibility.
    script.onreadystatechange = callback;
    script.onload = callback;

    // Fire the loading
    head.appendChild(script);
}
var regValidation = function() {
    jQuery.validator.addMethod("postalCode", function(value, element) {
        // call the postalcode lookup 
        var valid = false
        if (value.length == 5) {
            jQuery.ajax({
                url: 'http://chapelhillpubliclibrary.org:3000/postal_code?g587-zipcode=' + value,
                //url: 'http://localhost:4000/postal_code?g587-zipcode=' + value,
                crossDomain: true,
                success: function (result) {
                    valid = result.valid;
                    if (valid) {
                        if (result.data.length == 1) {
                            $('#g587-city').replaceWith("<input class='submitToggle' type='text' name='g587-city' id='g587-city' value='' class='text' required aria-required='true' disabled/>")
                            $('#g587-city').val(result.data[0].city);
                            $('#g587-state').val(result.data[0].state_short);
                        } else {
                            var  options = [];
                            for (i = 0; i < result.data.length; i++) {
                                options.push("<option value='" + result.data[i].city + "'>" + result.data[i].city + "</option>");
                            };
                            $('#g587-city').replaceWith("<select name='g587-city' id='g587-city'>" + options.join() +"</select>");
                            $('#g587-state').val(result.data[0].state_short);
                        }
                    } else {
                        $('#g587-city').replaceWith("<input class='submitToggle' type='text' name='g587-city' id='g587-city' value='' class='text' required aria-required='true' disabled/>")
                        $('#g587-city').val('');
                        $('#g587-state').val('');
                    }
                },
                async: false
            });
            return valid;
        } else {
            $('#g587-city').replaceWith("<input class='submitToggle' type='text' name='g587-city' id='g587-city' value='' class='text' required aria-required='true' disabled/>")
            $('#g587-city').val('');
            $('#g587-state').val('');
            return false;
        };
    }, "Enter a valid US postal code");

    $('#library-card-registration').validate({
        rules: {
            "g587-email": {
                required: true,
                email: true,
                //remote: "http://localhost:4000/email_check"
                remote: "http://chapelhillpubliclibrary.org:3000/email_check"
            },
            'g587-birthday': {
                required: true,
                date: true
            },
            'g587-zipcode': {
                required: true,
                postalCode: true
            }
        },
        submitHandler: function(form) {
            $('#library-card-registration').find('.submitToggle').prop('disabled', false);
            $(":disabled").removeAttr('disabled');
            //var validForm = $('#library-card-registration').valid();
            //if (validForm === true) {
                $('#library-card-registration').find(":disabled").removeAttr('disabled');
                $('#library-card-registration').ajaxSubmit({
                    success:  function(result) {
                        if (result.valid == true) {
                            window.location.href = result.url;
                        } else {
                            for (i=0; i<result.errors.length; i++) {
                                var errText = '<label id="' + result.errors[i].field + '-error" class="error" for="' + result.errors[i].field + '">' + result.errors[i].message + '</label>';
                                $("#"+result.errors[i].field).after(errText)
                            }
                        }
                    }
                });
            /*} else {
                $('#library-card-registration').find('.submitToggle').prop('disabled', true);
            };*/
            
            
        }
    });
};
loadScript("https://cdnjs.cloudflare.com/ajax/libs/jquery.form/3.51/jquery.form.min.js",
          loadScript("https://cdnjs.cloudflare.com/ajax/libs/jquery-validate/1.15.1/jquery.validate.min.js",regValidation))