function validate() {
    var result = validatePhoneNumber();
    return result;
    
}


function validatePhoneNumber() {
    if (/[0-9]{7}$/.test(document.getElementById("phone").value)) {
        return validateCardNumber();
    }
    alert("You have entered an invalid phone number!")
    document.getElementById("phone").focus();
    return (false)
}

function validateCardNumber() {
    number=document.getElementById("cardnum").value;
    if (/^[0-9]{16}$/.test(number)){
        return (true)
     }
    alert("Please enter a 16 digit valid credit card number!")
    document.getElementById("cardnum").focus();
    return (false)

}

