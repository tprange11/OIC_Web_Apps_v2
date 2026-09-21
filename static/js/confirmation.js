// onclick handler for "remove registration" links and buttons: confirm first, then
// follow the link or submit the enclosing form.
function confirmDelete(event) {
    event.preventDefault();
    
    if (confirm('Are you sure you want to remove this registration?')) {
        if (event.target.tagName === 'A') {
            window.location.href = event.target.href;
        } else {
            event.target.form.submit();
        }
    }
    return false;
} 
