// static/main.js

console.log("Sanity check!");

// Get Stripe publishable key
fetch("/config/")
    .then((result) => { return result.json(); })
    .then((data) => {
        // Initialize Stripe.js
        const stripe = Stripe(data.publicKey);

        // new
        // Event handler
        document.querySelector("#submitBtn").addEventListener("click", () => {
            // Get Checkout Session ID
            fetch("/create-checkout-session/")
                .then((result) => { return result.json(); })
                .then((data) => {
                    console.log(data);
                    // Redirect to Stripe Checkout
                    return stripe.redirectToCheckout({ sessionId: data.sessionId })
                })
                .then((res) => {
                    console.log(res);
                });
        });
    });

$(document).ready(function() {


    $('#catform').submit(function(e) {
        e.preventDefault();
        console.log(e)
        console.log(this)


        $.ajax({
            url: '/editprodaddcat',
            method: 'post',
            data: $(this).serialize(),
            success: function(serverResponse) {
                console.log("this is ajax working");
                $('.testingajax').append(serverResponse);

            },
            error: function(serverResponse) {
                $('.alert').append(serverResponse);
            }

        })
        $(this).trigger('reset');
    })
})