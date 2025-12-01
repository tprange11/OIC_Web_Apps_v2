function confirmDelete(event) {
    event.preventDefault();
    
    if (confirm('Are you sure you want to remove this registration?')) {
        // If confirmed, proceed with the original action
        if (event.target.tagName === 'A') {
            window.location.href = event.target.href;
        } else {
            event.target.form.submit();
        }
    }
    return false;
} 
