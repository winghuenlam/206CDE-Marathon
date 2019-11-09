function validate() {
    var result = validatePassword();
    return result;
}

function validatePassword() {
    var pass = document.getElementById("fpassword").value;
    var cpass = document.getElementById("cpassword").value;
    if (pass == cpass) {
        return validatePhoneNumber()
    } else {
        alert("Passwords do not match.");
        document.getElementById("cpassword").focus();
        return false;
    }
}



function validatePhoneNumber() {
    if (/[0-9]{7}$/.test(document.getElementById("phone").value)) {
        return (true)
    }
    alert("You have entered an invalid phone number!")
    document.getElementById("phone").focus();
    return (false)
}



