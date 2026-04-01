console.log('UCPC Poetry Archive Loaded');

document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;

    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        const href = link.getAttribute('href');

        if (href === currentPath || 
            (currentPath === '/' && href === '/') ||
            (currentPath.startsWith('/poet') && href === '/poets') ||
            (currentPath.startsWith('/view') && href === '/poets')) {
            link.classList.add('active');
        }
    });
});


// =======================================================
// 🔥 SOCIAL SHARE FUNCTION (ALL PLATFORMS)
// =======================================================

async function shareGhazal(textId) {
    try {
        const res = await fetch(`/ghazals/share_image/${textId}`);
        const data = await res.json();

        if (!data.share_url) {
            alert("❌ Error generating share link");
            return;
        }

        const url = data.share_url;

        // 🔥 Default: WhatsApp
        window.open(`https://wa.me/?text=${encodeURIComponent(url)}`);

    } catch (err) {
        console.error("Share error:", err);
        alert("❌ Something went wrong");
    }
}


// =======================================================
// 🔥 PLATFORM SPECIFIC SHARES
// =======================================================

function shareWhatsApp(url) {
    window.open(`https://wa.me/?text=${encodeURIComponent(url)}`);
}

function shareFacebook(url) {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`);
}

function shareTwitter(url) {
    window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}`);
}

function shareLinkedIn(url) {
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`);
}


// =======================================================
// 🔥 ADVANCED SHARE (WITH UI OPTIONS)
// =======================================================

async function openShareMenu(textId) {
    try {
        const res = await fetch(`/ghazals/share_image/${textId}`);
        const data = await res.json();

        if (!data.share_url) {
            alert("❌ Error generating share link");
            return;
        }

        const url = data.share_url;

        // 🔥 Simple prompt menu (can upgrade to modal later)
        const choice = prompt(
`Share Ghazal:

1 = WhatsApp
2 = Facebook
3 = X (Twitter)
4 = LinkedIn
5 = Copy Link

Enter choice:`);

        switch(choice) {
            case "1":
                shareWhatsApp(url);
                break;
            case "2":
                shareFacebook(url);
                break;
            case "3":
                shareTwitter(url);
                break;
            case "4":
                shareLinkedIn(url);
                break;
            case "5":
                copyToClipboard(url);
                break;
            default:
                alert("❌ Invalid choice");
        }

    } catch (err) {
        console.error(err);
        alert("❌ Share failed");
    }
}


// =======================================================
// 📋 COPY LINK
// =======================================================

function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => alert("✅ Link copied!"))
        .catch(() => alert("❌ Copy failed"));
}